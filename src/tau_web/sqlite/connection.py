"""Connection lifecycle, migrations, and read pooling for Tau SQLite."""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Awaitable, Callable, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

import aiosqlite
from aiosqlite import Row

from tau_web.sqlite.migrations import LATEST_SCHEMA_VERSION, pending_migrations
from tau_web.sqlite.process_lock import DatabaseProcessLock
from tau_web.sqlite.writer import SqliteTransaction, SqliteWriter, WritePriority

T = TypeVar("T")
ReadOperation = Callable[["SqliteReader"], Awaitable[T]]
SqlParameters = Sequence[object]

_BUSY_TIMEOUT_MILLISECONDS = 5_000


@dataclass(frozen=True, slots=True)
class CheckpointResult:
    """Result counters returned by SQLite's WAL checkpoint pragma."""

    busy: int
    log_frames: int
    checkpointed_frames: int


class DatabaseIntegrityError(RuntimeError):
    """Raised when SQLite reports corruption during startup validation."""


class SqliteReader:
    """Read-only query surface exposed to repositories."""

    def __init__(self, connection: aiosqlite.Connection) -> None:
        self._connection = connection

    async def fetch_one(self, sql: str, parameters: SqlParameters = ()) -> Row | None:
        cursor = await self._connection.execute(sql, parameters)
        try:
            return await cursor.fetchone()
        finally:
            await cursor.close()

    async def fetch_all(self, sql: str, parameters: SqlParameters = ()) -> list[Row]:
        cursor = await self._connection.execute(sql, parameters)
        try:
            return list(await cursor.fetchall())
        finally:
            await cursor.close()


class SqliteDatabase:
    """Own the process lock, write service, and bounded read connection pool."""

    def __init__(
        self,
        path: Path,
        *,
        read_pool_size: int = 4,
        writer_queue_size: int = 256,
    ) -> None:
        if read_pool_size <= 0:
            raise ValueError("Read pool size must be positive")
        self.path = path.expanduser().resolve()
        self._read_pool_size = read_pool_size
        self._writer_queue_size = writer_queue_size
        self._lock = DatabaseProcessLock(self.path)
        self._write_connection: aiosqlite.Connection | None = None
        self._writer: SqliteWriter | None = None
        self._read_pool: asyncio.Queue[aiosqlite.Connection] = asyncio.Queue(
            maxsize=read_pool_size
        )
        self._opened = False
        self.recovered_run_count = 0

    @property
    def opened(self) -> bool:
        return self._opened

    async def open(self) -> None:
        if self._opened:
            return
        await asyncio.to_thread(self._lock.acquire)
        try:
            self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            connection = await aiosqlite.connect(self.path)
            connection.row_factory = aiosqlite.Row
            self._write_connection = connection
            await _configure_write_connection(connection)
            await _apply_migrations(connection)
            await _validate_integrity(connection)
            self.recovered_run_count = await _recover_stale_runs(connection)
            _secure_database_files(self.path)

            self._writer = SqliteWriter(connection, queue_size=self._writer_queue_size)
            self._writer.start()
            for _ in range(self._read_pool_size):
                await self._read_pool.put(await _open_read_connection(self.path))
            self._opened = True
        except BaseException:
            await self._close_connections()
            await asyncio.to_thread(self._lock.release)
            raise

    async def write(
        self,
        operation: Callable[[SqliteTransaction], Awaitable[T]],
        *,
        priority: WritePriority = WritePriority.NORMAL,
    ) -> T:
        writer = self._require_writer()
        return await writer.transaction(operation, priority=priority)

    async def read(self, operation: ReadOperation[T]) -> T:
        if not self._opened:
            raise RuntimeError("SQLite database is not open")
        connection = await self._read_pool.get()
        try:
            return await operation(SqliteReader(connection))
        finally:
            self._read_pool.put_nowait(connection)

    async def integrity_check(self) -> tuple[str, ...]:
        """Return SQLite quick-check diagnostics (``("ok",)`` for a healthy store)."""

        async def inspect(reader: SqliteReader) -> tuple[str, ...]:
            rows = await reader.fetch_all("PRAGMA quick_check")
            return tuple(str(row[0]) for row in rows)

        return await self.read(inspect)

    async def checkpoint(self) -> CheckpointResult:
        """Request a passive WAL checkpoint behind already accepted writes."""
        writer = self._require_writer()

        async def run(transaction: SqliteTransaction) -> CheckpointResult:
            row = await transaction.fetch_one("PRAGMA wal_checkpoint(PASSIVE)")
            if row is None:
                raise RuntimeError("SQLite did not return checkpoint counters")
            return CheckpointResult(int(row[0]), int(row[1]), int(row[2]))

        return await writer.maintenance(run)

    async def close(self) -> None:
        if not self._opened and self._write_connection is None:
            await asyncio.to_thread(self._lock.release)
            return
        self._opened = False
        writer = self._writer
        self._writer = None
        if writer is not None:
            await writer.close()
        if self._write_connection is not None:
            await _checkpoint_connection(self._write_connection)
        await self._close_connections()
        await asyncio.to_thread(self._lock.release)

    async def __aenter__(self) -> SqliteDatabase:
        await self.open()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    def _require_writer(self) -> SqliteWriter:
        if not self._opened or self._writer is None:
            raise RuntimeError("SQLite database is not open")
        return self._writer

    async def _close_connections(self) -> None:
        while not self._read_pool.empty():
            connection = self._read_pool.get_nowait()
            await connection.close()
        if self._write_connection is not None:
            await self._write_connection.close()
            self._write_connection = None


async def _configure_write_connection(connection: aiosqlite.Connection) -> None:
    await _execute_pragma(connection, "PRAGMA journal_mode = WAL")
    await _execute_pragma(connection, "PRAGMA foreign_keys = ON")
    await _execute_pragma(connection, "PRAGMA synchronous = NORMAL")
    await _execute_pragma(connection, f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MILLISECONDS}")
    await _execute_pragma(connection, "PRAGMA temp_store = MEMORY")


async def _open_read_connection(path: Path) -> aiosqlite.Connection:
    connection = await aiosqlite.connect(f"{path.as_uri()}?mode=ro", uri=True)
    connection.row_factory = aiosqlite.Row
    await _execute_pragma(connection, "PRAGMA foreign_keys = ON")
    await _execute_pragma(connection, f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MILLISECONDS}")
    await _execute_pragma(connection, "PRAGMA temp_store = MEMORY")
    await _execute_pragma(connection, "PRAGMA query_only = ON")
    return connection


async def _execute_pragma(connection: aiosqlite.Connection, sql: str) -> None:
    cursor = await connection.execute(sql)
    await cursor.close()


async def _schema_version(connection: aiosqlite.Connection) -> int:
    cursor = await connection.execute("PRAGMA user_version")
    try:
        row = await cursor.fetchone()
    finally:
        await cursor.close()
    return int(row[0]) if row is not None else 0


async def _validate_integrity(connection: aiosqlite.Connection) -> None:
    cursor = await connection.execute("PRAGMA quick_check")
    try:
        diagnostics = tuple(str(row[0]) for row in await cursor.fetchall())
    finally:
        await cursor.close()
    if diagnostics != ("ok",):
        raise DatabaseIntegrityError("SQLite integrity check failed: " + "; ".join(diagnostics))


async def _recover_stale_runs(connection: aiosqlite.Connection) -> int:
    timestamp = datetime.now(UTC).isoformat()
    error_json = json.dumps(
        {"code": "runtime_restarted", "message": "Run interrupted by runtime restart"},
        separators=(",", ":"),
    )
    cursor = await connection.execute(
        """
        UPDATE session_runs
        SET status = 'interrupted', updated_at = ?, ended_at = ?, error_json = ?
        WHERE status = 'running'
        """,
        (timestamp, timestamp, error_json),
    )
    try:
        recovered = cursor.rowcount
    finally:
        await cursor.close()
    await connection.commit()
    return recovered


async def _checkpoint_connection(connection: aiosqlite.Connection) -> CheckpointResult:
    cursor = await connection.execute("PRAGMA wal_checkpoint(PASSIVE)")
    try:
        row = await cursor.fetchone()
    finally:
        await cursor.close()
    if row is None:
        raise RuntimeError("SQLite did not return checkpoint counters")
    return CheckpointResult(int(row[0]), int(row[1]), int(row[2]))


async def _apply_migrations(connection: aiosqlite.Connection) -> None:
    current_version = await _schema_version(connection)
    for migration in pending_migrations(current_version):
        applied_at = datetime.now(UTC).isoformat()
        script = f"""
BEGIN EXCLUSIVE;
{migration.sql}
INSERT INTO schema_migrations(version, name, applied_at)
VALUES ({migration.version}, '{migration.name}', '{applied_at}');
PRAGMA user_version = {migration.version};
COMMIT;
"""
        try:
            await connection.executescript(script)
        except BaseException:
            await connection.rollback()
            raise

    final_version = await _schema_version(connection)
    if final_version != LATEST_SCHEMA_VERSION:
        raise RuntimeError(
            f"SQLite migration ended at schema {final_version}; expected {LATEST_SCHEMA_VERSION}"
        )


_OWNER_ONLY_FILE_MODE = 0o600


def _secure_database_files(path: Path) -> None:
    for candidate in (path, path.with_name(f"{path.name}-wal"), path.with_name(f"{path.name}-shm")):
        with suppress(FileNotFoundError):
            os.chmod(candidate, _OWNER_ONLY_FILE_MODE)
