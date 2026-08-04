from __future__ import annotations

from pathlib import Path

import pytest

from tau_agent import UserMessage
from tau_agent.session import (
    CompactionEntry,
    CustomEntry,
    LeafEntry,
    MessageEntry,
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
        entries = [info, user, compaction, custom, leaf]

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
