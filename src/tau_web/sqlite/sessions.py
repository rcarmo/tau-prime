"""Durable workspace, session lifecycle, alias, and address repositories."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Final, cast
from uuid import uuid4

from aiosqlite import Row

from tau_agent.types import JSONValue
from tau_web.sqlite.connection import SqliteReader
from tau_web.sqlite.repositories import RecordNotFoundError, RepositoryError, SqliteRepository
from tau_web.sqlite.writer import SqliteTransaction

_AGENT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_MAX_AGENT_NAME_BYTES = 128
_MISSING: Final[object] = object()


class InvalidAgentNameError(RepositoryError):
    """Raised when a requested local agent alias is unsafe or malformed."""


class AgentNameConflictError(RepositoryError):
    """Raised when an active session already owns an alias."""


class SessionMetadataConflictError(RepositoryError):
    """Raised when a session metadata update uses a stale snapshot."""

    def __init__(
        self,
        session_id: str,
        *,
        expected_updated_at: str,
        actual_updated_at: str | None,
    ) -> None:
        self.session_id = session_id
        self.expected_updated_at = expected_updated_at
        self.actual_updated_at = actual_updated_at
        super().__init__(
            "Session metadata conflict for "
            f"{session_id}: expected updated_at {expected_updated_at!r}, "
            f"actual {actual_updated_at!r}"
        )


@dataclass(frozen=True, slots=True)
class WorkspaceRecord:
    workspace_id: str
    root_path: Path
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class SessionRecord:
    session_id: str
    workspace_id: str
    agent_name: str
    title: str | None
    provider_name: str
    model: str
    thinking_level: str | None
    active_leaf_entry_id: str | None
    created_at: str
    updated_at: str
    archived_at: str | None
    metadata: dict[str, JSONValue]


class SessionRepository(SqliteRepository):
    """Own durable workspaces, sessions, aliases, and local address resolution."""

    async def ensure_workspace(self, root_path: Path) -> WorkspaceRecord:
        resolved = root_path.expanduser().resolve()
        workspace_id = workspace_id_for_path(resolved)
        timestamp = _timestamp()

        async def write(transaction: SqliteTransaction) -> WorkspaceRecord:
            await transaction.execute(
                """
                INSERT INTO workspaces(workspace_id, root_path, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(root_path) DO UPDATE SET updated_at = excluded.updated_at
                """,
                (workspace_id, str(resolved), timestamp, timestamp),
            )
            row = await transaction.fetch_one(
                """
                SELECT workspace_id, root_path, created_at, updated_at
                FROM workspaces WHERE root_path = ?
                """,
                (str(resolved),),
            )
            if row is None:
                raise RuntimeError("Workspace upsert did not return a record")
            return _workspace_from_row(row)

        return await self.database.write(write)

    async def get_workspace(self, workspace_id: str) -> WorkspaceRecord | None:
        async def read(reader: SqliteReader) -> WorkspaceRecord | None:
            row = await reader.fetch_one(
                """
                SELECT workspace_id, root_path, created_at, updated_at
                FROM workspaces WHERE workspace_id = ?
                """,
                (workspace_id,),
            )
            return _workspace_from_row(row) if row is not None else None

        return await self.database.read(read)

    async def create(
        self,
        *,
        workspace_root: Path,
        provider_name: str,
        model: str,
        agent_name: str | None = None,
        title: str | None = None,
        thinking_level: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, JSONValue] | None = None,
    ) -> SessionRecord:
        if not provider_name.strip():
            raise ValueError("Provider name must not be empty")
        if not model.strip():
            raise ValueError("Model must not be empty")
        requested_name = validate_agent_name(agent_name) if agent_name is not None else None
        resolved_root = workspace_root.expanduser().resolve()
        workspace_id = workspace_id_for_path(resolved_root)
        record_id = session_id or uuid4().hex
        timestamp = _timestamp()
        normalized_metadata, metadata_json = _prepare_metadata(metadata)

        async def write(transaction: SqliteTransaction) -> SessionRecord:
            await transaction.execute(
                """
                INSERT INTO workspaces(workspace_id, root_path, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(root_path) DO UPDATE SET updated_at = excluded.updated_at
                """,
                (workspace_id, str(resolved_root), timestamp, timestamp),
            )
            selected_name = requested_name
            if selected_name is None:
                selected_name = await _allocate_agent_name(transaction, "default")
            elif await _active_agent_name_exists(transaction, selected_name):
                raise AgentNameConflictError(f"Active agent name already exists: @{selected_name}")
            await transaction.execute(
                """
                INSERT INTO sessions(
                    session_id, workspace_id, agent_name, title, provider_name, model,
                    thinking_level, created_at, updated_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    workspace_id,
                    selected_name,
                    title,
                    provider_name.strip(),
                    model.strip(),
                    thinking_level,
                    timestamp,
                    timestamp,
                    metadata_json,
                ),
            )
            return SessionRecord(
                session_id=record_id,
                workspace_id=workspace_id,
                agent_name=selected_name,
                title=title,
                provider_name=provider_name.strip(),
                model=model.strip(),
                thinking_level=thinking_level,
                active_leaf_entry_id=None,
                created_at=timestamp,
                updated_at=timestamp,
                archived_at=None,
                metadata=normalized_metadata,
            )

        return await self.database.write(write)

    async def get(self, session_id: str) -> SessionRecord | None:
        async def read(reader: SqliteReader) -> SessionRecord | None:
            row = await reader.fetch_one(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            return _session_from_row(row) if row is not None else None

        return await self.database.read(read)

    async def list(
        self,
        *,
        workspace_id: str | None = None,
        include_archived: bool = False,
    ) -> list[SessionRecord]:
        clauses: list[str] = []
        parameters: list[object] = []
        if workspace_id is not None:
            clauses.append("workspace_id = ?")
            parameters.append(workspace_id)
        if not include_archived:
            clauses.append("archived_at IS NULL")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        async def read(reader: SqliteReader) -> list[SessionRecord]:
            rows = await reader.fetch_all(
                f"SELECT * FROM sessions {where} ORDER BY updated_at DESC, session_id",  # noqa: S608
                parameters,
            )
            return [_session_from_row(row) for row in rows]

        return await self.database.read(read)

    async def patch(
        self,
        session_id: str,
        *,
        agent_name: str | None = None,
        provider_name: str | None = None,
        model: str | None = None,
        title: str | None = None,
        title_provided: bool = False,
        expected_updated_at: str | None = None,
    ) -> SessionRecord:
        requested_name = validate_agent_name(agent_name) if agent_name is not None else None
        normalized_provider_name = provider_name.strip() if provider_name is not None else None
        if normalized_provider_name is not None and not normalized_provider_name:
            raise ValueError("Provider name must not be empty")
        normalized_model = model.strip() if model is not None else None
        if normalized_model is not None and not normalized_model:
            raise ValueError("Model must not be empty")
        if (
            requested_name is None
            and normalized_provider_name is None
            and normalized_model is None
            and not title_provided
        ):
            raise ValueError("At least one session field must be provided")
        timestamp = _timestamp()

        async def write(transaction: SqliteTransaction) -> SessionRecord:
            current = _session_from_row(await _require_session(transaction, session_id))
            if current.archived_at is not None:
                raise RepositoryError("Archived sessions must be restored before updating")
            if expected_updated_at is not None and current.updated_at != expected_updated_at:
                raise SessionMetadataConflictError(
                    session_id,
                    expected_updated_at=expected_updated_at,
                    actual_updated_at=current.updated_at,
                )

            selected_name = current.agent_name
            if requested_name is not None:
                owner = await transaction.fetch_one(
                    """
                    SELECT session_id FROM sessions
                    WHERE agent_name = ? COLLATE NOCASE AND archived_at IS NULL
                    """,
                    (requested_name,),
                )
                if owner is not None and str(owner["session_id"]) != session_id:
                    raise AgentNameConflictError(
                        f"Active agent name already exists: @{requested_name}"
                    )
                selected_name = requested_name

            changed = await transaction.execute(
                """
                UPDATE sessions
                SET agent_name = ?, title = ?, provider_name = ?, model = ?, updated_at = ?
                WHERE session_id = ? AND updated_at = ?
                """,
                (
                    selected_name,
                    title if title_provided else current.title,
                    normalized_provider_name
                    if normalized_provider_name is not None
                    else current.provider_name,
                    normalized_model if normalized_model is not None else current.model,
                    timestamp,
                    session_id,
                    current.updated_at,
                ),
            )
            if changed != 1:
                row = await transaction.fetch_one(
                    "SELECT updated_at FROM sessions WHERE session_id = ?",
                    (session_id,),
                )
                actual_updated_at = (
                    str(row["updated_at"])
                    if row is not None and row["updated_at"] is not None
                    else None
                )
                raise SessionMetadataConflictError(
                    session_id,
                    expected_updated_at=current.updated_at,
                    actual_updated_at=actual_updated_at,
                )
            return _session_from_row(await _require_session(transaction, session_id))

        return await self.database.write(write)

    async def update_metadata(
        self,
        session_id: str,
        *,
        provider_name: str | None = None,
        model: str | None = None,
        title: str | None = None,
        thinking_level: str | None | object = _MISSING,
        expected_updated_at: str | None = None,
        transaction: SqliteTransaction | None = None,
    ) -> SessionRecord:
        normalized_provider_name = provider_name.strip() if provider_name is not None else None
        if normalized_provider_name is not None and not normalized_provider_name:
            raise ValueError("Provider name must not be empty")
        normalized_model = model.strip() if model is not None else None
        if normalized_model is not None and not normalized_model:
            raise ValueError("Model must not be empty")
        normalized_thinking_level = _normalize_optional_text_field(
            thinking_level,
            field="Thinking level",
        )
        timestamp = _timestamp()

        async def write(active_transaction: SqliteTransaction) -> SessionRecord:
            return await self._update_metadata_in_transaction(
                active_transaction,
                session_id,
                provider_name=normalized_provider_name,
                model=normalized_model,
                title=title,
                thinking_level=normalized_thinking_level,
                expected_updated_at=expected_updated_at,
                timestamp=timestamp,
            )

        if transaction is not None:
            return await write(transaction)
        return await self.database.write(write)

    async def _update_metadata_in_transaction(
        self,
        transaction: SqliteTransaction,
        session_id: str,
        *,
        provider_name: str | None,
        model: str | None,
        title: str | None,
        thinking_level: str | None | object,
        expected_updated_at: str | None,
        timestamp: str,
    ) -> SessionRecord:
        current = _session_from_row(await _require_session(transaction, session_id))
        if current.archived_at is not None:
            raise RepositoryError("Archived sessions must be restored before updating")
        if expected_updated_at is not None and current.updated_at != expected_updated_at:
            raise SessionMetadataConflictError(
                session_id,
                expected_updated_at=expected_updated_at,
                actual_updated_at=current.updated_at,
            )
        changed = await transaction.execute(
            """
            UPDATE sessions
            SET title = ?, provider_name = ?, model = ?, thinking_level = ?, updated_at = ?
            WHERE session_id = ? AND updated_at = ?
            """,
            (
                title if title is not None else current.title,
                provider_name if provider_name is not None else current.provider_name,
                model if model is not None else current.model,
                thinking_level if thinking_level is not _MISSING else current.thinking_level,
                timestamp,
                session_id,
                current.updated_at,
            ),
        )
        if changed != 1:
            row = await transaction.fetch_one(
                "SELECT updated_at FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            actual_updated_at = (
                str(row["updated_at"])
                if row is not None and row["updated_at"] is not None
                else None
            )
            raise SessionMetadataConflictError(
                session_id,
                expected_updated_at=current.updated_at,
                actual_updated_at=actual_updated_at,
            )
        return _session_from_row(await _require_session(transaction, session_id))

    async def rename(self, session_id: str, agent_name: str) -> SessionRecord:
        selected_name = validate_agent_name(agent_name)
        timestamp = _timestamp()

        async def write(transaction: SqliteTransaction) -> SessionRecord:
            row = await _require_session(transaction, session_id)
            if row["archived_at"] is not None:
                raise RepositoryError("Archived sessions must be restored before renaming")
            owner = await transaction.fetch_one(
                """
                SELECT session_id FROM sessions
                WHERE agent_name = ? COLLATE NOCASE AND archived_at IS NULL
                """,
                (selected_name,),
            )
            if owner is not None and str(owner["session_id"]) != session_id:
                raise AgentNameConflictError(f"Active agent name already exists: @{selected_name}")
            await transaction.execute(
                "UPDATE sessions SET agent_name = ?, updated_at = ? WHERE session_id = ?",
                (selected_name, timestamp, session_id),
            )
            updated = await _require_session(transaction, session_id)
            return _session_from_row(updated)

        return await self.database.write(write)

    async def archive(self, session_id: str) -> SessionRecord:
        timestamp = _timestamp()

        async def write(transaction: SqliteTransaction) -> SessionRecord:
            await _require_session(transaction, session_id)
            await transaction.execute(
                """
                UPDATE sessions SET archived_at = ?, updated_at = ?
                WHERE session_id = ? AND archived_at IS NULL
                """,
                (timestamp, timestamp, session_id),
            )
            return _session_from_row(await _require_session(transaction, session_id))

        return await self.database.write(write)

    async def restore(self, session_id: str, *, agent_name: str | None = None) -> SessionRecord:
        requested_name = validate_agent_name(agent_name) if agent_name is not None else None
        timestamp = _timestamp()

        async def write(transaction: SqliteTransaction) -> SessionRecord:
            row = await _require_session(transaction, session_id)
            selected_name = requested_name or str(row["agent_name"])
            if row["archived_at"] is None:
                if selected_name.casefold() == str(row["agent_name"]).casefold():
                    return _session_from_row(row)
                owner = await transaction.fetch_one(
                    """
                    SELECT session_id FROM sessions
                    WHERE agent_name = ? COLLATE NOCASE AND archived_at IS NULL
                    """,
                    (selected_name,),
                )
                if owner is not None and str(owner["session_id"]) != session_id:
                    raise AgentNameConflictError(
                        f"Active agent name already exists: @{selected_name}"
                    )
            elif await _active_agent_name_exists(transaction, selected_name):
                if requested_name is not None:
                    raise AgentNameConflictError(
                        f"Active agent name already exists: @{selected_name}"
                    )
                selected_name = await _allocate_agent_name(transaction, selected_name)
            await transaction.execute(
                """
                UPDATE sessions
                SET agent_name = ?, archived_at = NULL, updated_at = ?
                WHERE session_id = ?
                """,
                (selected_name, timestamp, session_id),
            )
            return _session_from_row(await _require_session(transaction, session_id))

        return await self.database.write(write)

    async def resolve(
        self, address: str, *, include_archived: bool = False
    ) -> SessionRecord | None:
        normalized = address.strip()
        if not normalized:
            return None
        archived_clause = "" if include_archived else " AND archived_at IS NULL"
        if normalized.startswith("@"):
            query = f"agent_name = ? COLLATE NOCASE{archived_clause}"
            parameter = validate_agent_name(normalized[1:])
        elif normalized.startswith("session:"):
            query = f"session_id = ?{archived_clause}"
            parameter = normalized.removeprefix("session:")
        elif normalized.startswith("chat_jid:"):
            query = f"json_extract(metadata_json, '$.chat_jid') = ?{archived_clause}"
            parameter = normalized.removeprefix("chat_jid:")
        else:
            query = f"session_id = ?{archived_clause}"
            parameter = normalized

        async def read(reader: SqliteReader) -> SessionRecord | None:
            row = await reader.fetch_one(
                f"SELECT * FROM sessions WHERE {query}",  # noqa: S608
                (parameter,),
            )
            return _session_from_row(row) if row is not None else None

        return await self.database.read(read)


def validate_agent_name(agent_name: str) -> str:
    """Validate and normalise one local session alias."""
    normalized = agent_name.strip().removeprefix("@")
    if not _AGENT_NAME_PATTERN.fullmatch(normalized):
        raise InvalidAgentNameError(
            "Agent name must start with a letter or digit and contain only "
            "letters, digits, '.', '_' or '-'"
        )
    if len(normalized.encode("utf-8")) > _MAX_AGENT_NAME_BYTES:
        raise InvalidAgentNameError(f"Agent name must be at most {_MAX_AGENT_NAME_BYTES} bytes")
    return normalized


def workspace_id_for_path(root_path: Path) -> str:
    resolved = root_path.expanduser().resolve()
    return sha256(str(resolved).encode("utf-8")).hexdigest()


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _normalize_optional_text_field(
    value: str | None | object,
    *,
    field: str,
) -> str | None | object:
    if value is _MISSING:
        return _MISSING
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string, null, or the internal missing sentinel")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    return normalized


async def _require_session(transaction: SqliteTransaction, session_id: str) -> Row:
    row = await transaction.fetch_one("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
    if row is None:
        raise RecordNotFoundError(f"Unknown session: {session_id}")
    return row


async def _active_agent_name_exists(transaction: SqliteTransaction, agent_name: str) -> bool:
    row = await transaction.fetch_one(
        """
        SELECT 1 FROM sessions
        WHERE agent_name = ? COLLATE NOCASE AND archived_at IS NULL
        """,
        (agent_name,),
    )
    return row is not None


async def _allocate_agent_name(transaction: SqliteTransaction, base: str) -> str:
    candidate = validate_agent_name(base)
    if not await _active_agent_name_exists(transaction, candidate):
        return candidate
    suffix = 2
    while True:
        candidate = validate_agent_name(f"{base}-{suffix}")
        if not await _active_agent_name_exists(transaction, candidate):
            return candidate
        suffix += 1


def _workspace_from_row(row: Row) -> WorkspaceRecord:
    return WorkspaceRecord(
        workspace_id=str(row["workspace_id"]),
        root_path=Path(str(row["root_path"])),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _prepare_metadata(
    metadata: dict[str, JSONValue] | None,
) -> tuple[dict[str, JSONValue], str]:
    normalized = dict(metadata or {})
    if not all(isinstance(key, str) for key in normalized):
        raise RepositoryError("Session metadata keys must be strings")
    try:
        encoded = json.dumps(
            normalized,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise RepositoryError("Session metadata must contain valid JSON values") from exc
    return normalized, encoded


def _session_from_row(row: Row) -> SessionRecord:
    raw_metadata = json.loads(str(row["metadata_json"]))
    if not isinstance(raw_metadata, dict) or not all(isinstance(key, str) for key in raw_metadata):
        raise RuntimeError("Session metadata is not a JSON object")
    metadata = cast(dict[str, JSONValue], raw_metadata)
    return SessionRecord(
        session_id=str(row["session_id"]),
        workspace_id=str(row["workspace_id"]),
        agent_name=str(row["agent_name"]),
        title=str(row["title"]) if row["title"] is not None else None,
        provider_name=str(row["provider_name"]),
        model=str(row["model"]),
        thinking_level=(str(row["thinking_level"]) if row["thinking_level"] is not None else None),
        active_leaf_entry_id=(
            str(row["active_leaf_entry_id"]) if row["active_leaf_entry_id"] is not None else None
        ),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        archived_at=str(row["archived_at"]) if row["archived_at"] is not None else None,
        metadata=metadata,
    )
