from __future__ import annotations

import asyncio
import json
import sqlite3
import stat
from pathlib import Path

import pytest

from tau_agent import UserMessage
from tau_agent.session import LeafEntry, MessageEntry, SessionInfoEntry
from tau_agent.session.jsonl import entry_to_json_line
from tau_web.sqlite.connection import SqliteDatabase, SqliteReader
from tau_web.sqlite.migrations import LATEST_SCHEMA_VERSION, MIGRATIONS
from tau_web.sqlite.process_lock import DatabaseLockedError, DatabaseProcessLock
from tau_web.sqlite.writer import SqliteTransaction, WriterClosedError

_FIXTURE_SESSION_ID = "upgrade-session"
_FIXTURE_QUEUE_ID = "upgrade-queue"
_FIXTURE_RUN_ID = "upgrade-run"


def _fixture_source_schema_version() -> int:
    if LATEST_SCHEMA_VERSION <= 1:
        return LATEST_SCHEMA_VERSION
    return LATEST_SCHEMA_VERSION - 1


def _fixture_entries() -> list[SessionInfoEntry | MessageEntry | LeafEntry]:
    info = SessionInfoEntry(
        id="upgrade-info",
        timestamp=1.0,
        created_at=1.0,
        cwd="/workspace",
        title="Upgrade fixture",
    )
    message = MessageEntry(
        id="upgrade-message",
        parent_id=info.id,
        timestamp=2.0,
        message=UserMessage(content="preserve seeded transcript"),
    )
    leaf = LeafEntry(
        id="upgrade-leaf",
        parent_id=message.id,
        timestamp=3.0,
        entry_id=message.id,
    )
    return [info, message, leaf]


def _build_migrated_fixture(
    path: Path, *, schema_version: int
) -> list[SessionInfoEntry | MessageEntry | LeafEntry]:
    entries = _fixture_entries()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        for migration in MIGRATIONS:
            if migration.version > schema_version:
                break
            connection.executescript(migration.sql)
            connection.execute(
                "INSERT INTO schema_migrations(version, name, applied_at) VALUES (?, ?, ?)",
                (migration.version, migration.name, "2026-08-05T00:00:00Z"),
            )
            connection.execute(f"PRAGMA user_version = {migration.version}")

        connection.execute(
            """
            INSERT INTO workspaces(workspace_id, root_path, created_at, updated_at)
            VALUES ('upgrade-workspace', '/workspace', 'now', 'now')
            """
        )
        connection.execute(
            """
            INSERT INTO sessions(
                session_id, workspace_id, agent_name, provider_name, model,
                created_at, updated_at
            ) VALUES (?, 'upgrade-workspace', 'upgrade', 'test', 'model', 'now', 'now')
            """,
            (_FIXTURE_SESSION_ID,),
        )
        for ordinal, entry in enumerate(entries):
            connection.execute(
                """
                INSERT INTO session_entries(
                    entry_id, session_id, parent_entry_id, entry_type,
                    timestamp, ordinal, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.id,
                    _FIXTURE_SESSION_ID,
                    entry.parent_id,
                    entry.type,
                    entry.timestamp,
                    ordinal,
                    entry_to_json_line(entry).strip(),
                ),
            )
        connection.execute(
            "UPDATE sessions SET active_leaf_entry_id = ? WHERE session_id = ?",
            (entries[1].id, _FIXTURE_SESSION_ID),
        )
        connection.execute(
            """
            INSERT INTO queued_messages(
                queue_id, session_id, queue_kind, position, content_json, created_at
            ) VALUES (?, ?, 'follow_up', 0, ?, 'now')
            """,
            (_FIXTURE_QUEUE_ID, _FIXTURE_SESSION_ID, json.dumps("preserve queued state")),
        )
        connection.execute(
            """
            INSERT INTO session_runs(
                run_id, session_id, status, started_at, updated_at
            ) VALUES (?, ?, 'pending', 'now', 'now')
            """,
            (_FIXTURE_RUN_ID, _FIXTURE_SESSION_ID),
        )
        connection.commit()
    finally:
        connection.close()
    return entries


def test_database_process_lock_is_exclusive(tmp_path: Path) -> None:
    database_path = tmp_path / "tau.sqlite3"
    first = DatabaseProcessLock(database_path)
    second = DatabaseProcessLock(database_path)

    first.acquire()
    try:
        assert first.acquired
        with pytest.raises(DatabaseLockedError):
            second.acquire()
    finally:
        first.release()

    second.acquire()
    second.release()


@pytest.mark.anyio
async def test_database_open_applies_migrations_and_pragmas(tmp_path: Path) -> None:
    database_path = tmp_path / "private" / "tau.sqlite3"

    async with SqliteDatabase(database_path, read_pool_size=2) as database:
        assert database.opened

        async def inspect(reader: SqliteReader) -> tuple[int, int, int, str]:
            version = await reader.fetch_one("PRAGMA user_version")
            foreign_keys = await reader.fetch_one("PRAGMA foreign_keys")
            query_only = await reader.fetch_one("PRAGMA query_only")
            journal_mode = await reader.fetch_one("PRAGMA journal_mode")
            assert version is not None
            assert foreign_keys is not None
            assert query_only is not None
            assert journal_mode is not None
            return (
                int(version[0]),
                int(foreign_keys[0]),
                int(query_only[0]),
                str(journal_mode[0]).lower(),
            )

        assert await database.read(inspect) == (LATEST_SCHEMA_VERSION, 1, 1, "wal")

    assert stat.S_IMODE(database_path.stat().st_mode) == 0o600
    assert not database.opened


@pytest.mark.anyio
async def test_database_reopen_is_idempotent(tmp_path: Path) -> None:
    database_path = tmp_path / "tau.sqlite3"

    async with SqliteDatabase(database_path):
        pass
    async with SqliteDatabase(database_path) as database:
        async def migration_count(reader: SqliteReader) -> int:
            row = await reader.fetch_one("SELECT count(*) FROM schema_migrations")
            assert row is not None
            return int(row[0])

        assert await database.read(migration_count) == len(range(1, LATEST_SCHEMA_VERSION + 1))


@pytest.mark.anyio
async def test_writer_commits_and_rolls_back_atomically(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        async def create_workspace(transaction: SqliteTransaction) -> None:
            await transaction.execute(
                """
                INSERT INTO workspaces(workspace_id, root_path, created_at, updated_at)
                VALUES ('one', '/one', 'now', 'now')
                """
            )

        await database.write(create_workspace)

        async def fail_after_insert(transaction: SqliteTransaction) -> None:
            await transaction.execute(
                """
                INSERT INTO workspaces(workspace_id, root_path, created_at, updated_at)
                VALUES ('two', '/two', 'now', 'now')
                """
            )
            raise RuntimeError("stop")

        with pytest.raises(RuntimeError, match="stop"):
            await database.write(fail_after_insert)

        async def workspace_ids(reader: SqliteReader) -> list[str]:
            rows = await reader.fetch_all(
                "SELECT workspace_id FROM workspaces ORDER BY workspace_id"
            )
            return [str(row[0]) for row in rows]

        assert await database.read(workspace_ids) == ["one"]


@pytest.mark.anyio
async def test_writer_serialises_concurrent_transactions(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        active = 0
        peak = 0
        completed: list[int] = []

        async def submit(value: int) -> None:
            async def operation(_: SqliteTransaction) -> None:
                nonlocal active, peak
                active += 1
                peak = max(peak, active)
                await asyncio.sleep(0.005)
                completed.append(value)
                active -= 1

            await database.write(operation)

        await asyncio.gather(*(submit(value) for value in range(8)))

        assert peak == 1
        assert completed == list(range(8))


@pytest.mark.anyio
async def test_database_lock_rejects_second_open_instance(tmp_path: Path) -> None:
    database_path = tmp_path / "tau.sqlite3"
    first = SqliteDatabase(database_path)
    second = SqliteDatabase(database_path)
    await first.open()
    try:
        with pytest.raises(DatabaseLockedError):
            await second.open()
    finally:
        await first.close()
        await second.close()


@pytest.mark.anyio
async def test_database_rejects_writes_after_close(tmp_path: Path) -> None:
    database = SqliteDatabase(tmp_path / "tau.sqlite3")
    await database.open()
    writer = database._require_writer()
    await database.close()

    async def operation(_: SqliteTransaction) -> None:
        return None

    with pytest.raises(WriterClosedError):
        await writer.transaction(operation)


@pytest.mark.anyio
async def test_integrity_check_and_checkpoint(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        assert await database.integrity_check() == ("ok",)
        checkpoint = await database.checkpoint()

        assert checkpoint.busy == 0
        assert checkpoint.log_frames >= 0
        assert checkpoint.checkpointed_frames >= 0


@pytest.mark.anyio
async def test_startup_marks_running_runs_interrupted(tmp_path: Path) -> None:
    database_path = tmp_path / "tau.sqlite3"
    async with SqliteDatabase(database_path) as database:
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
                ) VALUES ('session', 'workspace', 'default', 'test', 'model', 'now', 'now')
                """
            )
            await transaction.execute(
                """
                INSERT INTO session_runs(
                    run_id, session_id, status, started_at, updated_at
                ) VALUES ('run', 'session', 'running', 'now', 'now')
                """
            )

        await database.write(seed)

    async with SqliteDatabase(database_path) as database:
        assert database.recovered_run_count == 1

        async def inspect(reader: SqliteReader) -> tuple[str, bool, bool]:
            row = await reader.fetch_one(
                "SELECT status, ended_at, error_json FROM session_runs WHERE run_id = 'run'"
            )
            assert row is not None
            return str(row[0]), row[1] is not None, row[2] is not None

        assert await database.read(inspect) == ("interrupted", True, True)
