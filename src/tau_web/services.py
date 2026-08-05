"""Service wiring and lifecycle management for Tau Web."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Self

from tau_agent import AgentTool
from tau_coding.agent_pool import AsyncAgentPool
from tau_web.approvals import ToolApprovalManager
from tau_web.baseline_extensions.meters import HostMetersSampler
from tau_web.baseline_extensions.session_dashboard import (
    DASHBOARD_EVENT_TYPE,
    SessionDashboard,
)
from tau_web.chat_routing import ChatRouter
from tau_web.config import WebConfig
from tau_web.events import EventProjector, WebEventEnvelope, build_invalidation_envelope
from tau_web.extensions import ExtensionDirectory, SqliteExtensionStorageBackend
from tau_web.media_tools import create_attachment_tool
from tau_web.runtime import DurableAgentRuntime
from tau_web.sqlite.connection import SqliteDatabase
from tau_web.sqlite.repositories import (
    AuditRepository,
    DeliveryRepository,
    ExtensionStateRepository,
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
from tau_web.sse import GLOBAL_EVENT_SESSION_ID, EventBroker


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
    extension_state: ExtensionStateRepository
    extension_storage: SqliteExtensionStorageBackend
    extensions: ExtensionDirectory
    projector: EventProjector
    broker: EventBroker
    meters: HostMetersSampler
    dashboard: SessionDashboard
    approvals: ToolApprovalManager
    pool: AsyncAgentPool
    runtime: DurableAgentRuntime
    router: ChatRouter
    _unsubscribe: Callable[[], None] = field(repr=False)
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
        broker: EventBroker | None = None
        meters: HostMetersSampler | None = None
        unsubscribe: Callable[[], None] | None = None
        try:
            await database.open()
            sessions = SessionRepository(database)
            runs = RunRepository(database)
            queues = QueueRepository(database)
            deliveries = DeliveryRepository(database)
            audit = AuditRepository(database)
            media = MediaRepository(database)
            media_cutoff = datetime.now(UTC) - timedelta(days=config.media_retention_days)
            await media.purge_deleted_before(media_cutoff.isoformat())
            plans = PlanRepository(database)
            usage = UsageRepository(database)
            fts = SearchRepository(database)
            timeline = TimelineMessageRepository(database)
            extension_state = ExtensionStateRepository(database)
            extension_storage = SqliteExtensionStorageBackend(extension_state)
            extensions = ExtensionDirectory()
            projector = EventProjector(timeline)
            broker = EventBroker(
                replay_capacity=config.sse_replay_capacity,
                subscriber_capacity=config.sse_client_capacity,
            )
            meters = HostMetersSampler(broker=broker)
            await meters.open()
            approvals = ToolApprovalManager(
                audit,
                broker,
                timeout_seconds=config.tool_approval_timeout_seconds,
            )
            pool = AsyncAgentPool(max_concurrency=config.max_active_runs)
            dashboard = SessionDashboard(
                sessions=sessions,
                runs=runs,
                queues=queues,
                timeline=timeline,
                pool=pool,
                storage_for=lambda session_id: SqliteSessionStorage(database, session_id),
            )

            async def publish_event(envelope: WebEventEnvelope) -> None:
                dashboard_changed = await dashboard.observe(envelope)
                await broker.publish(envelope)
                if dashboard_changed:
                    await broker.publish(
                        build_invalidation_envelope(
                            event_type=DASHBOARD_EVENT_TYPE,
                            session_id=GLOBAL_EVENT_SESSION_ID,
                            payload={"updated_session_id": envelope.session_id},
                        )
                    )

            unsubscribe = projector.subscribe(publish_event)
            runtime = DurableAgentRuntime(
                pool,
                runs,
                queues,
                audit,
                event_projector=projector.project,
                media=media,
                approvals=approvals,
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
                extension_state=extension_state,
                extension_storage=extension_storage,
                extensions=extensions,
                projector=projector,
                broker=broker,
                meters=meters,
                dashboard=dashboard,
                approvals=approvals,
                pool=pool,
                runtime=runtime,
                router=router,
                _unsubscribe=unsubscribe,
            )
        except BaseException:
            with suppress(BaseException):
                if runtime is not None:
                    await runtime.shutdown()
                elif pool is not None:
                    await pool.shutdown()
            with suppress(BaseException):
                if unsubscribe is not None:
                    unsubscribe()
            with suppress(BaseException):
                if meters is not None:
                    await meters.close()
            with suppress(BaseException):
                if broker is not None:
                    broker.close()
            with suppress(BaseException):
                await database.close()
            raise

    def session_storage(self, session_id: str) -> SqliteSessionStorage:
        """Return append-only entry storage bound to one durable session."""
        return SqliteSessionStorage(self.database, session_id)

    def attachment_tool(self, session_id: str) -> AgentTool:
        """Return the session-confined uploaded-attachment tool."""
        return create_attachment_tool(self.media, session_id)

    async def close(self) -> None:
        """Shut down runtime, receipt tasks, and database resources."""
        async with self._close_lock:
            if self.closed:
                return

            cleanup_failed = False
            first_error: BaseException | None = None

            try:
                await self.meters.close()
            except BaseException as exc:
                cleanup_failed = True
                first_error = exc

            try:
                await self.approvals.shutdown()
            except BaseException as exc:
                cleanup_failed = True
                if first_error is None:
                    first_error = exc

            try:
                await self.runtime.shutdown()
            except BaseException as exc:
                cleanup_failed = True
                if first_error is None:
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
                await self.extensions.dispose()
            except BaseException as exc:
                cleanup_failed = True
                if first_error is None:
                    first_error = exc

            try:
                self._unsubscribe()
            except BaseException as exc:
                cleanup_failed = True
                if first_error is None:
                    first_error = exc

            try:
                self.broker.close()
            except BaseException as exc:
                cleanup_failed = True
                if first_error is None:
                    first_error = exc

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
