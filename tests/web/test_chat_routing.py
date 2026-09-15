from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest

from tau_agent import AgentEndEvent, AgentEvent, AgentStartEvent, QueueUpdateEvent
from tau_agent.types import JSONObject, JSONValue
from tau_coding.agent_pool import AsyncAgentPool
from tau_web.chat_routing import ChatRouter, ChatRoutingError
from tau_web.runtime import DurableAgentRuntime, DurableRunHandle
from tau_web.sqlite.connection import SqliteDatabase
from tau_web.sqlite.repositories import (
    AuditRepository,
    DeliveryRepository,
    QueueKind,
    QueueMessageRecord,
    QueueRepository,
    RunRecord,
    RunRepository,
    RunStatus,
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


@dataclass(slots=True)
class _ControlledRunHandle:
    run_id: str
    session_id: str
    _future: asyncio.Future[RunRecord]

    async def wait(self) -> RunRecord:
        return await self._future


class _ControlledRunWait:
    def __init__(self) -> None:
        self._future: asyncio.Future[RunRecord] = asyncio.get_running_loop().create_future()
        self.run_id: str | None = None
        self.session_id: str | None = None

    def bind(self, handle: DurableRunHandle) -> _ControlledRunHandle:
        self.run_id = handle.run_id
        self.session_id = handle.session_id
        return _ControlledRunHandle(handle.run_id, handle.session_id, self._future)

    def release(
        self,
        status: RunStatus,
        *,
        error: JSONObject | None = None,
    ) -> RunRecord:
        if self.run_id is None or self.session_id is None:
            raise AssertionError("Controlled run wait has not been bound to a run.")
        if self._future.done():
            raise AssertionError("Controlled run wait has already been released.")
        record = RunRecord(
            run_id=self.run_id,
            session_id=self.session_id,
            status=status,
            started_at="synthetic-started",
            updated_at="synthetic-updated",
            ended_at="synthetic-ended",
            last_event_type=None,
            last_status={"phase": status},
            error=error,
        )
        self._future.set_result(record)
        return record


class _RecordingRuntime(DurableAgentRuntime):
    def __init__(
        self,
        pool: AsyncAgentPool,
        runs: RunRepository,
        queues: QueueRepository,
        audit: AuditRepository,
    ) -> None:
        super().__init__(pool, runs, queues, audit)
        self.submit_prompt_calls: list[tuple[str, str, str | None]] = []
        self.submit_prompt_started = asyncio.Event()
        self.submit_prompt_release: asyncio.Event | None = None
        self.submit_prompt_wait_controls: list[_ControlledRunWait] = []
        self.enqueue_calls: list[tuple[str, JSONValue, QueueKind, str | None]] = []
        self.steer_calls: list[tuple[str, str, str | None]] = []

    def control_next_submit_prompt_wait(self) -> _ControlledRunWait:
        control = _ControlledRunWait()
        self.submit_prompt_wait_controls.append(control)
        return control

    async def submit_prompt(
        self,
        session_id: str,
        content: str,
        *,
        run_id: str | None = None,
    ) -> DurableRunHandle:
        self.submit_prompt_calls.append((session_id, content, run_id))
        self.submit_prompt_started.set()
        if self.submit_prompt_release is not None:
            await self.submit_prompt_release.wait()
        handle = await super().submit_prompt(session_id, content, run_id=run_id)
        if self.submit_prompt_wait_controls:
            return cast(DurableRunHandle, self.submit_prompt_wait_controls.pop(0).bind(handle))
        return handle

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


class _TestClock:
    def __init__(self, now: float = 0.0) -> None:
        self._now = now

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("Clock advance must not be negative.")
        self._now += seconds


async def _open_harness(
    tmp_path: Path,
    *,
    create_target: bool = True,
    register_target: bool = True,
    target_metadata: dict[str, JSONValue] | None = None,
    max_hops: int = 8,
    max_deliveries_per_window: int = 30,
    rate_window_seconds: float = 60,
    clock: Callable[[], float] | None = None,
    pool_max_concurrency: int = 1,
    source_release: asyncio.Event | None = None,
    target_release: asyncio.Event | None = None,
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

    source_session = _FakeSession(release=source_release)
    target_session = (
        _FakeSession(release=target_release)
        if register_target and target_record is not None
        else None
    )
    pool = AsyncAgentPool(max_concurrency=pool_max_concurrency)
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
        router=ChatRouter(
            sessions,
            deliveries,
            runtime,
            pool,
            max_hops=max_hops,
            max_deliveries_per_window=max_deliveries_per_window,
            rate_window_seconds=rate_window_seconds,
            clock=clock,
        ),
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
        assert result.deduped is False
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
        assert result.deduped is False
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
        assert result.deduped is False
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
async def test_chat_routing_send_deduplicates_concurrent_same_key_auto_dispatch(
    tmp_path: Path,
) -> None:
    harness = await _open_harness(tmp_path)
    release = asyncio.Event()
    harness.runtime.submit_prompt_release = release

    try:
        first_task = asyncio.create_task(
            harness.router.send(
                harness.source_id,
                "hello once",
                target_agent_name="target",
                idempotency_key="stable",
            )
        )
        await asyncio.wait_for(harness.runtime.submit_prompt_started.wait(), timeout=1.0)

        second_task = asyncio.create_task(
            harness.router.send(
                harness.source_id,
                "hello once",
                target_agent_name="target",
                idempotency_key="stable",
            )
        )
        await asyncio.sleep(0)
        assert not second_task.done()

        release.set()
        first, second = await asyncio.gather(first_task, second_task)

        assert first.deduped is False
        assert first.run_id is not None
        assert first.queue_id is None
        assert second.deduped is True
        assert second.run_id is None
        assert second.queue_id is None
        assert second.delivery == first.delivery
        assert harness.runtime.submit_prompt_calls == [(harness.target_id, "hello once", None)]
        assert await harness.deliveries.list(
            source_session_id=harness.source_id,
        ) == [first.delivery]

        assert harness.target_session is not None
        await asyncio.wait_for(harness.target_session.prompt_started.wait(), timeout=1.0)
        assert harness.target_session.prompt_calls == ["hello once"]
    finally:
        release.set()
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_send_replays_original_delivery_for_same_local_key(
    tmp_path: Path,
) -> None:
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
            "original content",
            target_agent_name="target-one",
            idempotency_key="stable",
        )
        replay = await harness.router.send(
            harness.source_id,
            "changed content",
            target_agent_name="target-two",
            mode="queue",
            idempotency_key="stable",
            in_reply_to="missing-parent",
        )

        assert first.deduped is False
        assert first.run_id is not None
        assert first.delivery.target_session_id == first_record.session_id
        assert replay.deduped is True
        assert replay.run_id is None
        assert replay.queue_id is None
        assert replay.delivery == first.delivery
        assert replay.mode == "auto"
        assert replay.target_session_id == first_record.session_id
        assert replay.target_session_id != second_record.session_id
        assert harness.runtime.enqueue_calls == []
        assert await harness.deliveries.list(
            source_session_id=harness.source_id,
        ) == [first.delivery]

        await asyncio.wait_for(first_session.prompt_started.wait(), timeout=1.0)
        assert first_session.prompt_calls == ["original content"]
        assert second_session.prompt_calls == []
        assert second_session.queue_message_calls == []
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_send_rate_limits_third_attempt_until_window_expires(
    tmp_path: Path,
) -> None:
    clock = _TestClock()
    harness = await _open_harness(
        tmp_path,
        max_deliveries_per_window=2,
        rate_window_seconds=60,
        clock=clock,
    )

    try:
        first = await harness.router.send(
            harness.source_id,
            "first",
            target_agent_name="target",
        )
        second = await harness.router.send(
            harness.source_id,
            "second",
            target_agent_name="target",
        )

        assert first.status == "dispatched"
        assert second.status == "dispatched"
        runtime_calls_before = list(harness.runtime.submit_prompt_calls)

        with pytest.raises(ChatRoutingError, match="rate limit") as exc:
            await harness.router.send(
                harness.source_id,
                "third",
                target_agent_name="target",
            )

        assert exc.value.code == "rate_limit_exceeded"
        assert exc.value.delivery.status == "rejected"
        assert exc.value.delivery.error == {
            "code": "rate_limit_exceeded",
            "message": "The source session exceeded the configured dispatch rate limit.",
            "details": {"retry_after": 60.0},
        }
        assert harness.runtime.submit_prompt_calls == runtime_calls_before

        clock.advance(60.0)
        allowed = await harness.router.send(
            harness.source_id,
            "after window",
            target_agent_name="target",
        )

        assert allowed.status == "dispatched"
        assert len(harness.runtime.submit_prompt_calls) == 3
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_send_idempotency_replay_bypasses_rate_limit(tmp_path: Path) -> None:
    clock = _TestClock()
    harness = await _open_harness(
        tmp_path,
        max_deliveries_per_window=2,
        rate_window_seconds=60,
        clock=clock,
    )

    try:
        first = await harness.router.send(
            harness.source_id,
            "hello once",
            target_agent_name="target",
            idempotency_key="stable",
        )
        replay = await harness.router.send(
            harness.source_id,
            "ignored replay",
            target_agent_name="target",
            mode="queue",
            idempotency_key="stable",
        )
        second = await harness.router.send(
            harness.source_id,
            "hello twice",
            target_agent_name="target",
        )

        assert first.status == "dispatched"
        assert replay.deduped is True
        assert replay.delivery == first.delivery
        assert second.status == "dispatched"
        assert harness.runtime.submit_prompt_calls == [
            (harness.target_id, "hello once", None),
            (harness.target_id, "hello twice", None),
        ]

        with pytest.raises(ChatRoutingError, match="rate limit") as exc:
            await harness.router.send(
                harness.source_id,
                "third distinct message",
                target_agent_name="target",
            )

        assert exc.value.code == "rate_limit_exceeded"
        assert len(await harness.deliveries.list(source_session_id=harness.source_id)) == 3
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_auto_receipt_marks_delivery_completed_after_drain(
    tmp_path: Path,
) -> None:
    harness = await _open_harness(tmp_path)
    control = harness.runtime.control_next_submit_prompt_wait()

    try:
        result = await harness.router.send(
            harness.source_id,
            "hello target",
            target_agent_name="target",
        )
        dispatched = await harness.deliveries.get(result.delivery_id)

        assert result.status == "dispatched"
        assert dispatched is not None
        assert dispatched.status == "dispatched"

        control.release("completed")
        assert await harness.router.drain_receipts() == ()

        completed = await harness.deliveries.get(result.delivery_id)
        assert completed is not None
        assert completed.status == "completed"
        assert completed.error is None
        assert completed.completed_at is not None
    finally:
        await harness.router.shutdown_receipts(cancel=True)
        await harness.aclose()


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("run_status", "error_code", "error_message"),
    [
        ("failed", "target_run_failed", "The target run failed."),
        ("cancelled", "target_run_cancelled", "The target run was cancelled."),
        ("interrupted", "target_run_interrupted", "The target run was interrupted."),
    ],
)
async def test_chat_routing_auto_receipt_marks_terminal_target_run_failures(
    tmp_path: Path,
    run_status: RunStatus,
    error_code: str,
    error_message: str,
) -> None:
    harness = await _open_harness(tmp_path)
    control = harness.runtime.control_next_submit_prompt_wait()
    run_error = {"code": "run_failed", "message": f"{run_status} target run"}

    try:
        result = await harness.router.send(
            harness.source_id,
            f"hello {run_status}",
            target_agent_name="target",
        )

        control.release(run_status, error=run_error)
        assert await harness.router.drain_receipts() == ()

        failed = await harness.deliveries.get(result.delivery_id)
        assert failed is not None
        assert failed.status == "failed"
        assert failed.completed_at is not None
        assert failed.error == {
            "code": error_code,
            "message": error_message,
            "details": {
                "run_id": result.run_id,
                "target_session_id": harness.target_id,
                "target_address": "@target",
                "run_error": run_error,
            },
        }
    finally:
        await harness.router.shutdown_receipts(cancel=True)
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_auto_receipts_do_not_block_opposite_direction_dispatch(
    tmp_path: Path,
) -> None:
    source_release = asyncio.Event()
    target_release = asyncio.Event()
    harness = await _open_harness(
        tmp_path,
        source_release=source_release,
        target_release=target_release,
    )
    target_wait = harness.runtime.control_next_submit_prompt_wait()
    source_wait = harness.runtime.control_next_submit_prompt_wait()

    try:
        to_target = await asyncio.wait_for(
            harness.router.send(
                harness.source_id,
                "hello target",
                target_agent_name="target",
            ),
            timeout=1.0,
        )

        assert harness.target_session is not None
        await asyncio.wait_for(harness.target_session.prompt_started.wait(), timeout=1.0)
        assert harness.target_session.prompt_calls == ["hello target"]
        assert harness.source_session.prompt_calls == []

        assert harness.target_id is not None
        to_source = await asyncio.wait_for(
            harness.router.send(
                harness.target_id,
                "hello source",
                target_agent_name="source",
            ),
            timeout=1.0,
        )

        assert to_target.status == "dispatched"
        assert to_source.status == "dispatched"
        assert harness.source_session.prompt_calls == []

        target_release.set()
        source_release.set()
        await asyncio.wait_for(harness.source_session.prompt_started.wait(), timeout=1.0)
        assert harness.source_session.prompt_calls == ["hello source"]

        target_wait.release("completed")
        source_wait.release("completed")
        assert await harness.router.drain_receipts() == ()

        target_delivery = await harness.deliveries.get(to_target.delivery_id)
        source_delivery = await harness.deliveries.get(to_source.delivery_id)
        assert target_delivery is not None and target_delivery.status == "completed"
        assert source_delivery is not None and source_delivery.status == "completed"
    finally:
        target_release.set()
        source_release.set()
        await harness.router.shutdown_receipts(cancel=True)
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_shutdown_receipts_can_cancel_pending_auto_receipts(
    tmp_path: Path,
) -> None:
    harness = await _open_harness(tmp_path)
    harness.runtime.control_next_submit_prompt_wait()

    try:
        result = await harness.router.send(
            harness.source_id,
            "hello target",
            target_agent_name="target",
        )
        dispatched = await harness.deliveries.get(result.delivery_id)

        assert dispatched is not None
        assert dispatched.status == "dispatched"
        assert await harness.router.shutdown_receipts(cancel=True) == ()
        assert await harness.router.drain_receipts() == ()
        assert await harness.deliveries.get(result.delivery_id) == dispatched
    finally:
        await harness.router.shutdown_receipts(cancel=True)
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_send_persists_ancestry_for_valid_reply(tmp_path: Path) -> None:
    harness = await _open_harness(tmp_path)

    try:
        root = await harness.router.send(
            harness.source_id,
            "hello target",
            target_agent_name="target",
        )

        assert harness.target_id is not None
        reply = await harness.router.send(
            harness.target_id,
            "hello source",
            target_agent_name="source",
            in_reply_to=root.delivery_id,
        )

        assert reply.status == "dispatched"
        assert reply.run_id is not None
        assert reply.deduped is False
        assert reply.target_session_id == harness.source_id
        assert reply.delivery.in_reply_to == root.delivery_id
        assert reply.delivery.ancestry == (root.delivery_id,)
        assert reply.delivery.hop_count == 1
        assert await harness.deliveries.get(reply.delivery_id) == reply.delivery

        await asyncio.wait_for(harness.source_session.prompt_started.wait(), timeout=1.0)
        assert harness.source_session.prompt_calls == ["hello source"]
        assert harness.target_session is not None
        assert harness.target_session.prompt_calls == ["hello target"]
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_send_rejects_reply_from_wrong_source_session(tmp_path: Path) -> None:
    harness = await _open_harness(tmp_path)

    try:
        root = await harness.router.send(
            harness.source_id,
            "hello target",
            target_agent_name="target",
        )

        with pytest.raises(ValueError, match="Reply source session must match"):
            await harness.router.send(
                harness.source_id,
                "invalid reply",
                target_agent_name="target",
                in_reply_to=root.delivery_id,
            )

        assert await harness.deliveries.list(source_session_id=harness.source_id) == [root.delivery]
        assert harness.runtime.submit_prompt_calls == [
            (harness.target_id, "hello target", None),
        ]
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_send_rejects_missing_reply_parent(tmp_path: Path) -> None:
    harness = await _open_harness(tmp_path)

    try:
        with pytest.raises(ValueError, match="Reply parent delivery does not exist"):
            await harness.router.send(
                harness.source_id,
                "hello target",
                target_agent_name="target",
                in_reply_to="missing-parent",
            )

        assert await harness.deliveries.list(source_session_id=harness.source_id) == []
        assert harness.runtime.submit_prompt_calls == []
        assert harness.runtime.enqueue_calls == []
        assert harness.runtime.steer_calls == []
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_send_rejects_replies_above_hop_limit_without_dispatch(
    tmp_path: Path,
) -> None:
    harness = await _open_harness(tmp_path, max_hops=1)

    try:
        root = await harness.router.send(
            harness.source_id,
            "hello target",
            target_agent_name="target",
        )
        assert harness.target_id is not None
        reply = await harness.router.send(
            harness.target_id,
            "hello source",
            target_agent_name="source",
            in_reply_to=root.delivery_id,
        )

        assert reply.delivery.hop_count == 1
        assert harness.target_session is not None
        prompt_calls_before = list(harness.runtime.submit_prompt_calls)
        target_prompts_before = list(harness.target_session.prompt_calls)

        with pytest.raises(ChatRoutingError, match="hop limit") as exc:
            await harness.router.send(
                harness.source_id,
                "hello again",
                target_agent_name="target",
                in_reply_to=reply.delivery_id,
            )

        assert exc.value.code == "hop_limit_exceeded"
        assert exc.value.delivery.status == "rejected"
        assert exc.value.delivery.target_session_id is None
        assert exc.value.delivery.target_address == "@target"
        assert exc.value.delivery.in_reply_to == reply.delivery_id
        assert exc.value.delivery.ancestry == (root.delivery_id, reply.delivery_id)
        assert exc.value.delivery.hop_count == 2
        assert exc.value.delivery.error == {
            "code": "hop_limit_exceeded",
            "message": "Reply delivery exceeded the configured hop limit.",
            "details": {
                "hop_count": 2,
                "max_hops": 1,
            },
        }
        assert await harness.deliveries.get(exc.value.delivery.delivery_id) == exc.value.delivery
        assert harness.runtime.submit_prompt_calls == prompt_calls_before
        assert harness.target_session.prompt_calls == target_prompts_before
        assert harness.runtime.enqueue_calls == []
        assert harness.runtime.steer_calls == []
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_chat_routing_send_rejects_repeated_target_cycles_before_dispatch(
    tmp_path: Path,
) -> None:
    harness = await _open_harness(tmp_path)

    try:
        third_record, third_session = await _create_target(
            harness,
            session_id="third",
            agent_name="third",
        )
        root = await harness.router.send(
            harness.source_id,
            "hello target",
            target_agent_name="target",
        )
        assert harness.target_id is not None
        second = await harness.router.send(
            harness.target_id,
            "hello third",
            target_agent_name=third_record.agent_name,
            in_reply_to=root.delivery_id,
        )

        assert second.target_session_id == third_record.session_id
        assert harness.target_session is not None
        prompt_calls_before = list(harness.runtime.submit_prompt_calls)
        target_prompts_before = list(harness.target_session.prompt_calls)

        with pytest.raises(ChatRoutingError, match="revisit a previous target") as exc:
            await harness.router.send(
                third_record.session_id,
                "cycle back to target",
                target_agent_name="target",
                in_reply_to=second.delivery_id,
            )

        assert exc.value.code == "delivery_cycle"
        assert exc.value.delivery.status == "rejected"
        assert exc.value.delivery.target_session_id == harness.target_id
        assert exc.value.delivery.in_reply_to == second.delivery_id
        assert exc.value.delivery.ancestry == (root.delivery_id, second.delivery_id)
        assert exc.value.delivery.hop_count == 2
        assert await harness.deliveries.get(exc.value.delivery.delivery_id) == exc.value.delivery
        assert harness.runtime.submit_prompt_calls == prompt_calls_before
        assert harness.target_session.prompt_calls == target_prompts_before
        await asyncio.wait_for(third_session.prompt_started.wait(), timeout=1.0)
        assert third_session.prompt_calls == ["hello third"]
    finally:
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
