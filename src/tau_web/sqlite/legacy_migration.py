"""Normalised Vibes/Piclaw migration bundles with transactional rollback."""

from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal, cast
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from tau_agent.session import SessionEntry
from tau_agent.types import JSONObject, JSONValue
from tau_web.sqlite.connection import SqliteDatabase
from tau_web.sqlite.interchange import SessionInterchangeError, validate_entry_sequence
from tau_web.sqlite.session_storage import SqliteSessionStorage
from tau_web.sqlite.sessions import validate_agent_name, workspace_id_for_path
from tau_web.sqlite.writer import SqliteTransaction


class LegacyTimelineMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    role: str
    content: str = ""
    content_blocks: list[JSONObject] | None = None
    created_at: str | None = None


class LegacyMediaItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    filename: str
    media_type: str
    content_base64: str
    width: int | None = None
    height: int | None = None
    metadata: JSONObject = Field(default_factory=dict)


class LegacySession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_kind: Literal["vibes", "piclaw"]
    source_session_id: str
    workspace_root: str
    agent_name: str
    provider_name: str
    model: str
    title: str | None = None
    thinking_level: str | None = None
    chat_jid: str | None = None
    entries: list[SessionEntry] = Field(default_factory=list)
    timeline: list[LegacyTimelineMessage] = Field(default_factory=list)
    plan_markdown: str | None = None
    plan_explanation: str | None = None
    media: list[LegacyMediaItem] = Field(default_factory=list)
    metadata: JSONObject = Field(default_factory=dict)


class LegacyMigrationBundle(BaseModel):
    """Versioned normal form accepted from Vibes and Piclaw exporters."""

    model_config = ConfigDict(extra="forbid")

    format: Literal["tau-legacy-migration"] = "tau-legacy-migration"
    version: Literal[1] = 1
    sessions: list[LegacySession]


@dataclass(frozen=True, slots=True)
class MigratedSession:
    source_kind: str
    source_session_id: str
    session_id: str
    agent_name: str
    workspace_id: str
    timeline_ids: dict[str, str]
    media_ids: dict[str, str]


@dataclass(frozen=True, slots=True)
class MigrationManifest:
    migration_id: str
    created_at: str
    sessions: tuple[MigratedSession, ...]

    def to_json(self) -> str:
        return (
            json.dumps(
                {
                    "format": "tau-migration-rollback",
                    "version": 1,
                    "migration_id": self.migration_id,
                    "created_at": self.created_at,
                    "sessions": [
                        {
                            "source_kind": session.source_kind,
                            "source_session_id": session.source_session_id,
                            "session_id": session.session_id,
                            "agent_name": session.agent_name,
                            "workspace_id": session.workspace_id,
                            "timeline_ids": session.timeline_ids,
                            "media_ids": session.media_ids,
                        }
                        for session in self.sessions
                    ],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    @classmethod
    def from_json(cls, text: str) -> MigrationManifest:
        try:
            raw = json.loads(text)
            if (
                not isinstance(raw, dict)
                or raw.get("format") != "tau-migration-rollback"
                or raw.get("version") != 1
                or not isinstance(raw.get("sessions"), list)
            ):
                raise ValueError("Unsupported rollback manifest")
            sessions = tuple(
                MigratedSession(
                    source_kind=str(item["source_kind"]),
                    source_session_id=str(item["source_session_id"]),
                    session_id=str(item["session_id"]),
                    agent_name=str(item["agent_name"]),
                    workspace_id=str(item["workspace_id"]),
                    timeline_ids=_string_mapping(item["timeline_ids"]),
                    media_ids=_string_mapping(item["media_ids"]),
                )
                for item in raw["sessions"]
                if isinstance(item, dict)
            )
            if len(sessions) != len(raw["sessions"]):
                raise ValueError("Invalid rollback session record")
            return cls(
                migration_id=str(raw["migration_id"]),
                created_at=str(raw["created_at"]),
                sessions=sessions,
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise SessionInterchangeError(f"Invalid rollback manifest: {exc}") from exc


class LegacyMigrationService:
    """Import a normalised legacy bundle and issue a verifiable rollback manifest."""

    def __init__(self, database: SqliteDatabase) -> None:
        self.database = database

    def parse_bundle(self, text: str) -> LegacyMigrationBundle:
        try:
            bundle = LegacyMigrationBundle.model_validate_json(text)
        except ValidationError as exc:
            raise SessionInterchangeError(f"Invalid legacy migration bundle: {exc}") from exc
        if not bundle.sessions:
            raise SessionInterchangeError("Legacy migration bundle contains no sessions")
        identities: set[tuple[str, str]] = set()
        entry_ids: set[str] = set()
        for session in bundle.sessions:
            identity = (session.source_kind, session.source_session_id)
            if identity in identities:
                raise SessionInterchangeError(
                    f"Duplicate legacy session identity: {session.source_kind}:"
                    f"{session.source_session_id}"
                )
            identities.add(identity)
            validate_agent_name(session.agent_name)
            validate_entry_sequence(session.entries)
            for entry in session.entries:
                if entry.id in entry_ids:
                    raise SessionInterchangeError(
                        f"Duplicate entry id across legacy sessions: {entry.id}"
                    )
                entry_ids.add(entry.id)
            _validate_source_ids(session)
            for media in session.media:
                _decode_media(media)
        return cast(LegacyMigrationBundle, bundle)

    async def import_bundle(self, bundle: LegacyMigrationBundle) -> MigrationManifest:
        # Revalidate model instances assembled by callers rather than parsed from JSON.
        parsed = self.parse_bundle(bundle.model_dump_json())
        migration_id = uuid4().hex
        timestamp = datetime.now(UTC).isoformat()

        async def write(transaction: SqliteTransaction) -> MigrationManifest:
            migrated: list[MigratedSession] = []
            for source in parsed.sessions:
                migrated.append(
                    await self._import_session(
                        transaction,
                        source,
                        migration_id=migration_id,
                        timestamp=timestamp,
                    )
                )
            return MigrationManifest(
                migration_id=migration_id,
                created_at=timestamp,
                sessions=tuple(migrated),
            )

        return await self.database.write(write)

    async def rollback(self, manifest: MigrationManifest) -> int:
        """Delete only sessions carrying the matching migration marker."""

        async def write(transaction: SqliteTransaction) -> int:
            for migrated in manifest.sessions:
                row = await transaction.fetch_one(
                    "SELECT metadata_json FROM sessions WHERE session_id = ?",
                    (migrated.session_id,),
                )
                if row is None:
                    raise SessionInterchangeError(
                        f"Cannot roll back missing session: {migrated.session_id}"
                    )
                metadata = json.loads(str(row["metadata_json"]))
                marker = metadata.get("legacy_import") if isinstance(metadata, dict) else None
                if (
                    not isinstance(marker, dict)
                    or marker.get("migration_id") != manifest.migration_id
                ):
                    raise SessionInterchangeError(
                        f"Session does not belong to migration {manifest.migration_id}: "
                        f"{migrated.session_id}"
                    )
            for migrated in manifest.sessions:
                await transaction.execute(
                    "DELETE FROM media_items WHERE session_id = ?",
                    (migrated.session_id,),
                )
                await transaction.execute(
                    "DELETE FROM sessions WHERE session_id = ?",
                    (migrated.session_id,),
                )
            await transaction.execute(
                """
                DELETE FROM media_blobs
                WHERE NOT EXISTS(
                    SELECT 1 FROM media_items
                    WHERE media_items.blob_id = media_blobs.blob_id
                       OR media_items.thumbnail_blob_id = media_blobs.blob_id
                )
                """
            )
            for workspace_id in {item.workspace_id for item in manifest.sessions}:
                await transaction.execute(
                    """
                    DELETE FROM workspaces
                    WHERE workspace_id = ?
                      AND NOT EXISTS(
                        SELECT 1 FROM sessions WHERE sessions.workspace_id = workspaces.workspace_id
                      )
                    """,
                    (workspace_id,),
                )
            return len(manifest.sessions)

        return await self.database.write(write)

    async def _import_session(
        self,
        transaction: SqliteTransaction,
        source: LegacySession,
        *,
        migration_id: str,
        timestamp: str,
    ) -> MigratedSession:
        session_id = uuid4().hex
        workspace_root = Path(source.workspace_root).expanduser().resolve()
        workspace_id = workspace_id_for_path(workspace_root)
        agent_name = await _allocate_agent_name(transaction, source.agent_name)
        timeline_ids = {item.source_id: uuid4().hex for item in source.timeline}
        media_ids = {item.source_id: uuid4().hex for item in source.media}
        legacy_metadata: dict[str, JSONValue] = {
            "migration_id": migration_id,
            "source_kind": source.source_kind,
            "source_session_id": source.source_session_id,
            "timeline_ids": cast(dict[str, JSONValue], timeline_ids),
            "media_ids": cast(dict[str, JSONValue], media_ids),
        }
        if source.chat_jid is not None:
            legacy_metadata["chat_jid"] = source.chat_jid
        metadata: dict[str, JSONValue] = dict(source.metadata)
        metadata["legacy_import"] = legacy_metadata
        if source.chat_jid is not None:
            metadata["chat_jid"] = source.chat_jid

        for entry in source.entries:
            collision = await transaction.fetch_one(
                "SELECT session_id FROM session_entries WHERE entry_id = ?",
                (entry.id,),
            )
            if collision is not None:
                raise SessionInterchangeError(f"Legacy entry id already exists: {entry.id}")

        await transaction.execute(
            """
            INSERT INTO workspaces(workspace_id, root_path, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(root_path) DO UPDATE SET updated_at = excluded.updated_at
            """,
            (workspace_id, str(workspace_root), timestamp, timestamp),
        )
        await transaction.execute(
            """
            INSERT INTO sessions(
                session_id, workspace_id, agent_name, title, provider_name, model,
                thinking_level, created_at, updated_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                workspace_id,
                agent_name,
                source.title,
                source.provider_name,
                source.model,
                source.thinking_level,
                timestamp,
                timestamp,
                json.dumps(metadata, separators=(",", ":"), sort_keys=True),
            ),
        )
        if source.entries:
            storage = SqliteSessionStorage(self.database, session_id)
            await storage.append_many_in_transaction(transaction, source.entries)
        if source.plan_markdown is not None:
            await transaction.execute(
                """
                INSERT INTO session_plans(
                    session_id, markdown, explanation, revision, updated_at, updated_by
                ) VALUES (?, ?, ?, 1, ?, ?)
                """,
                (
                    session_id,
                    source.plan_markdown,
                    source.plan_explanation,
                    timestamp,
                    f"migration:{source.source_kind}",
                ),
            )
        for message in source.timeline:
            public_id = timeline_ids[message.source_id]
            created_at = message.created_at or timestamp
            await transaction.execute(
                """
                INSERT INTO timeline_messages(
                    public_id, session_id, role, content, content_blocks_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    public_id,
                    session_id,
                    message.role,
                    message.content,
                    _dump_optional_blocks(message.content_blocks),
                    created_at,
                    created_at,
                ),
            )
        for media in source.media:
            content = _decode_media(media)
            digest = sha256(content).hexdigest()
            blob = await transaction.fetch_one(
                "SELECT blob_id FROM media_blobs WHERE sha256 = ?",
                (digest,),
            )
            if blob is None:
                blob_id = uuid4().hex
                await transaction.execute(
                    """
                    INSERT INTO media_blobs(blob_id, sha256, content, byte_length, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (blob_id, digest, content, len(content), timestamp),
                )
            else:
                blob_id = str(blob["blob_id"])
            item_metadata: dict[str, JSONValue] = dict(media.metadata)
            item_metadata["legacy_source_id"] = media.source_id
            await transaction.execute(
                """
                INSERT INTO media_items(
                    media_id, session_id, blob_id, filename, media_type,
                    width, height, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    media_ids[media.source_id],
                    session_id,
                    blob_id,
                    media.filename,
                    media.media_type,
                    media.width,
                    media.height,
                    json.dumps(item_metadata, separators=(",", ":"), sort_keys=True),
                    timestamp,
                ),
            )
        return MigratedSession(
            source_kind=source.source_kind,
            source_session_id=source.source_session_id,
            session_id=session_id,
            agent_name=agent_name,
            workspace_id=workspace_id,
            timeline_ids=timeline_ids,
            media_ids=media_ids,
        )


async def _agent_name_exists(transaction: SqliteTransaction, agent_name: str) -> bool:
    row = await transaction.fetch_one(
        """
        SELECT 1 FROM sessions
        WHERE agent_name = ? COLLATE NOCASE AND archived_at IS NULL
        """,
        (agent_name,),
    )
    return row is not None


async def _allocate_agent_name(transaction: SqliteTransaction, base: str) -> str:
    validated = validate_agent_name(base)
    suffix = 1
    while True:
        candidate = validated if suffix == 1 else f"{validated}-{suffix}"
        if not await _agent_name_exists(transaction, candidate):
            return candidate
        suffix += 1


def _validate_source_ids(session: LegacySession) -> None:
    timeline_ids = [item.source_id for item in session.timeline]
    media_ids = [item.source_id for item in session.media]
    if len(set(timeline_ids)) != len(timeline_ids):
        raise SessionInterchangeError(
            f"Legacy session has duplicate timeline source IDs: {session.source_session_id}"
        )
    if len(set(media_ids)) != len(media_ids):
        raise SessionInterchangeError(
            f"Legacy session has duplicate media source IDs: {session.source_session_id}"
        )


def _decode_media(media: LegacyMediaItem) -> bytes:
    try:
        content = base64.b64decode(media.content_base64, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise SessionInterchangeError(
            f"Invalid base64 media content for source item {media.source_id}"
        ) from exc
    if not content:
        raise SessionInterchangeError(f"Legacy media content is empty: {media.source_id}")
    return content


def _dump_optional_blocks(blocks: list[JSONObject] | None) -> str | None:
    if blocks is None:
        return None
    return json.dumps(blocks, separators=(",", ":"), sort_keys=True)


def _string_mapping(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(item, str) for key, item in value.items()
    ):
        raise ValueError("Expected a string mapping")
    return dict(value)
