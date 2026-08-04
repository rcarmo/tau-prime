from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest

from tau_agent import AgentEndEvent, AgentEvent, AgentStartEvent, ErrorEvent, QueueUpdateEvent
from tau_coding.agent_pool import AsyncAgentPool, PoolSessionState, UnknownSessionError
from tau_web.runtime import DurableAgentRuntime
from tau_web.sqlite.connection import SqliteDatabase
from tau_web.sqlite.repositories import (
    AuditRepository,
    QueueMessageRecord,
    QueueRepository,
    RunRepository,
)
from tau_web.sqlite.sessions import SessionRepository


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@dataclass(slots=True)
class _Script:
    events: tuple[AgentEvent, ...] = ()
    started: asyncio.Event | None = None
    release: asyncio.Event | None = None
    exception: BaseException | None = None


class _FakeSession:
    def __init__(
        self,
        *,
        prompt_scripts: Sequence[_Script] = (),
        continue_scripts: Sequence[_Script] = (),
        queue_message_scripts: Sequence[_Script] = (),
        cooperative_cancel: bool = True,
    ) -> None:
        self._prompt_scripts: deque[_Script] = deque(prompt_scripts)
        self._continue_scripts: deque[_Script] = deque(continue_scripts)
        self._queue_message_scripts: deque[_Script] = deque(queue_message_scripts)
        self._cooperative_cancel = cooperative_cancel
        self._active_release: asyncio.Event | None = None
        self._active_run_token: int | None = None
        self._next_run_token = 0
        self.prompt_calls: list[str] = []
        self.continue_calls = 0
        self.queue_message_calls: list[tuple[str, str]] = []
        self.queued_steering: tuple[str, ...] = ()
        self.queued_follow_up: tuple[str, ...] = ()
        self.cancel_calls = 0
        self.close_calls = 0

    def prompt(
        self,
        content: str,
        *,
        streaming_behavior: str | None = None,
    ) -> AsyncIterator[AgentEvent]:
        assert streaming_behavior is None
        self.prompt_calls.append(content)
        return self._run_script(self._next_prompt_script())

    def continue_(self) -> AsyncIterator[AgentEvent]:
        self.continue_calls += 1
        return self._run_script(self._next_continue_script())

    async def queue_message(self, content: str, *, behavior: str) -> QueueUpdateEvent:
        active_run_token = self._active_run_token
        if active_run_token is None:
            raise RuntimeError("Session is idle; cannot queue a message.")
        self.queue_message_calls.append((content, behavior))
        script = self._queue_message_scripts.popleft() if self._queue_message_scripts else _Script()
        if script.started is not None:
            script.started.set()
        if script.release is not None:
            await script.release.wait()
        if script.exception is not None:
            raise script.exception
        if self._active_run_token != active_run_token:
            raise RuntimeError("Session active run changed while queueing a message.")
        if behavior == "steer":
            self.queued_steering = (*self.queued_steering, content)
        elif behavior == "follow_up":
            self.queued_follow_up = (*self.queued_follow_up, content)
        else:
            raise AssertionError(f"Unexpected queue behavior: {behavior!r}")
        return QueueUpdateEvent(
            steering=self.queued_steering,
            follow_up=self.queued_follow_up,
        )

    def cancel(self) -> None:
        self.cancel_calls += 1
        if self._cooperative_cancel and self._active_release is not None:
            self._active_release.set()

    async def aclose(self) -> None:
        self.close_calls += 1

    def _next_prompt_script(self) -> _Script:
        if not self._prompt_scripts:
            raise AssertionError("No prompt script was queued.")
        return self._prompt_scripts.popleft()

    def _next_continue_script(self) -> _Script:
        if not self._continue_scripts:
            raise AssertionError("No continue script was queued.")
        return self._continue_scripts.popleft()

    async def _run_script(self, script: _Script) -> AsyncIterator[AgentEvent]:
        self._active_release = script.release
        self._next_run_token += 1
        self._active_run_token = self._next_run_token
        try:
            if script.started is not None:
                script.started.set()
            if script.release is not None:
                await script.release.wait()
            for event in script.events:
                yield event
            if script.exception is not None:
                raise script.exception
        finally:
            self._active_run_token = None
            self._active_release = None


@dataclass(slots=True)
class _RuntimeHarness:
    database: SqliteDatabase
    runtime: DurableAgentRuntime
    runs: RunRepository
    queues: QueueRepository
    audit: AuditRepository
    session: _FakeSession
    session_id: str

    async def aclose(self) -> None:
        await self.runtime.shutdown()
        await self.database.close()


async def _open_runtime(
    tmp_path: Path,
    session: _FakeSession,
    *,
    session_id: str = "alpha",
    owned: bool = False,
) -> _RuntimeHarness:
    database = SqliteDatabase(tmp_path / "tau.sqlite3")
    await database.open()
    await SessionRepository(database).create(
        workspace_root=tmp_path,
        provider_name="test",
        model="model",
        agent_name=session_id,
        session_id=session_id,
    )
    runs = RunRepository(database)
    queues = QueueRepository(database)
    audit = AuditRepository(database)
    runtime = DurableAgentRuntime(AsyncAgentPool(max_concurrency=1), runs, queues, audit)
    runtime.register_session(session_id, session, owned=owned)
    return _RuntimeHarness(
        database=database,
        runtime=runtime,
        runs=runs,
        queues=queues,
        audit=audit,
        session=session,
        session_id=session_id,
    )


async def _transition_statuses(harness: _RuntimeHarness) -> list[str]:
    records = list(reversed(await harness.audit.list(session_id=harness.session_id, limit=20)))
    return [
        str(record.details["to_status"])
        for record in records
        if record.event_type == "run.transition"
    ]


@pytest.mark.anyio
async def test_runtime_run_repository_list_is_session_isolated_for_overlapping_sessions(
    tmp_path: Path,
) -> None:
    alpha_started = asyncio.Event()
    alpha_release = asyncio.Event()
    beta_started = asyncio.Event()
    beta_release = asyncio.Event()
    alpha = _FakeSession(
        prompt_scripts=(
            _Script(
                events=(AgentStartEvent(), AgentEndEvent()),
                started=alpha_started,
                release=alpha_release,
            ),
        )
    )
    beta = _FakeSession(
        prompt_scripts=(
            _Script(
                events=(AgentStartEvent(), QueueUpdateEvent(follow_up=("beta-done",))),
                started=beta_started,
                release=beta_release,
            ),
        )
    )
    database = SqliteDatabase(tmp_path / "tau.sqlite3")
    await database.open()
    sessions = SessionRepository(database)
    await sessions.create(
        workspace_root=tmp_path,
        provider_name="test",
        model="model",
        agent_name="alpha",
        session_id="alpha",
    )
    await sessions.create(
        workspace_root=tmp_path,
        provider_name="test",
        model="model",
        agent_name="beta",
        session_id="beta",
    )
    runs = RunRepository(database)
    queues = QueueRepository(database)
    audit = AuditRepository(database)
    pool = AsyncAgentPool(max_concurrency=2)
    runtime = DurableAgentRuntime(pool, runs, queues, audit)
    runtime.register_session("alpha", alpha)
    runtime.register_session("beta", beta)

    try:
        alpha_handle = await runtime.submit_prompt("alpha", "first")
        beta_handle = await runtime.submit_prompt("beta", "second")

        await asyncio.wait_for(alpha_started.wait(), timeout=1.0)
        await asyncio.wait_for(beta_started.wait(), timeout=1.0)

        alpha_snapshot = pool.snapshot("alpha")
        beta_snapshot = pool.snapshot("beta")
        assert alpha_snapshot.state is PoolSessionState.RUNNING
        assert beta_snapshot.state is PoolSessionState.RUNNING
        assert alpha_snapshot.current_run_id == alpha_handle.run_id
        assert beta_snapshot.current_run_id == beta_handle.run_id

        alpha_active = await runs.list(session_id="alpha")
        beta_active = await runs.list(session_id="beta")
        assert [
            (
                record.run_id,
                record.session_id,
                record.status,
                record.last_status,
                record.last_event_type,
            )
            for record in alpha_active
        ] == [(alpha_handle.run_id, "alpha", "pending", {"phase": "pending"}, None)]
        assert [
            (
                record.run_id,
                record.session_id,
                record.status,
                record.last_status,
                record.last_event_type,
            )
            for record in beta_active
        ] == [(beta_handle.run_id, "beta", "pending", {"phase": "pending"}, None)]
        assert beta_handle.run_id not in {record.run_id for record in alpha_active}
        assert alpha_handle.run_id not in {record.run_id for record in beta_active}

        alpha_release.set()
        beta_release.set()
        alpha_record, beta_record = await asyncio.wait_for(
            asyncio.gather(alpha_handle.wait(), beta_handle.wait()),
            timeout=1.0,
        )

        assert alpha_record.status == "completed"
        assert alpha_record.last_event_type == "agent_end"
        assert alpha_record.last_status == {"phase": "completed"}
        assert beta_record.status == "completed"
        assert beta_record.last_event_type == "queue_update"
        assert beta_record.last_status == {"phase": "completed"}

        alpha_completed = await runs.list(session_id="alpha")
        beta_completed = await runs.list(session_id="beta")
        assert [
            (
                record.run_id,
                record.session_id,
                record.status,
                record.last_status,
                record.last_event_type,
            )
            for record in alpha_completed
        ] == [(alpha_handle.run_id, "alpha", "completed", {"phase": "completed"}, "agent_end")]
        assert [
            (
                record.run_id,
                record.session_id,
                record.status,
                record.last_status,
                record.last_event_type,
            )
            for record in beta_completed
        ] == [
            (
                beta_handle.run_id,
                "beta",
                "completed",
                {"phase": "completed"},
                "queue_update",
            )
        ]
        assert beta_handle.run_id not in {record.run_id for record in alpha_completed}
        assert alpha_handle.run_id not in {record.run_id for record in beta_completed}

        await runtime.shutdown()

        await asyncio.sleep(0)
        assert not runtime._driver_tasks
        assert not pool._tasks
    finally:
        alpha_release.set()
        beta_release.set()
        await runtime.shutdown()
        await database.close()


@pytest.mark.anyio
async def test_runtime_creates_pending_row_before_execution(tmp_path: Path) -> None:
    first_started = asyncio.Event()
    first_release = asyncio.Event()
    session = _FakeSession(
        prompt_scripts=(
            _Script(started=first_started, release=first_release),
            _Script(events=(AgentStartEvent(), AgentEndEvent())),
        )
    )
    harness = await _open_runtime(tmp_path, session)

    try:
        first = await harness.runtime.submit_prompt(harness.session_id, "first")
        await asyncio.wait_for(first_started.wait(), timeout=1.0)

        second = await harness.runtime.submit_prompt(harness.session_id, "second")
        pending = await harness.runs.get(second.run_id)

        assert pending is not None
        assert pending.status == "pending"
        assert pending.last_status == {"phase": "pending"}

        first_release.set()
        assert (await first.wait()).status == "completed"
        assert (await second.wait()).status == "completed"
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_runtime_serializes_concurrent_follow_up_enqueues(tmp_path: Path) -> None:
    run_started = asyncio.Event()
    run_release = asyncio.Event()
    first_queue_started = asyncio.Event()
    first_queue_release = asyncio.Event()
    session = _FakeSession(
        prompt_scripts=(_Script(started=run_started, release=run_release),),
        queue_message_scripts=(
            _Script(started=first_queue_started, release=first_queue_release),
            _Script(),
        ),
    )
    harness = await _open_runtime(tmp_path, session)

    handle = await harness.runtime.submit_prompt(harness.session_id, "work")
    first_task: asyncio.Task[QueueMessageRecord] | None = None
    second_task: asyncio.Task[QueueMessageRecord] | None = None
    try:
        await asyncio.wait_for(run_started.wait(), timeout=1.0)

        first_task = asyncio.create_task(harness.runtime.follow_up(handle.run_id, "one"))
        await asyncio.wait_for(first_queue_started.wait(), timeout=1.0)

        second_task = asyncio.create_task(harness.runtime.follow_up(handle.run_id, "two"))
        await asyncio.sleep(0)

        assert session.queue_message_calls == [("one", "follow_up")]

        first_queue_release.set()
        first = await asyncio.wait_for(first_task, timeout=1.0)
        second = await asyncio.wait_for(second_task, timeout=1.0)

        assert session.queue_message_calls == [("one", "follow_up"), ("two", "follow_up")]
        assert (first.position, second.position) == (0, 1)
        assert first.consumed_at is not None
        assert second.consumed_at is not None
        assert (
            await harness.queues.list(session_id=harness.session_id, queue_kind="follow_up") == []
        )
    finally:
        first_queue_release.set()
        run_release.set()
        if first_task is not None:
            await asyncio.gather(first_task, return_exceptions=True)
        if second_task is not None:
            await asyncio.gather(second_task, return_exceptions=True)
        await handle.wait()
        await harness.aclose()


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("method_name", "queue_kind", "reason", "queue_second_run"),
    [
        ("follow_up", "follow_up", "no_active_run", False),
        ("steer", "steer", "run_changed", True),
    ],
)
async def test_runtime_defers_queue_message_when_active_run_changes_during_dispatch(
    tmp_path: Path,
    method_name: str,
    queue_kind: str,
    reason: str,
    queue_second_run: bool,
) -> None:
    first_started = asyncio.Event()
    first_release = asyncio.Event()
    second_started = asyncio.Event()
    second_release = asyncio.Event()
    queue_started = asyncio.Event()
    queue_release = asyncio.Event()
    prompt_scripts = [_Script(started=first_started, release=first_release)]
    if queue_second_run:
        prompt_scripts.append(_Script(started=second_started, release=second_release))
    session = _FakeSession(
        prompt_scripts=tuple(prompt_scripts),
        queue_message_scripts=(_Script(started=queue_started, release=queue_release),),
    )
    harness = await _open_runtime(tmp_path, session)

    first = await harness.runtime.submit_prompt(harness.session_id, "work")
    second = None
    task: asyncio.Task[QueueMessageRecord] | None = None
    try:
        await asyncio.wait_for(first_started.wait(), timeout=1.0)
        if queue_second_run:
            second = await harness.runtime.submit_prompt(harness.session_id, "next")

        task = asyncio.create_task(
            harness.runtime.steer(first.run_id, "queued")
            if method_name == "steer"
            else harness.runtime.follow_up(first.run_id, "queued")
        )
        await asyncio.wait_for(queue_started.wait(), timeout=1.0)

        first_release.set()
        assert (await first.wait()).status == "completed"
        if queue_second_run:
            assert second is not None
            await asyncio.wait_for(second_started.wait(), timeout=1.0)

        queue_release.set()
        queued = await asyncio.wait_for(task, timeout=1.0)
        stored = await harness.queues.get(queued.queue_id)
        audits = await harness.audit.list(session_id=harness.session_id, limit=20)
        defer_audit = next(
            record
            for record in audits
            if record.event_type == "queue.defer" and record.request_id == queued.queue_id
        )

        assert queued.queue_kind == queue_kind
        assert queued.consumed_at is None
        assert stored == queued
        assert await harness.queues.list(session_id=harness.session_id, queue_kind=queue_kind) == [
            queued
        ]
        assert session.queue_message_calls == [("queued", queue_kind)]
        assert defer_audit.details["run_id"] == first.run_id
        assert defer_audit.details["reason"] == reason
        if second is None:
            assert "active_run_id" not in defer_audit.details
        else:
            assert defer_audit.details["active_run_id"] == second.run_id
    finally:
        first_release.set()
        second_release.set()
        queue_release.set()
        if task is not None:
            await asyncio.gather(task, return_exceptions=True)
        if second is not None:
            await second.wait()
        await harness.aclose()


@pytest.mark.anyio
async def test_runtime_follow_up_defers_fifo_backlog_until_dispatch_next(tmp_path: Path) -> None:
    run_started = asyncio.Event()
    run_release = asyncio.Event()
    session = _FakeSession(prompt_scripts=(_Script(started=run_started, release=run_release),))
    harness = await _open_runtime(tmp_path, session)

    handle = await harness.runtime.submit_prompt(harness.session_id, "work")
    try:
        await asyncio.wait_for(run_started.wait(), timeout=1.0)

        old = await harness.runtime.enqueue(
            harness.session_id,
            "old",
            queue_kind="follow_up",
        )
        new = await harness.runtime.follow_up(handle.run_id, "new")

        assert session.queue_message_calls == []
        assert old.consumed_at is None
        assert new.consumed_at is None
        assert await harness.queues.list(session_id=harness.session_id, queue_kind="follow_up") == [
            old,
            new,
        ]

        first = await harness.runtime.dispatch_next(handle.run_id, "follow_up")
        assert first is not None
        assert first.queue_id == old.queue_id
        assert first.position == old.position
        assert first.consumed_at is not None
        assert await harness.queues.get(old.queue_id) == first
        assert session.queue_message_calls == [("old", "follow_up")]
        assert await harness.queues.list(session_id=harness.session_id, queue_kind="follow_up") == [
            new
        ]

        second = await harness.runtime.dispatch_next(handle.run_id, "follow_up")
        assert second is not None
        assert second.queue_id == new.queue_id
        assert second.position == new.position
        assert second.consumed_at is not None
        assert await harness.queues.get(new.queue_id) == second
        assert session.queue_message_calls == [
            ("old", "follow_up"),
            ("new", "follow_up"),
        ]
        assert (
            await harness.queues.list(
                session_id=harness.session_id,
                queue_kind="follow_up",
            )
            == []
        )
    finally:
        run_release.set()
        await handle.wait()
        await harness.aclose()


@pytest.mark.anyio
async def test_runtime_persists_completed_run_and_audits_transitions(tmp_path: Path) -> None:
    session = _FakeSession(prompt_scripts=(_Script(events=(AgentStartEvent(), AgentEndEvent())),))
    harness = await _open_runtime(tmp_path, session)

    try:
        handle = await harness.runtime.submit_prompt(harness.session_id, "hello")
        record = await handle.wait()

        assert record.status == "completed"
        assert record.last_event_type == "agent_end"
        assert record.last_status == {"phase": "completed"}
        assert record.error is None
        assert await harness.runs.get(handle.run_id) == record
        assert await _transition_statuses(harness) == ["pending", "running", "completed"]
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_runtime_persists_failed_run_from_error_event(tmp_path: Path) -> None:
    session = _FakeSession(
        prompt_scripts=(
            _Script(events=(AgentStartEvent(), ErrorEvent(message="boom", recoverable=False))),
        )
    )
    harness = await _open_runtime(tmp_path, session)

    try:
        handle = await harness.runtime.submit_prompt(harness.session_id, "explode")
        record = await handle.wait()

        assert record.status == "failed"
        assert record.last_event_type == "error"
        assert record.last_status == {"phase": "failed"}
        assert record.error == {
            "code": "agent_error",
            "message": "boom",
            "recoverable": False,
        }
        assert await _transition_statuses(harness) == ["pending", "running", "failed"]
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_runtime_cancel_marks_run_cancelled(tmp_path: Path) -> None:
    started = asyncio.Event()
    session = _FakeSession(prompt_scripts=(_Script(started=started, release=asyncio.Event()),))
    harness = await _open_runtime(tmp_path, session)

    try:
        handle = await harness.runtime.submit_prompt(harness.session_id, "cancel me")
        await asyncio.wait_for(started.wait(), timeout=1.0)

        assert await harness.runtime.cancel(handle.run_id) is True

        record = await handle.wait()
        assert record.status == "cancelled"
        assert record.last_event_type is None
        assert record.error is None
        assert await _transition_statuses(harness) == ["pending", "cancelled"]
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_runtime_abort_maps_pool_cancelled_to_interrupted(tmp_path: Path) -> None:
    started = asyncio.Event()
    session = _FakeSession(
        prompt_scripts=(_Script(started=started, release=asyncio.Event()),),
        cooperative_cancel=False,
    )
    harness = await _open_runtime(tmp_path, session)

    try:
        handle = await harness.runtime.submit_prompt(harness.session_id, "abort me")
        await asyncio.wait_for(started.wait(), timeout=1.0)

        assert await harness.runtime.abort(handle.run_id) is True

        record = await handle.wait()
        assert record.status == "interrupted"
        assert record.last_event_type is None
        assert record.error is None
        assert session.cancel_calls == 1
        assert await _transition_statuses(harness) == ["pending", "interrupted"]
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_runtime_retry_leaves_old_run_unchanged_and_submits_continue(tmp_path: Path) -> None:
    session = _FakeSession(
        prompt_scripts=(
            _Script(events=(AgentStartEvent(), ErrorEvent(message="boom", recoverable=False))),
        ),
        continue_scripts=(_Script(events=(AgentStartEvent(), AgentEndEvent())),),
    )
    harness = await _open_runtime(tmp_path, session)

    try:
        failed_handle = await harness.runtime.submit_prompt(harness.session_id, "first")
        failed = await failed_handle.wait()
        retry_handle = await harness.runtime.retry(failed.run_id)
        retried = await retry_handle.wait()
        original = await harness.runs.get(failed.run_id)
        audits = await harness.audit.list(session_id=harness.session_id, limit=20)
        retry_audit = next(record for record in audits if record.event_type == "run.retry")

        assert original == failed
        assert failed.status == "failed"
        assert retried.status == "completed"
        assert retry_handle.run_id != failed.run_id
        assert session.continue_calls == 1
        assert retry_audit.details == {
            "previous_run_id": failed.run_id,
            "previous_status": "failed",
            "new_run_id": retry_handle.run_id,
        }
    finally:
        await harness.aclose()


@pytest.mark.anyio
async def test_runtime_marks_pool_submission_failure_failed(tmp_path: Path) -> None:
    session_id = "alpha"
    database = SqliteDatabase(tmp_path / "tau.sqlite3")
    await database.open()
    await SessionRepository(database).create(
        workspace_root=tmp_path,
        provider_name="test",
        model="model",
        agent_name=session_id,
        session_id=session_id,
    )
    runs = RunRepository(database)
    queues = QueueRepository(database)
    audit = AuditRepository(database)
    runtime = DurableAgentRuntime(AsyncAgentPool(max_concurrency=1), runs, queues, audit)

    try:
        with pytest.raises(UnknownSessionError, match=session_id):
            await runtime.submit_prompt(session_id, "hello")

        records = await runs.list(session_id=session_id)
        assert len(records) == 1
        failed = records[0]
        assert failed.status == "failed"
        assert failed.last_status == {"phase": "failed"}
        assert failed.error == {
            "code": "submission_failed",
            "message": "Session 'alpha' is not registered.",
            "exception_type": "UnknownSessionError",
        }
        audits = list(reversed(await audit.list(session_id=session_id, limit=20)))
        assert [
            str(record.details["to_status"])
            for record in audits
            if record.event_type == "run.transition"
        ] == ["pending", "failed"]
    finally:
        await runtime.shutdown()
        await database.close()


@pytest.mark.anyio
async def test_runtime_shutdown_drains_driver_tasks_and_closes_owned_sessions(
    tmp_path: Path,
) -> None:
    started = asyncio.Event()
    session = _FakeSession(prompt_scripts=(_Script(started=started, release=asyncio.Event()),))
    harness = await _open_runtime(tmp_path, session, owned=True)

    try:
        handle = await harness.runtime.submit_prompt(harness.session_id, "shutdown")
        await asyncio.wait_for(started.wait(), timeout=1.0)

        await harness.runtime.shutdown()
        await harness.runtime.shutdown()

        record = await handle.wait()
        assert record.status == "cancelled"
        assert session.close_calls == 1
        assert await _transition_statuses(harness) == ["pending", "cancelled"]
    finally:
        await harness.database.close()
