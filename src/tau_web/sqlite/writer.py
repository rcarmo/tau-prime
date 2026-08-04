"""Bounded single-writer service for Tau's SQLite store."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from enum import IntEnum
from itertools import count
from typing import TypeVar, cast

import aiosqlite
from aiosqlite import Row

T = TypeVar("T")
SqlParameters = Sequence[object]
WriteOperation = Callable[["SqliteTransaction"], Awaitable[object]]


class WritePriority(IntEnum):
    """Lower values run first while preserving FIFO order within a priority."""

    FINALISE = 0
    NORMAL = 10
    BACKGROUND = 20
    STOP = 100


class WriterClosedError(RuntimeError):
    """Raised when a mutation is submitted after shutdown starts."""


class SqliteTransaction:
    """Restricted transaction surface exposed to repositories."""

    def __init__(self, connection: aiosqlite.Connection) -> None:
        self._connection = connection

    async def execute(self, sql: str, parameters: SqlParameters = ()) -> int:
        cursor = await self._connection.execute(sql, parameters)
        try:
            return cursor.rowcount
        finally:
            await cursor.close()

    async def execute_insert(self, sql: str, parameters: SqlParameters = ()) -> int:
        cursor = await self._connection.execute(sql, parameters)
        try:
            if cursor.lastrowid is None:
                raise RuntimeError("SQLite insert did not return a row id")
            return cursor.lastrowid
        finally:
            await cursor.close()

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


@dataclass(slots=True)
class _WriteRequest:
    operation: WriteOperation | None
    future: asyncio.Future[object] | None


class SqliteWriter:
    """Serialise mutations through one connection and a bounded priority queue."""

    def __init__(self, connection: aiosqlite.Connection, *, queue_size: int = 256) -> None:
        if queue_size <= 0:
            raise ValueError("Writer queue size must be positive")
        self._connection = connection
        self._queue: asyncio.PriorityQueue[tuple[int, int, _WriteRequest]] = (
            asyncio.PriorityQueue(maxsize=queue_size)
        )
        self._sequence = count()
        self._task: asyncio.Task[None] | None = None
        self._accepting = True

    @property
    def accepting(self) -> bool:
        return self._accepting

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run(), name="tau-sqlite-writer")

    async def transaction(
        self,
        operation: Callable[[SqliteTransaction], Awaitable[T]],
        *,
        priority: WritePriority = WritePriority.NORMAL,
    ) -> T:
        """Run one repository operation atomically on the writer connection."""
        if not self._accepting:
            raise WriterClosedError("SQLite writer is shutting down")
        self.start()
        loop = asyncio.get_running_loop()
        future: asyncio.Future[object] = loop.create_future()

        async def erased(transaction: SqliteTransaction) -> object:
            return await operation(transaction)

        request = _WriteRequest(operation=erased, future=future)
        await self._queue.put((int(priority), next(self._sequence), request))
        return cast(T, await future)

    async def drain(self) -> None:
        """Wait until all accepted mutations have completed."""
        await self._queue.join()

    async def close(self) -> None:
        """Reject new work, drain accepted writes, and stop the worker."""
        if not self._accepting:
            if self._task is not None:
                await self._task
            return
        self._accepting = False
        if self._task is None:
            return
        await self._queue.join()
        request = _WriteRequest(operation=None, future=None)
        await self._queue.put((int(WritePriority.STOP), next(self._sequence), request))
        await self._task

    async def _run(self) -> None:
        transaction = SqliteTransaction(self._connection)
        while True:
            _, _, request = await self._queue.get()
            try:
                if request.operation is None:
                    return
                await self._connection.execute("BEGIN IMMEDIATE")
                try:
                    result = await request.operation(transaction)
                except BaseException:
                    await self._connection.rollback()
                    raise
                else:
                    await self._connection.commit()
                if request.future is not None and not request.future.done():
                    request.future.set_result(result)
            except BaseException as exc:
                if request.future is not None and not request.future.done():
                    request.future.set_exception(exc)
            finally:
                self._queue.task_done()
