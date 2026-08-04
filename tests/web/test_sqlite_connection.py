from __future__ import annotations

import asyncio
import stat
from pathlib import Path

import pytest

from tau_web.sqlite.connection import SqliteDatabase, SqliteReader
from tau_web.sqlite.migrations import LATEST_SCHEMA_VERSION
from tau_web.sqlite.process_lock import DatabaseLockedError, DatabaseProcessLock
from tau_web.sqlite.writer import SqliteTransaction, WriterClosedError


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

        async def inspect(reader: SqliteReader) -> tuple[int, int, int]:
            version = await reader.fetch_one("PRAGMA user_version")
            foreign_keys = await reader.fetch_one("PRAGMA foreign_keys")
            query_only = await reader.fetch_one("PRAGMA query_only")
            assert version is not None
            assert foreign_keys is not None
            assert query_only is not None
            return int(version[0]), int(foreign_keys[0]), int(query_only[0])

        assert await database.read(inspect) == (LATEST_SCHEMA_VERSION, 1, 1)

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
