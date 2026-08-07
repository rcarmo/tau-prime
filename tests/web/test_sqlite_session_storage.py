from __future__ import annotations

from pathlib import Path

import pytest

from tau_agent import AssistantMessage, ToolCall, ToolResultMessage, UserMessage
from tau_agent.session import (
    CompactionEntry,
    CustomEntry,
    LeafEntry,
    MessageEntry,
    SessionEntry,
    SessionInfoEntry,
)
from tau_web.sqlite.connection import SqliteDatabase, SqliteReader
from tau_web.sqlite.session_storage import SqliteSessionStorage, SqliteSessionStorageError
from tau_web.sqlite.writer import SqliteTransaction


async def _seed_session(database: SqliteDatabase, session_id: str = "session") -> None:
    async def seed(transaction: SqliteTransaction) -> None:
        await transaction.execute(
            """
            INSERT INTO workspaces(workspace_id, root_path, created_at, updated_at)
            VALUES ('workspace', '/workspace', 'now', 'now')
            """
        )
        await transaction.execute(
            """
            INSERT INTO sessions(
                session_id, workspace_id, agent_name, provider_name, model,
                created_at, updated_at
            ) VALUES (?, 'workspace', 'default', 'test', 'model', 'now', 'now')
            """,
            (session_id,),
        )

    await database.write(seed)


@pytest.mark.anyio
async def test_session_storage_round_trips_entries_and_leaf(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        await _seed_session(database)
        storage = SqliteSessionStorage(database, "session")
        info = SessionInfoEntry(id="info", cwd="/workspace", title="Test")
        user = MessageEntry(
            id="user",
            parent_id="info",
            message=UserMessage(content="Hello"),
        )
        compaction = CompactionEntry(
            id="compact",
            parent_id="user",
            summary="Summary",
            replaces_entry_ids=["user"],
            details={"source": "test"},
        )
        custom = CustomEntry(
            id="custom",
            parent_id="compact",
            namespace="test.extension",
            data={"preserved": True},
        )
        leaf = LeafEntry(id="leaf", parent_id="custom", entry_id="custom")
        entries: list[SessionEntry] = [info, user, compaction, custom, leaf]

        await storage.append_many(entries)

        assert await storage.read_all() == entries
        assert await storage.read_path("custom") == entries[:-1]

        async def active_leaf(reader: SqliteReader) -> str | None:
            row = await reader.fetch_one(
                "SELECT active_leaf_entry_id FROM sessions WHERE session_id = 'session'"
            )
            assert row is not None
            return str(row[0]) if row[0] is not None else None

        assert await database.read(active_leaf) == "custom"


@pytest.mark.anyio
async def test_session_storage_preserves_foreign_tool_call_ids(tmp_path: Path) -> None:
    foreign_id = "call_123|fc_opaque/provider"
    assistant = MessageEntry(
        id="assistant",
        message=AssistantMessage(
            tool_calls=[ToolCall(id=foreign_id, name="read", arguments={"path": "README.md"})]
        ),
    )
    result = MessageEntry(
        id="result",
        parent_id="assistant",
        message=ToolResultMessage(
            tool_call_id=foreign_id,
            name="read",
            content="contents",
            ok=True,
        ),
    )

    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        await _seed_session(database)
        storage = SqliteSessionStorage(database, "session")
        await storage.append_many([assistant, result])

        restored = await storage.read_all()

    assert restored == [assistant, result]
    restored_assistant = restored[0]
    restored_result = restored[1]
    assert isinstance(restored_assistant, MessageEntry)
    assert isinstance(restored_assistant.message, AssistantMessage)
    assert restored_assistant.message.tool_calls[0].id == foreign_id
    assert isinstance(restored_result, MessageEntry)
    assert isinstance(restored_result.message, ToolResultMessage)
    assert restored_result.message.tool_call_id == foreign_id


@pytest.mark.anyio
async def test_session_storage_append_conforms_to_protocol(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        await _seed_session(database)
        storage = SqliteSessionStorage(database, "session")
        entry = SessionInfoEntry(id="info", cwd="/workspace")

        await storage.append(entry)

        assert await storage.read_all() == [entry]


@pytest.mark.anyio
async def test_session_storage_batch_rolls_back_on_bad_parent(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        await _seed_session(database)
        storage = SqliteSessionStorage(database, "session")
        first = SessionInfoEntry(id="info")
        invalid = MessageEntry(
            id="message",
            parent_id="missing",
            message=UserMessage(content="bad"),
        )

        with pytest.raises(SqliteSessionStorageError, match="does not exist"):
            await storage.append_many([first, invalid])

        assert await storage.read_all() == []


@pytest.mark.anyio
async def test_session_storage_rejects_cross_session_parent(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        await _seed_session(database, "first")

        async def second_session(transaction: SqliteTransaction) -> None:
            await transaction.execute(
                """
                INSERT INTO sessions(
                    session_id, workspace_id, agent_name, provider_name, model,
                    created_at, updated_at
                ) VALUES ('second', 'workspace', 'other', 'test', 'model', 'now', 'now')
                """
            )

        await database.write(second_session)
        first = SqliteSessionStorage(database, "first")
        second = SqliteSessionStorage(database, "second")
        await first.append(SessionInfoEntry(id="first-root"))

        with pytest.raises(SqliteSessionStorageError, match="another session"):
            await second.append(
                MessageEntry(
                    id="second-message",
                    parent_id="first-root",
                    message=UserMessage(content="bad edge"),
                )
            )


@pytest.mark.anyio
async def test_session_storage_detects_column_payload_mismatch(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        await _seed_session(database)
        storage = SqliteSessionStorage(database, "session")
        await storage.append(SessionInfoEntry(id="info"))

        async def corrupt(transaction: SqliteTransaction) -> None:
            await transaction.execute(
                "UPDATE session_entries SET entry_type = 'message' WHERE entry_id = 'info'"
            )

        await database.write(corrupt)

        with pytest.raises(SqliteSessionStorageError, match="disagree"):
            await storage.read_all()


@pytest.mark.anyio
async def test_coding_session_load_persists_interrupted_tail_tool_repair_once_in_sqlite(
    tmp_path: Path,
) -> None:
    from tau_agent import AssistantMessage, ToolCall, ToolResultMessage, UserMessage
    from tau_agent.session import LeafEntry, MessageEntry
    from tau_ai import FakeProvider, ProviderResponseEndEvent, ProviderResponseStartEvent
    from tau_coding import CodingSession, CodingSessionConfig
    from tau_web.sqlite.sessions import SessionRepository

    database_path = tmp_path / "tau.sqlite3"
    session_id = "worker-1"
    user_entry = MessageEntry(
        id="user",
        message=UserMessage(content="Read README.md"),
    )
    tool_call = ToolCall(id="call-1", name="read", arguments={"path": "README.md"})
    assistant_entry = MessageEntry(
        id="assistant",
        parent_id=user_entry.id,
        message=AssistantMessage(content="I'll read it.", tool_calls=[tool_call]),
    )
    expected_repair = ToolResultMessage(
        tool_call_id="call-1",
        name="read",
        content="Tool call interrupted by user",
        ok=False,
        error="Tool call interrupted by user",
    )
    expected_messages = (
        user_entry.message,
        assistant_entry.message,
        expected_repair,
    )

    async with SqliteDatabase(database_path) as database:
        record = await SessionRepository(database).create(
            workspace_root=tmp_path,
            provider_name="test",
            model="fake",
            agent_name=session_id,
            session_id=session_id,
        )
        storage = SqliteSessionStorage(database, record.session_id)
        await storage.append(user_entry)
        await storage.append(assistant_entry)
        await storage.append(
            LeafEntry(
                id="assistant-leaf",
                parent_id=assistant_entry.id,
                entry_id=assistant_entry.id,
            )
        )

        provider = FakeProvider(
            [
                [
                    ProviderResponseStartEvent(model="fake"),
                    ProviderResponseEndEvent(message=AssistantMessage(content="Recovered.")),
                ]
            ]
        )
        session = await CodingSession.load(
            CodingSessionConfig(
                provider=provider,
                model="fake",
                system="You are Tau.",
                storage=storage,
                cwd=tmp_path,
            )
        )

        assert provider.calls == []
        assert session.messages == expected_messages

        repaired_entries = await SqliteSessionStorage(database, record.session_id).read_all()
        message_entries = [entry for entry in repaired_entries if entry.type == "message"]
        leaf_entries = [entry for entry in repaired_entries if entry.type == "leaf"]
        assert [entry.message for entry in message_entries] == list(expected_messages)
        assert len(repaired_entries) == 5
        assert len(leaf_entries) == 2
        assert leaf_entries[-1].entry_id == message_entries[-1].id

    async with SqliteDatabase(database_path) as database:
        fresh_storage = SqliteSessionStorage(database, session_id)

        assert await fresh_storage.read_all() == repaired_entries

        restored = await CodingSession.load(
            CodingSessionConfig(
                provider=FakeProvider([]),
                model="fake",
                system="You are Tau.",
                storage=fresh_storage,
                cwd=tmp_path,
            )
        )

        assert restored.messages == expected_messages
        assert await fresh_storage.read_all() == repaired_entries
