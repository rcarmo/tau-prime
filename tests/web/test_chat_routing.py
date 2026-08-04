from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from tau_agent import AgentEndEvent, AgentEvent, AgentStartEvent, QueueUpdateEvent
from tau_agent.types import JSONValue
from tau_coding.agent_pool import AsyncAgentPool
from tau_web.chat_routing import ChatRouter, ChatRoutingError
from tau_web.runtime import DurableAgentRuntime
from tau_web.sqlite.connection import SqliteDatabase
from tau_web.sqlite.repositories import (
    AuditRepository,
    DeliveryRepository,
    QueueKind,
    QueueMessageRecord,
    QueueRepository,
    RunRepository,
)
from tau_web.sqlite.sessions import SessionRecord, SessionRepository


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class _FakeSession:
    def __init__(
        self,
        events: tuple[AgentEvent, ...] = (AgentStartEvent(), AgentEndEvent()),
        *,
        release: asyncio.Event | None = None,
    ) -> None:
        self._events = events
        self._release = release
        self._active_run_token: int | None = None
        self._next_run_token = 0
        self.prompt_calls: list[str] = []
        self.prompt_started = asyncio.Event()
        self.queue_message_calls: list[tuple[str, str]] = []
        self.queued_steering: tuple[str, ...] = ()
        self.queued_follow_up: tuple[str, ...] = ()

    def prompt(
        self,
        content: str,
        *,
        streaming_behavior: str | None = None,
    ) -> AsyncIterator[AgentEvent]:
        assert streaming_behavior is None
        self.prompt_calls.append(content)

        async def run() -> AsyncIterator[AgentEvent]:
            self._next_run_token += 1
            active_run_token = self._next_run_token
            self._active_run_token = active_run_token
            self.prompt_started.set()
            try:
                if self._release is not None:
                    await self._release.wait()
                for event in self._events:
                    yield event
            finally:
                if self._active_run_token == active_run_token:
                    self._active_run_token = None

        return run()

    def continue_(self) -> AsyncIterator[AgentEvent]:
        raise AssertionError("continue_() should not be called in chat routing tests")

    async def queue_message(self, content: str, *, behavior: str) -> QueueUpdateEvent:
        active_run_token = self._active_run_token
        if active_run_token is None:
            raise RuntimeError("Session is idle; cannot queue a message.")
        self.queue_message_calls.append((content, behavior))
        if self._active_run_token != active_run_token:
            raise RuntimeError("Session active run changed while queueing a message.")
        if behavior == "steer":
            self.queued_steering = (*self.queued_steering, content)
        elif behavior == "follow_up":
            self.queued_follow_up = (*self.queued_follow_up, content)
        else:
            raise AssertionError(
                "queue_message() should not be called in chat routing tests: "
                f"{behavior=} {content=}"
            )
        return QueueUpdateEvent(
            steering=self.queued_steering,
            follow_up=self.queued_follow_up,
        )

    def cancel(self) -> None:
        return None

    async def aclose(self) -> None:
        return None


class _RecordingRuntime(DurableAgentRuntime):
    def __init__(
        self,
        pool: AsyncAgentPool,
        runs: RunRepository,
        queues: QueueRepository,
        audit: AuditRepository,
    ) -> None:
        super().__init__(pool, runs, queues, audit)
        self.enqueue_calls: list[tuple[str, JSONValue, QueueKind, str | None]] = []
        self.steer_calls: list[tuple[str, str, str | None]] = []

    async def enqueue(
        self,
        session_id: str,
        content: JSONValue,
        queue_kind: QueueKind = "follow_up",
        source_session_id: str | None = None,
    ) -> QueueMessageRecord:
        self.enqueue_calls.append((session_id, content, queue_kind, source_session_id))
        return await super().enqueue(
            session_id,
            content,
            queue_kind=queue_kind,
            source_session_id=source_session_id,
        )

    async def steer(
        self,
        run_id: str,
        content: str,
        source_session_id: str | None = None,
    ) -> QueueMessageRecord:
        self.steer_calls.append((run_id, content, source_session_id))
        return await super().steer(
            run_id,
            content,
            source_session_id=source_session_id,
        )


@dataclass(slots=True)
class _Harness:
    database: SqliteDatabase
    sessions: SessionRepository
    deliveries: DeliveryRepository
    queues: QueueRepository
    runtime: _RecordingRuntime
    pool: AsyncAgentPool
    router: ChatRouter
    source_session: _FakeSession
    target_session: _FakeSession | None
    source_id: str
    target_id: str | None

    async def aclose(self) -> None:
        await self.runtime.shutdown()
        await self.database.close()


async def _open_harness(
    tmp_path: Path,
    *,
    create_target: bool = True,
    register_target: bool = True,
    target_metadata: dict[str, JSONValue] | None = None,
) -> _Harness:
    database = SqliteDatabase(tmp_path / "tau.sqlite3")
    await database.open()

    sessions = SessionRepository(database)
    source_record = await sessions.create(
        workspace_root=tmp_path,
        provider_name="test",
        model="model",
        agent_name="source",
        session_id="source",
    )

    target_record = None
    if create_target:
        target_record = await sessions.create(
            workspace_root=tmp_path,
            provider_name="test",
            model="model",
            agent_name="target",
            session_id="target",
            metadata=target_metadata,
        )

    source_session = _FakeSession()
    target_session = _FakeSession() if register_target and target_record is not None else None
    pool = AsyncAgentPool(max_concurrency=1)
    queues = QueueRepository(database)
    runtime = _RecordingRuntime(
        pool,
        RunRepository(database),
        queues,
        AuditRepository(database),
    )
    runtime.register_session(source_record.session_id, source_session)
    if target_record is not None and target_session is not None:
        runtime.register_session(target_record.session_id, target_session)

    deliveries = DeliveryRepository(database)
    return _Harness(
        database=database,
        sessions=sessions,
        deliveries=deliveries,
        queues=queues,
        runtime=runtime,
        pool=pool,
        router=ChatRouter(sessions, deliveries, runtime, pool),
        source_session=source_session,
        target_session=target_session,
        source_id=source_record.session_id,
        target_id=target_record.session_id if target_record is not None else None,
    )


async def _create_target(
    harness: _Harness,
    *,
    session_id: str,
    agent_name: str,
    metadata: dict[str, JSONValue] | None = None,
    release: asyncio.Event | None = None,
) -> tuple[SessionRecord, _FakeSession]:
    record = await harness.sessions.create(
        workspace_root=harness.database.path.parent,
        provider_name="test",
        model="model",
        agent_name=agent_name,
        session_id=session_id,
        metadata=metadata,
    )
    session = _FakeSession(release=release)
    harness.runtime.register_session(record.session_id, session)
    return record, session


@pytest.mark.anyio
async def test_chat_routing_resolve_target_supports_local_and_remote_selectors(
    tmp_path: Path,
) -> None:
    harness = await _open_harness(
        tmp_path,
        target_metadata={"chat_jid": "room@example.com"},
    )

    try:
        address, target = await harness.router.resolve_target(target_agent_name=" target ")
        assert address == "@target"
        assert target is not None and target.session_id == harness.target_id

        address, target = await harness.router.resolve_target(target_chat_jid="room@example.com")
        assert address == "chat_jid:room@example.com"
        assert target is not None and target.session_id == harness.target_id

        address, target = await harness.router.resolve_target(target_address="xmpp! @target ")
        assert address == "xmpp!@target"
        assert target is None
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_send_dispatches_to_active_local_target(tmp_path: Path) -> None:
    harness = await _open_harness(tmp_path)

    try:
        result = await harness.router.send(
            harness.source_id,
            "hello from source",
            target_agent_name="target",
        )
        assert result.status == "dispatched"
        assert result.run_id is not None
        assert result.target_session_id == harness.target_id
        assert result.delivery.idempotency_key is None
        assert result.delivery.in_reply_to is None
        assert result.delivery.ancestry == ()
        assert result.delivery.hop_count == 0

        assert harness.target_session is not None
        await asyncio.wait_for(harness.target_session.prompt_started.wait(), timeout=1.0)
        assert harness.target_session.prompt_calls == ["hello from source"]
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_send_queue_mode_accepts_idle_target_and_returns_queue_id(
    tmp_path: Path,
) -> None:
    harness = await _open_harness(tmp_path)

    try:
        result = await harness.router.send(
            harness.source_id,
            "queue this for later",
            target_agent_name="target",
            mode="queue",
        )

        assert result.status == "accepted"
        assert result.run_id is None
        assert result.queue_id is not None
        assert result.delivery.accepted_at is not None
        assert result.target_session_id == harness.target_id
        assert harness.runtime.enqueue_calls == [
            (harness.target_id, "queue this for later", "follow_up", harness.source_id)
        ]

        queued = await harness.queues.get(result.queue_id)
        assert queued is not None
        assert queued.session_id == harness.target_id
        assert queued.queue_kind == "follow_up"
        assert queued.content == "queue this for later"
        assert queued.source_session_id == harness.source_id
        assert queued.consumed_at is None

        assert harness.target_session is not None
        assert harness.target_session.prompt_calls == []
        assert harness.target_session.queue_message_calls == []
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_send_steer_mode_uses_current_run_and_completes_delivery(
    tmp_path: Path,
) -> None:
    harness = await _open_harness(tmp_path, create_target=False, register_target=False)
    target_release = asyncio.Event()
    target_handle = None
    try:
        target_record, target_session = await _create_target(
            harness,
            session_id="target",
            agent_name="target",
            release=target_release,
        )
        target_handle = await harness.runtime.submit_prompt(target_record.session_id, "working")
        await asyncio.wait_for(target_session.prompt_started.wait(), timeout=1.0)

        active_run_id = harness.pool.snapshot(target_record.session_id).current_run_id
        assert active_run_id is not None

        result = await harness.router.send(
            harness.source_id,
            "adjust course",
            target_agent_name="target",
            mode="steer",
        )

        assert result.status == "completed"
        assert result.run_id == active_run_id
        assert result.queue_id is not None
        assert result.target_session_id == target_record.session_id
        assert harness.runtime.steer_calls == [(active_run_id, "adjust course", harness.source_id)]
        assert target_session.queue_message_calls == [("adjust course", "steer")]

        queued = await harness.queues.get(result.queue_id)
        assert queued is not None
        assert queued.session_id == target_record.session_id
        assert queued.queue_kind == "steer"
        assert queued.content == "adjust course"
        assert queued.source_session_id == harness.source_id
        assert queued.consumed_at is not None
        assert result.delivery.completed_at is not None
    finally:
        target_release.set()
        if target_handle is not None:
            await target_handle.wait()
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_send_steer_mode_rejects_idle_target(tmp_path: Path) -> None:
    harness = await _open_harness(tmp_path)

    try:
        with pytest.raises(ChatRoutingError, match="not running") as exc:
            await harness.router.send(
                harness.source_id,
                "adjust course",
                target_agent_name="target",
                mode="steer",
            )

        assert exc.value.code == "target_not_running"
        assert exc.value.delivery.status == "rejected"
        assert exc.value.delivery.target_session_id == harness.target_id
        assert exc.value.delivery.target_address == "@target"
        assert harness.target_id is not None
        assert await harness.queues.list(session_id=harness.target_id) == []
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_send_requires_exactly_one_target_selector(tmp_path: Path) -> None:
    harness = await _open_harness(tmp_path)

    try:
        with pytest.raises(ValueError, match="Exactly one non-blank target selector"):
            await harness.router.send(
                harness.source_id,
                "hello",
                target_agent_name="target",
                target_address="@target",
            )

        assert await harness.deliveries.list(source_session_id=harness.source_id) == []
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_send_requires_active_source_session(tmp_path: Path) -> None:
    harness = await _open_harness(tmp_path)

    try:
        inactive_source = await harness.sessions.create(
            workspace_root=tmp_path,
            provider_name="test",
            model="model",
            agent_name="inactive-source",
            session_id="inactive-source",
        )

        with pytest.raises(ValueError, match="Source session must exist and be active"):
            await harness.router.send(
                inactive_source.session_id,
                "hello",
                target_agent_name="target",
            )

        assert await harness.deliveries.list(source_session_id=inactive_source.session_id) == []
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_send_queue_mode_keeps_targets_isolated(tmp_path: Path) -> None:
    harness = await _open_harness(tmp_path, create_target=False, register_target=False)

    try:
        first_record, first_session = await _create_target(
            harness,
            session_id="target-one",
            agent_name="target-one",
        )
        second_record, second_session = await _create_target(
            harness,
            session_id="target-two",
            agent_name="target-two",
        )

        first = await harness.router.send(
            harness.source_id,
            "for first target",
            target_agent_name="target-one",
            mode="queue",
        )
        second = await harness.router.send(
            harness.source_id,
            "for second target",
            target_agent_name="target-two",
            mode="queue",
        )

        assert first.queue_id is not None
        assert second.queue_id is not None
        first_queue = await harness.queues.get(first.queue_id)
        second_queue = await harness.queues.get(second.queue_id)

        assert first_queue is not None
        assert second_queue is not None
        assert first_queue.queue_id != second_queue.queue_id
        assert first_queue.session_id == first_record.session_id
        assert second_queue.session_id == second_record.session_id
        assert first_queue.position == 0
        assert second_queue.position == 0
        assert first_queue.content == "for first target"
        assert second_queue.content == "for second target"
        assert await harness.queues.list(session_id=first_record.session_id) == [first_queue]
        assert await harness.queues.list(session_id=second_record.session_id) == [second_queue]
        assert first.target_session_id == first_record.session_id
        assert second.target_session_id == second_record.session_id
        assert first_session.prompt_calls == []
        assert first_session.queue_message_calls == []
        assert second_session.prompt_calls == []
        assert second_session.queue_message_calls == []
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_send_rejects_remote_target(tmp_path: Path) -> None:
    harness = await _open_harness(tmp_path)

    try:
        with pytest.raises(
            ChatRoutingError,
            match="Remote chat routing is not supported yet",
        ) as exc:
            await harness.router.send(
                harness.source_id,
                "hello",
                target_address="xmpp!@target",
            )

        assert exc.value.code == "remote_transport_unsupported"
        assert exc.value.delivery.status == "rejected"
        assert exc.value.delivery.transport == "xmpp"
        assert exc.value.delivery.target_address == "xmpp!@target"
        assert exc.value.delivery.accepted_at is None
        assert exc.value.delivery.completed_at is not None
        assert exc.value.delivery.idempotency_key is None
        assert exc.value.delivery.in_reply_to is None
        assert exc.value.delivery.ancestry == ()
        assert exc.value.delivery.hop_count == 0

        persisted = await harness.deliveries.get(exc.value.delivery.delivery_id)
        assert persisted == exc.value.delivery
        assert persisted is not None
        assert persisted.error == {
            "code": "remote_transport_unsupported",
            "message": "Remote chat routing is not supported yet.",
            "details": {
                "target_address": "xmpp!@target",
                "transport": "xmpp",
            },
        }
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_send_rejects_missing_target(tmp_path: Path) -> None:
    harness = await _open_harness(tmp_path, create_target=False, register_target=False)

    try:
        with pytest.raises(ChatRoutingError, match="target session is not active") as exc:
            await harness.router.send(
                harness.source_id,
                "hello",
                target_agent_name="missing",
            )

        assert exc.value.code == "target_not_found"
        assert exc.value.delivery.status == "rejected"
        assert exc.value.delivery.target_session_id is None
        assert exc.value.delivery.target_address == "@missing"
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_send_rejects_inactive_target(tmp_path: Path) -> None:
    harness = await _open_harness(tmp_path, register_target=False)

    try:
        with pytest.raises(ChatRoutingError, match="target session is not active") as exc:
            await harness.router.send(
                harness.source_id,
                "hello",
                target_agent_name="target",
            )

        assert exc.value.code == "target_not_active"
        assert exc.value.delivery.status == "rejected"
        assert exc.value.delivery.target_session_id == harness.target_id
        assert exc.value.delivery.target_address == "@target"
    finally:
        await harness.aclose()
