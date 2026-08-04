# mypy: disable-error-code="untyped-decorator"

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass

import pytest

import tau_coding as tau_coding_package
from tau_agent import AgentEndEvent, AgentEvent, AgentStartEvent, ErrorEvent, QueueUpdateEvent
from tau_coding.agent_pool import (
    AsyncAgentPool,
    DuplicateRunIdError,
    PoolClosedError,
    PoolSessionState,
    RunHandle,
    RunStatus,
    SessionClosedError,
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@dataclass(slots=True)
class _Script:
    events: tuple[AgentEvent, ...] = ()
    started: asyncio.Event | None = None
    release: asyncio.Event | None = None
    yielded: tuple[asyncio.Event | None, ...] = ()
    completed: asyncio.Event | None = None
    exception: BaseException | None = None


class _YieldingLock(asyncio.Lock):
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        self.release()
        await asyncio.sleep(0)


class _FakeSession:
    def __init__(
        self,
        *,
        prompt_scripts: Sequence[_Script] = (),
        continue_scripts: Sequence[_Script] = (),
        queue_message_scripts: Sequence[_Script] = (),
    ) -> None:
        self._prompt_scripts: deque[_Script] = deque(prompt_scripts)
        self._continue_scripts: deque[_Script] = deque(continue_scripts)
        self._queue_message_scripts: deque[_Script] = deque(queue_message_scripts)
        self.prompt_calls: list[str] = []
        self.continue_calls = 0
        self.queue_message_calls: list[tuple[str, str]] = []
        self.cancel_calls = 0
        self.close_calls = 0
        self.queued_steering: tuple[str, ...] = ()
        self.queued_follow_up: tuple[str, ...] = ()
        self._active_release: asyncio.Event | None = None
        self._active_run_token: int | None = None
        self._next_run_token = 0
        self._running = False

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
        if self._active_release is not None:
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
        self._running = True
        try:
            if script.started is not None:
                script.started.set()
            if script.release is not None:
                await script.release.wait()
            for index, event in enumerate(script.events):
                if index < len(script.yielded):
                    signal = script.yielded[index]
                    if signal is not None:
                        signal.set()
                yield event
            if script.exception is not None:
                raise script.exception
        finally:
            self._active_run_token = None
            self._running = False
            self._active_release = None
            if script.completed is not None:
                script.completed.set()


async def _collect_events(handle: RunHandle) -> list[AgentEvent]:
    return [event async for event in handle.events()]


async def _event_types(handle: RunHandle) -> list[str]:
    return [event.type async for event in handle.events()]


async def _assert_pool_drained(pool: AsyncAgentPool, *session_ids: str) -> None:
    await asyncio.sleep(0)
    assert not pool._tasks
    for session_id in session_ids:
        assert not pool._sessions[session_id].run_tasks


def test_package_root_exports_agent_pool_types() -> None:
    assert tau_coding_package.AsyncAgentPool is AsyncAgentPool
    assert tau_coding_package.DuplicateRunIdError is DuplicateRunIdError
    assert tau_coding_package.PoolSessionState is PoolSessionState
    assert tau_coding_package.RunStatus is RunStatus


def test_agent_pool_rejects_blank_explicit_run_id() -> None:
    pool = AsyncAgentPool(max_concurrency=1)
    pool.register_session("alpha", _FakeSession())

    with pytest.raises(ValueError, match="non-blank"):
        pool.submit_prompt("alpha", "hello", run_id="   ")

    with pytest.raises(ValueError, match="non-blank"):
        pool.submit_continue("alpha", run_id="")


@pytest.mark.anyio
async def test_agent_pool_accepts_explicit_prompt_run_id() -> None:
    session = _FakeSession(prompt_scripts=(_Script(events=(AgentStartEvent(), AgentEndEvent())),))
    pool = AsyncAgentPool(max_concurrency=1)
    pool.register_session("alpha", session)

    handle = pool.submit_prompt("alpha", "hello", run_id="prompt-1")
    result = await handle.wait()

    assert handle.run_id == "prompt-1"
    assert result.run_id == "prompt-1"
    assert result.status is RunStatus.COMPLETED
    await _assert_pool_drained(pool, "alpha")


@pytest.mark.anyio
async def test_agent_pool_accepts_explicit_continue_run_id() -> None:
    session = _FakeSession(continue_scripts=(_Script(events=(AgentStartEvent(), AgentEndEvent())),))
    pool = AsyncAgentPool(max_concurrency=1)
    pool.register_session("alpha", session)

    handle = pool.submit_continue("alpha", run_id="continue-1")
    result = await handle.wait()

    assert handle.run_id == "continue-1"
    assert result.run_id == "continue-1"
    assert result.status is RunStatus.COMPLETED
    assert session.continue_calls == 1
    await _assert_pool_drained(pool, "alpha")


@pytest.mark.anyio
async def test_agent_pool_rejects_duplicate_explicit_run_id_for_session_lifetime() -> None:
    session = _FakeSession(prompt_scripts=(_Script(events=(AgentStartEvent(), AgentEndEvent())),))
    pool = AsyncAgentPool(max_concurrency=1)
    pool.register_session("alpha", session)

    first = pool.submit_prompt("alpha", "hello", run_id="fixed-run")
    assert (await first.wait()).status is RunStatus.COMPLETED

    with pytest.raises(DuplicateRunIdError, match="fixed-run"):
        pool.submit_prompt("alpha", "again", run_id="fixed-run")

    await _assert_pool_drained(pool, "alpha")


@pytest.mark.anyio
async def test_agent_pool_rejects_duplicate_explicit_run_id_after_many_other_runs() -> None:
    extra_runs = 1_024
    session = _FakeSession(prompt_scripts=tuple(_Script() for _ in range(extra_runs + 1)))
    pool = AsyncAgentPool(max_concurrency=1)
    pool.register_session("alpha", session)

    first = pool.submit_prompt("alpha", "hello", run_id="fixed-run")
    assert (await first.wait()).status is RunStatus.COMPLETED

    for index in range(extra_runs):
        handle = pool.submit_prompt("alpha", f"run-{index}", run_id=f"run-{index}")
        assert (await handle.wait()).status is RunStatus.COMPLETED

    with pytest.raises(DuplicateRunIdError, match="fixed-run"):
        pool.submit_prompt("alpha", "again", run_id="fixed-run")

    await _assert_pool_drained(pool, "alpha")


@pytest.mark.anyio
async def test_agent_pool_steer_queues_message_for_current_run() -> None:
    started = asyncio.Event()
    release = asyncio.Event()
    session = _FakeSession(prompt_scripts=(_Script(started=started, release=release),))
    pool = AsyncAgentPool(max_concurrency=1)
    pool.register_session("alpha", session)

    handle = pool.submit_prompt("alpha", "hello", run_id="prompt-1")
    await asyncio.wait_for(started.wait(), timeout=1.0)

    queue_update = await pool.steer("alpha", "adjust", current_run_id=handle.run_id)

    assert queue_update == QueueUpdateEvent(steering=("adjust",), follow_up=())
    assert session.queue_message_calls == [("adjust", "steer")]
    assert pool.snapshot("alpha").current_run_id == handle.run_id

    release.set()
    assert (await handle.wait()).status is RunStatus.COMPLETED
    await _assert_pool_drained(pool, "alpha")


@pytest.mark.anyio
async def test_agent_pool_rejects_follow_up_for_stale_run_id() -> None:
    started = asyncio.Event()
    release = asyncio.Event()
    session = _FakeSession(prompt_scripts=(_Script(started=started, release=release),))
    pool = AsyncAgentPool(max_concurrency=1)
    pool.register_session("alpha", session)

    handle = pool.submit_prompt("alpha", "hello", run_id="prompt-1")
    await asyncio.wait_for(started.wait(), timeout=1.0)

    with pytest.raises(RuntimeError, match="active run changed"):
        await pool.follow_up("alpha", "later", current_run_id="prompt-0")

    assert session.queue_message_calls == []

    release.set()
    assert (await handle.wait()).status is RunStatus.COMPLETED
    await _assert_pool_drained(pool, "alpha")


@pytest.mark.anyio
async def test_agent_pool_rejects_queue_message_if_active_run_changes_during_session_queueing() -> (
    None
):
    first_started = asyncio.Event()
    first_release = asyncio.Event()
    second_started = asyncio.Event()
    second_release = asyncio.Event()
    queue_started = asyncio.Event()
    queue_release = asyncio.Event()
    session = _FakeSession(
        prompt_scripts=(
            _Script(started=first_started, release=first_release),
            _Script(started=second_started, release=second_release),
        ),
        queue_message_scripts=(_Script(started=queue_started, release=queue_release),),
    )
    pool = AsyncAgentPool(max_concurrency=1)
    pool.register_session("alpha", session)

    first = pool.submit_prompt("alpha", "hello", run_id="prompt-1")
    second = pool.submit_prompt("alpha", "again", run_id="prompt-2")
    await asyncio.wait_for(first_started.wait(), timeout=1.0)

    queue_task = asyncio.create_task(pool.steer("alpha", "adjust", current_run_id=first.run_id))
    await asyncio.wait_for(queue_started.wait(), timeout=1.0)

    first_release.set()
    assert (await first.wait()).status is RunStatus.COMPLETED
    await asyncio.wait_for(second_started.wait(), timeout=1.0)
    assert pool.snapshot("alpha").current_run_id == second.run_id

    queue_release.set()
    with pytest.raises(RuntimeError, match="active run changed"):
        await queue_task

    assert session.queued_steering == ()

    second_release.set()
    assert (await second.wait()).status is RunStatus.COMPLETED
    await _assert_pool_drained(pool, "alpha")


@pytest.mark.anyio
async def test_agent_pool_enforces_global_max_concurrency_exactly() -> None:
    alpha_started = asyncio.Event()
    alpha_release = asyncio.Event()
    beta_started = asyncio.Event()
    beta_release = asyncio.Event()
    gamma_started = asyncio.Event()
    gamma_release = asyncio.Event()

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
                events=(AgentStartEvent(), AgentEndEvent()),
                started=beta_started,
                release=beta_release,
            ),
        )
    )
    gamma = _FakeSession(
        prompt_scripts=(
            _Script(
                events=(AgentStartEvent(), AgentEndEvent()),
                started=gamma_started,
                release=gamma_release,
            ),
        )
    )
    pool = AsyncAgentPool(max_concurrency=2)
    pool.register_session("alpha", alpha)
    pool.register_session("beta", beta)
    pool.register_session("gamma", gamma)

    alpha_run = pool.submit_prompt("alpha", "alpha")
    beta_run = pool.submit_prompt("beta", "beta")
    gamma_run = pool.submit_prompt("gamma", "gamma")

    await asyncio.wait_for(alpha_started.wait(), timeout=1.0)
    await asyncio.wait_for(beta_started.wait(), timeout=1.0)
    assert not gamma_started.is_set()
    assert pool.snapshot("alpha").state is PoolSessionState.RUNNING
    assert pool.snapshot("beta").state is PoolSessionState.RUNNING
    assert pool.snapshot("gamma").state is PoolSessionState.QUEUED

    alpha_release.set()
    assert (await alpha_run.wait()).status is RunStatus.COMPLETED

    await asyncio.wait_for(gamma_started.wait(), timeout=1.0)
    assert not gamma_release.is_set()

    beta_release.set()
    gamma_release.set()
    assert (await beta_run.wait()).status is RunStatus.COMPLETED
    assert (await gamma_run.wait()).status is RunStatus.COMPLETED
    await _assert_pool_drained(pool, "alpha", "beta", "gamma")


@pytest.mark.anyio
async def test_agent_pool_allows_independent_sessions_to_overlap() -> None:
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
                events=(AgentStartEvent(), AgentEndEvent()),
                started=beta_started,
                release=beta_release,
            ),
        )
    )
    pool = AsyncAgentPool(max_concurrency=2)
    pool.register_session("alpha", alpha)
    pool.register_session("beta", beta)

    alpha_run = pool.submit_prompt("alpha", "first")
    beta_run = pool.submit_prompt("beta", "second")

    await asyncio.wait_for(alpha_started.wait(), timeout=1.0)
    await asyncio.wait_for(beta_started.wait(), timeout=1.0)
    assert pool.snapshot("alpha").state is PoolSessionState.RUNNING
    assert pool.snapshot("beta").state is PoolSessionState.RUNNING

    alpha_release.set()
    beta_release.set()
    assert (await alpha_run.wait()).status is RunStatus.COMPLETED
    assert (await beta_run.wait()).status is RunStatus.COMPLETED
    await _assert_pool_drained(pool, "alpha", "beta")


@pytest.mark.anyio
async def test_agent_pool_serializes_same_session_turns_fifo() -> None:
    first_started = asyncio.Event()
    first_release = asyncio.Event()
    second_started = asyncio.Event()
    second_release = asyncio.Event()

    session = _FakeSession(
        prompt_scripts=(
            _Script(
                events=(AgentStartEvent(), AgentEndEvent()),
                started=first_started,
                release=first_release,
            ),
            _Script(
                events=(AgentStartEvent(), AgentEndEvent()),
                started=second_started,
                release=second_release,
            ),
        )
    )
    pool = AsyncAgentPool(max_concurrency=2)
    pool.register_session("alpha", session)

    first = pool.submit_prompt("alpha", "first")
    second = pool.submit_prompt("alpha", "second")

    await asyncio.wait_for(first_started.wait(), timeout=1.0)
    assert not second_started.is_set()
    assert pool.snapshot("alpha").state is PoolSessionState.RUNNING
    assert pool.snapshot("alpha").queued_runs == 1

    first_release.set()
    assert (await first.wait()).status is RunStatus.COMPLETED

    await asyncio.wait_for(second_started.wait(), timeout=1.0)
    second_release.set()
    assert (await second.wait()).status is RunStatus.COMPLETED
    assert session.prompt_calls == ["first", "second"]
    await _assert_pool_drained(pool, "alpha")


@pytest.mark.anyio
async def test_agent_pool_submit_continue_uses_session_continue() -> None:
    session = _FakeSession(continue_scripts=(_Script(events=(AgentStartEvent(), AgentEndEvent())),))
    pool = AsyncAgentPool(max_concurrency=1)
    pool.register_session("alpha", session)

    handle = pool.submit_continue("alpha")

    result = await handle.wait()

    assert result.status is RunStatus.COMPLETED
    assert session.continue_calls == 1
    assert await _event_types(handle) == ["agent_start", "agent_end"]
    await _assert_pool_drained(pool, "alpha")


@pytest.mark.anyio
async def test_agent_pool_preserves_event_order_and_failed_result() -> None:
    error = ErrorEvent(message="boom", recoverable=False)
    session = _FakeSession(
        prompt_scripts=(_Script(events=(AgentStartEvent(), error, AgentEndEvent())),)
    )
    pool = AsyncAgentPool(max_concurrency=1)
    pool.register_session("alpha", session)

    handle = pool.submit_prompt("alpha", "hello")

    assert handle.result() is None
    result = await handle.wait()
    snapshot = pool.snapshot("alpha")

    assert result.status is RunStatus.FAILED
    assert result.yielded_error == error
    assert result.exception is None
    assert result.event_count == 3
    assert await _collect_events(handle) == [AgentStartEvent(), error, AgentEndEvent()]
    assert snapshot.state is PoolSessionState.FAILED
    assert snapshot.last_run_id == handle.run_id
    assert snapshot.last_error == error
    assert snapshot.last_exception is None
    await _assert_pool_drained(pool, "alpha")


@pytest.mark.anyio
async def test_agent_pool_shutdown_cancels_backpressured_run_and_leaves_no_tasks() -> None:
    second_yielded = asyncio.Event()
    session = _FakeSession(
        prompt_scripts=(
            _Script(
                events=(AgentStartEvent(), AgentEndEvent()),
                yielded=(None, second_yielded),
            ),
        )
    )
    pool = AsyncAgentPool(max_concurrency=1, event_queue_size=1)
    pool.register_session("alpha", session)

    handle = pool.submit_prompt("alpha", "hello")
    await asyncio.wait_for(second_yielded.wait(), timeout=1.0)

    await asyncio.wait_for(pool.shutdown(cancel_timeout=0.01), timeout=1.0)
    result = await asyncio.wait_for(handle.wait(), timeout=1.0)

    assert result.status is RunStatus.CANCELLED
    assert await _event_types(handle) == ["agent_start"]
    assert pool.snapshot("alpha").state is PoolSessionState.CLOSED
    assert session.close_calls == 0
    await _assert_pool_drained(pool, "alpha")


@pytest.mark.anyio
async def test_agent_pool_cancel_current_run_unblocks_backpressure_and_drains_queue() -> None:
    first_second_yielded = asyncio.Event()
    second_started = asyncio.Event()
    second_release = asyncio.Event()

    session = _FakeSession(
        prompt_scripts=(
            _Script(
                events=(AgentStartEvent(), AgentEndEvent()),
                yielded=(None, first_second_yielded),
            ),
            _Script(
                events=(AgentStartEvent(), AgentEndEvent()),
                started=second_started,
                release=second_release,
            ),
        )
    )
    pool = AsyncAgentPool(max_concurrency=1, event_queue_size=1)
    pool.register_session("alpha", session)

    first = pool.submit_prompt("alpha", "first")
    second = pool.submit_prompt("alpha", "second")
    second_events = asyncio.create_task(_event_types(second))
    await asyncio.wait_for(first_second_yielded.wait(), timeout=1.0)

    assert pool.cancel_current_run("alpha") is True
    assert pool.snapshot("alpha").state is PoolSessionState.CANCELLING

    first_result = await asyncio.wait_for(first.wait(), timeout=1.0)
    assert first_result.status is RunStatus.CANCELLED
    assert await _event_types(first) == ["agent_start"]

    await asyncio.wait_for(second_started.wait(), timeout=1.0)
    second_release.set()
    assert (await second.wait()).status is RunStatus.COMPLETED
    assert await second_events == ["agent_start", "agent_end"]
    assert session.cancel_calls == 1
    assert session.prompt_calls == ["first", "second"]
    await _assert_pool_drained(pool, "alpha")


@pytest.mark.anyio
async def test_agent_pool_predecessor_cleanup_does_not_clobber_successor_state() -> None:
    second_started = asyncio.Event()
    second_release = asyncio.Event()

    session = _FakeSession(
        prompt_scripts=(
            _Script(events=(AgentStartEvent(), AgentEndEvent())),
            _Script(
                events=(AgentStartEvent(), AgentEndEvent()),
                started=second_started,
                release=second_release,
            ),
        )
    )
    pool = AsyncAgentPool(max_concurrency=1)
    pool.register_session("alpha", session)
    pool._sessions["alpha"].turn_lock = _YieldingLock()

    first = pool.submit_prompt("alpha", "first")
    second = pool.submit_prompt("alpha", "second")

    assert (await first.wait()).status is RunStatus.COMPLETED
    assert await _event_types(first) == ["agent_start", "agent_end"]

    await asyncio.wait_for(second_started.wait(), timeout=1.0)
    snapshot = pool.snapshot("alpha")
    assert snapshot.current_run_id == second.run_id
    assert snapshot.state is PoolSessionState.RUNNING

    second_release.set()
    assert (await second.wait()).status is RunStatus.COMPLETED
    assert await _event_types(second) == ["agent_start", "agent_end"]
    await _assert_pool_drained(pool, "alpha")


@pytest.mark.anyio
async def test_agent_pool_records_exceptions_and_releases_global_slot() -> None:
    beta_started = asyncio.Event()
    beta_release = asyncio.Event()
    boom = RuntimeError("boom")

    alpha = _FakeSession(prompt_scripts=(_Script(events=(AgentStartEvent(),), exception=boom),))
    beta = _FakeSession(
        prompt_scripts=(
            _Script(
                events=(AgentStartEvent(), AgentEndEvent()),
                started=beta_started,
                release=beta_release,
            ),
        )
    )
    pool = AsyncAgentPool(max_concurrency=1)
    pool.register_session("alpha", alpha)
    pool.register_session("beta", beta)

    alpha_run = pool.submit_prompt("alpha", "alpha")
    beta_run = pool.submit_prompt("beta", "beta")

    alpha_result = await alpha_run.wait()

    assert alpha_result.status is RunStatus.FAILED
    assert alpha_result.exception is boom
    assert await _event_types(alpha_run) == ["agent_start"]

    await asyncio.wait_for(beta_started.wait(), timeout=1.0)
    beta_release.set()
    assert (await beta_run.wait()).status is RunStatus.COMPLETED
    assert await _event_types(beta_run) == ["agent_start", "agent_end"]
    await _assert_pool_drained(pool, "alpha", "beta")


@pytest.mark.anyio
async def test_close_session_cancels_active_run_closes_owned_session_and_rejects_new_work() -> None:
    started = asyncio.Event()
    release = asyncio.Event()
    session = _FakeSession(prompt_scripts=(_Script(started=started, release=release),))
    pool = AsyncAgentPool(max_concurrency=1)
    pool.register_session("alpha", session, owned=True)

    handle = pool.submit_prompt("alpha", "hello")
    await asyncio.wait_for(started.wait(), timeout=1.0)

    await pool.close_session("alpha")

    assert (await handle.wait()).status is RunStatus.CANCELLED
    assert session.cancel_calls == 1
    assert session.close_calls == 1
    assert pool.snapshot("alpha").state is PoolSessionState.CLOSED
    await _assert_pool_drained(pool, "alpha")

    with pytest.raises(SessionClosedError):
        pool.submit_prompt("alpha", "again")


@pytest.mark.anyio
async def test_agent_pool_shutdown_is_idempotent_and_respects_owned_sessions() -> None:
    owned = _FakeSession()
    borrowed = _FakeSession()
    pool = AsyncAgentPool(max_concurrency=1)
    pool.register_session("owned", owned, owned=True)
    pool.register_session("borrowed", borrowed, owned=False)

    await pool.shutdown()
    await pool.shutdown()

    assert owned.close_calls == 1
    assert borrowed.close_calls == 0
    assert pool.snapshot("owned").state is PoolSessionState.CLOSED
    assert pool.snapshot("borrowed").state is PoolSessionState.CLOSED
    await _assert_pool_drained(pool, "owned", "borrowed")

    with pytest.raises(PoolClosedError):
        pool.submit_prompt("owned", "again")
