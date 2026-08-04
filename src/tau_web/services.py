"""Service wiring and lifecycle management for Tau Web."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Self

from tau_coding.agent_pool import AsyncAgentPool
from tau_web.chat_routing import ChatRouter
from tau_web.config import WebConfig
from tau_web.events import EventProjector
from tau_web.runtime import DurableAgentRuntime
from tau_web.sqlite.connection import SqliteDatabase
from tau_web.sqlite.repositories import (
    AuditRepository,
    DeliveryRepository,
    MediaRepository,
    PlanRepository,
    QueueRepository,
    RunRepository,
    SearchRepository,
    TimelineMessageRepository,
    UsageRepository,
)
from tau_web.sqlite.session_storage import SqliteSessionStorage
from tau_web.sqlite.sessions import SessionRepository


@dataclass(slots=True)
class TauWebServices:
    """Own the core Tau Web services behind one SQLite database."""

    config: WebConfig
    database: SqliteDatabase
    sessions: SessionRepository
    runs: RunRepository
    queues: QueueRepository
    deliveries: DeliveryRepository
    audit: AuditRepository
    media: MediaRepository
    plans: PlanRepository
    usage: UsageRepository
    fts: SearchRepository
    timeline: TimelineMessageRepository
    projector: EventProjector
    pool: AsyncAgentPool
    runtime: DurableAgentRuntime
    router: ChatRouter
    closed: bool = False
    _close_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)

    @classmethod
    async def open(cls, config: WebConfig) -> Self:
        """Open the durable database and assemble the Tau Web service graph."""
        database_path = config.database_path
        if database_path is None:
            raise ValueError("WebConfig.database_path must not be None")

        database = SqliteDatabase(database_path)
        pool: AsyncAgentPool | None = None
        runtime: DurableAgentRuntime | None = None
        try:
            await database.open()
            sessions = SessionRepository(database)
            runs = RunRepository(database)
            queues = QueueRepository(database)
            deliveries = DeliveryRepository(database)
            audit = AuditRepository(database)
            media = MediaRepository(database)
            plans = PlanRepository(database)
            usage = UsageRepository(database)
            fts = SearchRepository(database)
            timeline = TimelineMessageRepository(database)
            projector = EventProjector(timeline)
            pool = AsyncAgentPool(max_concurrency=config.max_active_runs)
            runtime = DurableAgentRuntime(
                pool,
                runs,
                queues,
                audit,
                event_projector=projector.project,
            )
            router = ChatRouter(sessions, deliveries, runtime, pool)
            return cls(
                config=config,
                database=database,
                sessions=sessions,
                runs=runs,
                queues=queues,
                deliveries=deliveries,
                audit=audit,
                media=media,
                plans=plans,
                usage=usage,
                fts=fts,
                timeline=timeline,
                projector=projector,
                pool=pool,
                runtime=runtime,
                router=router,
            )
        except BaseException:
            with suppress(BaseException):
                if runtime is not None:
                    await runtime.shutdown()
                elif pool is not None:
                    await pool.shutdown()
            with suppress(BaseException):
                await database.close()
            raise

    def session_storage(self, session_id: str) -> SqliteSessionStorage:
        """Return append-only entry storage bound to one durable session."""
        return SqliteSessionStorage(self.database, session_id)

    async def close(self) -> None:
        """Shut down runtime, receipt tasks, and database resources."""
        async with self._close_lock:
            if self.closed:
                return

            cleanup_failed = False
            first_error: BaseException | None = None

            try:
                await self.runtime.shutdown()
            except BaseException as exc:
                cleanup_failed = True
                first_error = exc

            try:
                receipt_errors = await self.router.shutdown_receipts(cancel=True, timeout=1)
            except BaseException as exc:
                cleanup_failed = True
                if first_error is None:
                    first_error = exc
            else:
                if first_error is None and receipt_errors:
                    first_error = receipt_errors[0]

            try:
                await self.database.close()
            except BaseException as exc:
                cleanup_failed = True
                if first_error is None:
                    first_error = exc

            if not cleanup_failed:
                self.closed = True
            if first_error is not None:
                raise first_error
