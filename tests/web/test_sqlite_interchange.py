from __future__ import annotations

import base64
import json
import stat
from pathlib import Path

import pytest

from tau_agent import AssistantMessage, ToolCall, ToolResultMessage, UserMessage
from tau_agent.session import (
    CompactionEntry,
    CustomEntry,
    LabelEntry,
    LeafEntry,
    MessageEntry,
    ModelChangeEntry,
    SessionEntry,
    SessionInfoEntry,
    ThinkingLevelChangeEntry,
    path_to_entry,
)
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
async def test_jsonl_rich_interchange_round_trip_preserves_semantics_and_branches(
    tmp_path: Path,
) -> None:
    entries: list[SessionEntry] = [
        SessionInfoEntry(
            id="info",
            timestamp=1.0,
            created_at=1.0,
            cwd="/workspace/tau",
            title="Rich interchange source",
        ),
        ModelChangeEntry(
            id="model",
            parent_id="info",
            timestamp=2.0,
            model="source-model",
        ),
        ThinkingLevelChangeEntry(
            id="thinking",
            parent_id="model",
            timestamp=3.0,
            thinking_level="high",
        ),
        MessageEntry(
            id="user-root",
            parent_id="thinking",
            timestamp=4.0,
            message=UserMessage(content="Summarize current workspace state."),
        ),
        MessageEntry(
            id="assistant-left",
            parent_id="user-root",
            timestamp=5.0,
            message=AssistantMessage(
                content="I will read the project summary.",
                tool_calls=[
                    ToolCall(id="call-read", name="read", arguments={"path": "README.md"})
                ],
            ),
        ),
        MessageEntry(
            id="assistant-right",
            parent_id="user-root",
            timestamp=6.0,
            message=AssistantMessage(content="Alternative branch answer."),
        ),
        MessageEntry(
            id="tool-result",
            parent_id="assistant-left",
            timestamp=7.0,
            message=ToolResultMessage(
                tool_call_id="call-read",
                name="read",
                content="Loaded README.md",
                ok=True,
                data={"bytes": 512},
                details={"cached": False, "source": "disk"},
            ),
        ),
        CompactionEntry(
            id="compaction",
            parent_id="tool-result",
            timestamp=8.0,
            summary="Compacted earlier branch context.",
            replaces_entry_ids=["user-root", "assistant-left", "tool-result"],
            details={"reason": "token_budget", "token_estimate": 2048},
        ),
        LabelEntry(
            id="label",
            parent_id="compaction",
            timestamp=9.0,
            label="Left branch compacted",
        ),
        CustomEntry(
            id="custom",
            parent_id="label",
            timestamp=10.0,
            namespace="tau.tests.rich_interchange",
            data={"ok": True, "tags": ["alpha", "beta"], "stage": 1},
        ),
        LeafEntry(
            id="leaf-active",
            parent_id="custom",
            timestamp=11.0,
            entry_id="custom",
        ),
    ]
    source_jsonl = "".join(entry_to_json_line(entry) for entry in entries)

    async with SqliteDatabase(tmp_path / "source.sqlite3") as source_database:
        source_interchange = SessionInterchange(source_database)
        source_result = await source_interchange.import_jsonl(
            source_jsonl,
            options=JsonlImportOptions(
                workspace_root=tmp_path / "workspace-source",
                provider_name="test",
                model="source-model",
                session_id="rich-source",
                agent_name="rich-source-agent",
                title="Rich source session",
                thinking_level="high",
                metadata={"fixture": "rich", "nested": {"level": 1}},
            ),
        )
        first_export = await source_interchange.export_jsonl(source_result.session_id)
        source_round_trip = source_interchange.parse_jsonl(first_export)
        source_session = await SessionRepository(source_database).get(source_result.session_id)

    assert source_session is not None
    assert source_session.active_leaf_entry_id == "custom"
    assert source_session.metadata == {
        "fixture": "rich",
        "interchange_format": "tau-jsonl",
        "nested": {"level": 1},
    }

    async with SqliteDatabase(tmp_path / "target.sqlite3") as target_database:
        target_interchange = SessionInterchange(target_database)
        target_result = await target_interchange.import_jsonl(
            first_export,
            options=JsonlImportOptions(
                workspace_root=tmp_path / "workspace-target",
                provider_name="test",
                model="target-model",
                session_id="rich-target",
                agent_name="rich-target-agent",
                title="Rich target session",
                thinking_level="medium",
                metadata={"fixture": "rich", "nested": {"level": 1}},
            ),
        )
        second_export = await target_interchange.export_jsonl(target_result.session_id)
        target_round_trip = target_interchange.parse_jsonl(second_export)
        target_session = await SessionRepository(target_database).get(target_result.session_id)

    def canonical(payload: list[SessionEntry]) -> list[dict[str, object]]:
        return [entry.model_dump(mode="json") for entry in payload]

    def branch_leaf_ids(payload: list[SessionEntry]) -> list[str]:
        non_leaf = [entry for entry in payload if not isinstance(entry, LeafEntry)]
        non_leaf_parent_ids = {entry.parent_id for entry in non_leaf if entry.parent_id is not None}
        return [entry.id for entry in non_leaf if entry.id not in non_leaf_parent_ids]

    assert target_session is not None
    assert target_session.active_leaf_entry_id == "custom"
    assert target_session.metadata == {
        "fixture": "rich",
        "interchange_format": "tau-jsonl",
        "nested": {"level": 1},
    }
    assert canonical(source_round_trip) == canonical(entries)
    assert canonical(target_round_trip) == canonical(source_round_trip)
    assert [entry.id for entry in target_round_trip] == [entry.id for entry in entries]
    assert {entry.id: entry.parent_id for entry in target_round_trip} == {
        entry.id: entry.parent_id for entry in source_round_trip
    }
    assert [
        (entry.id, entry.parent_id, entry.entry_id)
        for entry in target_round_trip
        if isinstance(entry, LeafEntry)
    ] == [
        (entry.id, entry.parent_id, entry.entry_id)
        for entry in source_round_trip
        if isinstance(entry, LeafEntry)
    ]
    assert branch_leaf_ids(source_round_trip) == ["assistant-right", "custom"]
    assert branch_leaf_ids(target_round_trip) == ["assistant-right", "custom"]
    assert {
        leaf_id: [entry.id for entry in path_to_entry(source_round_trip, leaf_id)]
        for leaf_id in branch_leaf_ids(source_round_trip)
    } == {
        leaf_id: [entry.id for entry in path_to_entry(target_round_trip, leaf_id)]
        for leaf_id in branch_leaf_ids(target_round_trip)
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
