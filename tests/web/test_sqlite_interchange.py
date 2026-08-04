from __future__ import annotations

import base64
import json
import stat
from pathlib import Path

import pytest

from tau_agent import UserMessage
from tau_agent.session import LeafEntry, MessageEntry, SessionInfoEntry
from tau_agent.session.jsonl import entry_to_json_line
from tau_web.sqlite.connection import SqliteDatabase, SqliteReader
from tau_web.sqlite.interchange import (
    JsonlImportOptions,
    SessionInterchange,
    SessionInterchangeError,
)
from tau_web.sqlite.legacy_migration import (
    LegacyMediaItem,
    LegacyMigrationBundle,
    LegacyMigrationService,
    LegacySession,
    LegacyTimelineMessage,
    MigrationManifest,
)
from tau_web.sqlite.session_storage import SqliteSessionStorage
from tau_web.sqlite.sessions import SessionRepository


def _jsonl_entries() -> list[SessionInfoEntry | MessageEntry | LeafEntry]:
    info = SessionInfoEntry(id="info", cwd="/workspace", title="Imported")
    message = MessageEntry(
        id="message",
        parent_id=info.id,
        message=UserMessage(content="hello"),
    )
    leaf = LeafEntry(id="leaf", parent_id=message.id, entry_id=message.id)
    return [info, message, leaf]


def _jsonl_fixture() -> tuple[list[SessionInfoEntry | MessageEntry | LeafEntry], str]:
    entries = _jsonl_entries()
    return entries, "".join(entry_to_json_line(entry) for entry in entries)


@pytest.mark.anyio
async def test_jsonl_import_export_round_trip_is_atomic(tmp_path: Path) -> None:
    entries, jsonl_text = _jsonl_fixture()

    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        interchange = SessionInterchange(database)
        result = await interchange.import_jsonl(
            jsonl_text,
            options=JsonlImportOptions(
                workspace_root=tmp_path / "workspace",
                provider_name="test",
                model="model",
                session_id="imported",
                agent_name="worker",
                title="Imported",
                metadata={"fixture": True},
            ),
        )

        exported = await interchange.export_jsonl(result.session_id)

        assert result.entry_count == 3
        assert result.agent_name == "worker"
        assert interchange.parse_jsonl(exported) == entries
        assert await SqliteSessionStorage(database, result.session_id).read_all() == entries
        session = await SessionRepository(database).get(result.session_id)
        assert session is not None
        assert session.metadata == {
            "fixture": True,
            "interchange_format": "tau-jsonl",
        }


@pytest.mark.anyio
async def test_jsonl_import_validates_before_writing(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        interchange = SessionInterchange(database)
        invalid = MessageEntry(
            id="message",
            parent_id="missing",
            message=UserMessage(content="invalid"),
        )

        with pytest.raises(SessionInterchangeError, match="not imported earlier"):
            await interchange.import_jsonl(
                entry_to_json_line(invalid),
                options=JsonlImportOptions(
                    workspace_root=tmp_path / "new-workspace",
                    provider_name="test",
                    model="model",
                    session_id="invalid",
                ),
            )

        assert await SessionRepository(database).get("invalid") is None

        async def workspace_count(reader: SqliteReader) -> int:
            row = await reader.fetch_one("SELECT COUNT(*) FROM workspaces")
            assert row is not None
            return int(row[0])

        assert await database.read(workspace_count) == 0


@pytest.mark.anyio
async def test_jsonl_import_rejects_database_entry_collision_without_partial_session(
    tmp_path: Path,
) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        interchange = SessionInterchange(database)
        options = JsonlImportOptions(
            workspace_root=tmp_path,
            provider_name="test",
            model="model",
            session_id="first",
        )
        _, jsonl_text = _jsonl_fixture()
        await interchange.import_jsonl(jsonl_text, options=options)

        with pytest.raises(SessionInterchangeError, match="another session"):
            await interchange.import_jsonl(
                jsonl_text,
                options=JsonlImportOptions(
                    workspace_root=tmp_path,
                    provider_name="test",
                    model="model",
                    session_id="second",
                ),
            )

        assert await SessionRepository(database).get("second") is None


@pytest.mark.anyio
async def test_jsonl_file_import_export_is_private_and_refuses_overwrite(
    tmp_path: Path,
) -> None:
    entries, jsonl_text = _jsonl_fixture()
    source = tmp_path / "source.jsonl"
    source.write_text(jsonl_text, encoding="utf-8")
    destination = tmp_path / "export" / "session.jsonl"

    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        interchange = SessionInterchange(database)
        imported = await interchange.import_jsonl_file(
            source,
            options=JsonlImportOptions(
                workspace_root=tmp_path,
                provider_name="test",
                model="model",
            ),
        )
        assert (
            await interchange.export_jsonl_file(
                imported.session_id,
                destination,
            )
            == destination.resolve()
        )
        assert stat.S_IMODE(destination.stat().st_mode) == 0o600
        assert interchange.parse_jsonl(destination.read_text(encoding="utf-8")) == entries

        with pytest.raises(SessionInterchangeError, match="already exists"):
            await interchange.export_jsonl_file(imported.session_id, destination)


@pytest.mark.anyio
async def test_legacy_bundle_maps_source_data_and_rolls_back(tmp_path: Path) -> None:
    entries, _ = _jsonl_fixture()
    media_bytes = b"legacy image bytes"
    source_one = LegacySession(
        source_kind="piclaw",
        source_session_id="piclaw:one",
        workspace_root=str(tmp_path / "workspace"),
        agent_name="worker",
        provider_name="test",
        model="model",
        title="Legacy one",
        chat_jid="web:one",
        entries=entries,
        timeline=[
            LegacyTimelineMessage(
                source_id="message:1",
                role="user",
                content="legacy timeline",
                content_blocks=[{"type": "text", "text": "legacy timeline"}],
            )
        ],
        plan_markdown="- [ ] migrated",
        plan_explanation="legacy plan",
        media=[
            LegacyMediaItem(
                source_id="media:1",
                filename="image.bin",
                media_type="application/octet-stream",
                content_base64=base64.b64encode(media_bytes).decode(),
                metadata={"caption": "legacy"},
            )
        ],
        metadata={"legacy_flag": True},
    )
    source_two = LegacySession(
        source_kind="vibes",
        source_session_id="vibes:two",
        workspace_root=str(tmp_path / "workspace"),
        agent_name="worker",
        provider_name="test",
        model="model",
        title="Legacy two",
    )
    bundle = LegacyMigrationBundle(sessions=[source_one, source_two])

    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        migration = LegacyMigrationService(database)
        parsed = migration.parse_bundle(bundle.model_dump_json())
        manifest = await migration.import_bundle(parsed)
        round_tripped_manifest = MigrationManifest.from_json(manifest.to_json())

        assert round_tripped_manifest == manifest
        assert [item.agent_name for item in manifest.sessions] == ["worker", "worker-2"]
        first = await SessionRepository(database).get(manifest.sessions[0].session_id)
        assert first is not None
        assert first.metadata["chat_jid"] == "web:one"
        marker = first.metadata["legacy_import"]
        assert isinstance(marker, dict)
        assert marker["source_session_id"] == "piclaw:one"
        assert marker["timeline_ids"] == manifest.sessions[0].timeline_ids
        assert marker["media_ids"] == manifest.sessions[0].media_ids

        async def imported_counts(reader: SqliteReader) -> tuple[int, int, int, int]:
            values: list[int] = []
            for table in (
                "timeline_messages",
                "session_plans",
                "media_items",
                "media_blobs",
            ):
                row = await reader.fetch_one(f"SELECT COUNT(*) FROM {table}")
                assert row is not None
                values.append(int(row[0]))
            return values[0], values[1], values[2], values[3]

        assert await database.read(imported_counts) == (1, 1, 1, 1)
        assert await migration.rollback(round_tripped_manifest) == 2
        assert await database.read(imported_counts) == (0, 0, 0, 0)
        assert await SessionRepository(database).list(include_archived=True) == []


@pytest.mark.anyio
async def test_legacy_bundle_validation_and_rollback_marker_protection(tmp_path: Path) -> None:
    invalid_json = json.dumps(
        {
            "format": "tau-legacy-migration",
            "version": 1,
            "sessions": [
                {
                    "source_kind": "piclaw",
                    "source_session_id": "source",
                    "workspace_root": str(tmp_path),
                    "agent_name": "worker",
                    "provider_name": "test",
                    "model": "model",
                    "media": [
                        {
                            "source_id": "bad",
                            "filename": "bad",
                            "media_type": "application/octet-stream",
                            "content_base64": "not base64",
                        }
                    ],
                }
            ],
        }
    )

    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        migration = LegacyMigrationService(database)
        with pytest.raises(SessionInterchangeError, match="base64"):
            migration.parse_bundle(invalid_json)
        assert await SessionRepository(database).list(include_archived=True) == []

        valid = LegacyMigrationBundle(
            sessions=[
                LegacySession(
                    source_kind="vibes",
                    source_session_id="source",
                    workspace_root=str(tmp_path),
                    agent_name="worker",
                    provider_name="test",
                    model="model",
                )
            ]
        )
        manifest = await migration.import_bundle(valid)
        tampered = MigrationManifest(
            migration_id="wrong",
            created_at=manifest.created_at,
            sessions=manifest.sessions,
        )
        with pytest.raises(SessionInterchangeError, match="does not belong"):
            await migration.rollback(tampered)
        assert len(await SessionRepository(database).list()) == 1
