"""Async in-process pool for multiplexing coding sessions."""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol
from uuid import uuid4

from tau_agent import AgentEvent, ErrorEvent, QueueUpdateEvent

_TERMINAL_SENTINEL = object()


def _new_run_id() -> str:
    return uuid4().hex


class AgentPoolError(RuntimeError):
    """Base exception for async agent-pool failures."""


class PoolClosedError(AgentPoolError):
    """Raised when submitting work after pool shutdown."""


class SessionAlreadyRegisteredError(AgentPoolError):
    """Raised when attempting to register one duplicate session id."""


class DuplicateRunIdError(AgentPoolError):
    """Raised when one session run id is submitted more than once."""


class UnknownSessionError(AgentPoolError):
    """Raised when one session id is not registered."""


class SessionClosedError(AgentPoolError):
    """Raised when submitting work to one session closed to new work."""


class CodingSessionLike(Protocol):
    """Minimal coding-session surface required by ``AsyncAgentPool``."""

    def prompt(
        self,
        content: str,
        *,
        streaming_behavior: str | None = None,
    ) -> AsyncIterator[AgentEvent]:
        """Start one prompt run and stream resulting agent events."""

    def continue_(self) -> AsyncIterator[AgentEvent]:
        """Continue one restored or interrupted run."""

    async def queue_message(self, content: str, *, behavior: str) -> QueueUpdateEvent:
        """Queue one message for the currently active run."""

    def cancel(self) -> None:
        """Request cooperative cancellation of the current run."""

    async def aclose(self) -> None:
        """Close any session-owned resources."""


class PoolSessionState(StrEnum):
    """Externally visible state for one registered pool session."""

    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    CANCELLING = "cancelling"
    FAILED = "failed"
    CLOSED = "closed"


class RunStatus(StrEnum):
    """Final outcome for one submitted pool run."""

    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class PoolSessionSnapshot:
    """Immutable snapshot of one registered session."""

    session_id: str
    owned: bool
    state: PoolSessionState
    current_run_id: str | None
    queued_runs: int
    last_run_id: str | None
    last_error: ErrorEvent | None
    last_exception: BaseException | None


@dataclass(frozen=True, slots=True)
class RunResult:
    """Final result recorded for one submitted run."""

    run_id: str
    session_id: str
    status: RunStatus
    yielded_error: ErrorEvent | None = None
    exception: BaseException | None = None
    event_count: int = 0


class _EventStream:
    """Single-consumer bounded event stream that can abort blocked producers."""

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("Event stream capacity must be at least 1.")
        self._capacity = capacity
        self._items: deque[AgentEvent] = deque()
        self._lock = asyncio.Lock()
        self._can_put = asyncio.Event()
        self._can_put.set()
        self._can_get = asyncio.Event()
        self._aborted = False
        self._closed = False

    async def put(self, event: AgentEvent) -> bool:
        while True:
            async with self._lock:
                if self._closed or self._aborted:
                    return False
                if len(self._items) < self._capacity:
                    self._items.append(event)
                    self._can_get.set()
                    if len(self._items) >= self._capacity:
                        self._can_put.clear()
                    return True
            await self._can_put.wait()

    def abort(self) -> None:
        if self._closed and self._aborted:
            return
        self._aborted = True
        self._closed = True
        self._can_put.set()
        self._can_get.set()

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._can_put.set()
        self._can_get.set()

    async def iter_events(self) -> AsyncIterator[AgentEvent]:
        while True:
            async with self._lock:
                if self._items:
                    item = self._items.popleft()
                    if len(self._items) < self._capacity:
                        self._can_put.set()
                    if self._items or self._closed:
                        self._can_get.set()
                    else:
                        self._can_get.clear()
                elif self._closed:
                    return
                else:
                    self._can_get.clear()
                    item = None
            if item is None:
                await self._can_get.wait()
                continue
            yield item


@dataclass(frozen=True, slots=True)
class RunHandle:
    """Handle for one submitted run and its event stream."""

    run_id: str
    session_id: str
    task: asyncio.Task[RunResult]
    _stream: _EventStream

    def __aiter__(self) -> AsyncIterator[AgentEvent]:
        return self.events()

    async def events(self) -> AsyncIterator[AgentEvent]:
        """Iterate streamed events until the terminal sentinel arrives."""
        async for event in self._stream.iter_events():
            yield event

    def result(self) -> RunResult | None:
        """Return the completed result, if available."""
        if not self.task.done():
            return None
        return self.task.result()

    async def wait(self) -> RunResult:
        """Wait for one submitted run to finish."""
        return await asyncio.shield(self.task)


@dataclass(slots=True)
class _RegisteredSession:
    session_id: str
    session: CodingSessionLike
    owned: bool
    turn_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    run_tasks: dict[str, asyncio.Task[RunResult]] = field(default_factory=dict)
    seen_run_ids: set[str] = field(default_factory=set)
    state: PoolSessionState = PoolSessionState.IDLE
    pending_runs: int = 0
    current_run_id: str | None = None
    current_stream: _EventStream | None = None
    cancel_requested: bool = False
    accepting_new_work: bool = True
    disposed: bool = False
    last_run_id: str | None = None
    last_error: ErrorEvent | None = None
    last_exception: BaseException | None = None

    def snapshot(self) -> PoolSessionSnapshot:
        return PoolSessionSnapshot(
            session_id=self.session_id,
            owned=self.owned,
            state=self.state,
            current_run_id=self.current_run_id,
            queued_runs=self.pending_runs,
            last_run_id=self.last_run_id,
            last_error=self.last_error,
            last_exception=self.last_exception,
        )


class AsyncAgentPool:
    """Serialize session turns while sharing bounded global concurrency."""

    def __init__(self, *, max_concurrency: int, event_queue_size: int = 64) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1.")
        if event_queue_size < 1:
            raise ValueError("event_queue_size must be at least 1.")
        self._sessions: dict[str, _RegisteredSession] = {}
        self._tasks: set[asyncio.Task[RunResult]] = set()
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._event_queue_size = event_queue_size
        self._accepting_new_work = True
        self._shutdown_complete = False
        self._shutdown_lock = asyncio.Lock()

    def register_session(
        self,
        session_id: str,
        session: CodingSessionLike,
        *,
        owned: bool = False,
    ) -> PoolSessionSnapshot:
        """Register one session for pooled execution."""
        if session_id in self._sessions:
            raise SessionAlreadyRegisteredError(f"Session {session_id!r} is already registered.")
        entry = _RegisteredSession(session_id=session_id, session=session, owned=owned)
        self._refresh_state(entry)
        self._sessions[session_id] = entry
        return entry.snapshot()

    def snapshot(self, session_id: str) -> PoolSessionSnapshot:
        """Return one immutable session snapshot."""
        return self._require_session(session_id).snapshot()

    def snapshots(self) -> tuple[PoolSessionSnapshot, ...]:
        """Return immutable snapshots for all registered sessions."""
        return tuple(entry.snapshot() for entry in self._sessions.values())

    def submit_prompt(
        self,
        session_id: str,
        content: str,
        *,
        run_id: str | None = None,
    ) -> RunHandle:
        """Submit one prompt run for one registered session."""
        return self._submit(session_id, lambda session: session.prompt(content), run_id=run_id)

    def submit_continue(self, session_id: str, *, run_id: str | None = None) -> RunHandle:
        """Submit one continue run for one registered session."""
        return self._submit(session_id, lambda session: session.continue_(), run_id=run_id)

    async def steer(
        self,
        session_id: str,
        content: str,
        *,
        current_run_id: str,
    ) -> QueueUpdateEvent:
        """Queue one steering message for the specified active run."""
        return await self._queue_message(
            session_id,
            content,
            behavior="steer",
            current_run_id=current_run_id,
        )

    async def follow_up(
        self,
        session_id: str,
        content: str,
        *,
        current_run_id: str,
    ) -> QueueUpdateEvent:
        """Queue one follow-up message for the specified active run."""
        return await self._queue_message(
            session_id,
            content,
            behavior="follow_up",
            current_run_id=current_run_id,
        )

    def cancel_current_run(self, session_id: str) -> bool:
        """Request cooperative cancellation for the active run, if any."""
        entry = self._require_session(session_id)
        if entry.disposed:
            raise SessionClosedError(f"Session {session_id!r} is closed.")
        if entry.current_run_id is None:
            return False
        self._request_cancel(entry)
        return True

    async def close_session(self, session_id: str) -> None:
        """Stop accepting work, drain in-flight tasks, and close owned resources."""
        entry = self._require_session(session_id)
        if entry.disposed:
            return
        entry.accepting_new_work = False
        if entry.current_run_id is not None:
            self._request_cancel(entry)
        tasks = tuple(entry.run_tasks.values())
        if tasks:
            await asyncio.gather(*(asyncio.shield(task) for task in tasks))
        if entry.owned:
            await entry.session.aclose()
        entry.disposed = True
        self._refresh_state(entry)

    async def shutdown(self, *, cancel_timeout: float = 1.0) -> None:
        """Reject new work, drain existing tasks, and close owned sessions."""
        async with self._shutdown_lock:
            if self._shutdown_complete:
                return
            self._accepting_new_work = False
            for entry in self._sessions.values():
                if entry.disposed:
                    continue
                entry.accepting_new_work = False
                if entry.current_run_id is not None:
                    self._request_cancel(entry)
                else:
                    self._refresh_state(entry)
            tasks = tuple(self._tasks)
            if tasks:
                done, pending = await asyncio.wait(tasks, timeout=cancel_timeout)
                if pending:
                    for task in pending:
                        task.cancel()
                    await asyncio.gather(*pending, return_exceptions=True)
                else:
                    await asyncio.gather(*done, return_exceptions=True)
            for entry in self._sessions.values():
                if entry.disposed:
                    continue
                if entry.owned:
                    await entry.session.aclose()
                entry.disposed = True
                self._refresh_state(entry)
            self._shutdown_complete = True

    async def _queue_message(
        self,
        session_id: str,
        content: str,
        *,
        behavior: str,
        current_run_id: str,
    ) -> QueueUpdateEvent:
        if not current_run_id.strip():
            raise ValueError("current_run_id must be non-blank.")
        if not self._accepting_new_work:
            raise PoolClosedError("AsyncAgentPool is shut down.")
        entry = self._require_session(session_id)
        if entry.disposed or not entry.accepting_new_work:
            raise SessionClosedError(f"Session {session_id!r} is closed.")
        active_run_id = entry.current_run_id
        behavior_label = behavior.replace("_", " ")
        if active_run_id is None:
            raise RuntimeError(
                f"Session {session_id!r} has no active run; cannot queue {behavior_label}."
            )
        if active_run_id != current_run_id:
            raise RuntimeError(
                f"Session {session_id!r} active run changed from {current_run_id!r} "
                f"to {active_run_id!r}; refusing to queue {behavior_label}."
            )
        return await entry.session.queue_message(content, behavior=behavior)

    def _submit(
        self,
        session_id: str,
        factory: Callable[[CodingSessionLike], AsyncIterator[AgentEvent]],
        *,
        run_id: str | None = None,
    ) -> RunHandle:
        if not self._accepting_new_work:
            raise PoolClosedError("AsyncAgentPool is shut down.")
        entry = self._require_session(session_id)
        if entry.disposed or not entry.accepting_new_work:
            raise SessionClosedError(f"Session {session_id!r} is closed.")
        claimed_run_id = self._claim_run_id(entry, session_id, run_id)
        entry.pending_runs += 1
        entry.last_run_id = claimed_run_id
        entry.last_error = None
        entry.last_exception = None
        self._refresh_state(entry)
        stream = _EventStream(self._event_queue_size)
        task = asyncio.create_task(
            self._run(entry, claimed_run_id, stream, factory),
            name=f"tau-pool:{session_id}:{claimed_run_id}",
        )
        entry.run_tasks[claimed_run_id] = task
        self._tasks.add(task)
        task.add_done_callback(
            lambda done_task: self._on_task_done(entry, claimed_run_id, done_task)
        )
        return RunHandle(
            run_id=claimed_run_id,
            session_id=session_id,
            task=task,
            _stream=stream,
        )

    async def _run(
        self,
        entry: _RegisteredSession,
        run_id: str,
        stream: _EventStream,
        factory: Callable[[CodingSessionLike], AsyncIterator[AgentEvent]],
    ) -> RunResult:
        status = RunStatus.COMPLETED
        yielded_error: ErrorEvent | None = None
        exception: BaseException | None = None
        event_count = 0
        pending_consumed = False
        current_run_set = False
        semaphore_acquired = False

        try:
            async with entry.turn_lock:
                if not entry.accepting_new_work:
                    entry.pending_runs -= 1
                    pending_consumed = True
                    self._refresh_state(entry)
                    status = RunStatus.CANCELLED
                else:
                    await self._semaphore.acquire()
                    semaphore_acquired = True
                    entry.pending_runs -= 1
                    pending_consumed = True
                    if not entry.accepting_new_work:
                        self._refresh_state(entry)
                        status = RunStatus.CANCELLED
                    else:
                        entry.current_run_id = run_id
                        entry.current_stream = stream
                        current_run_set = True
                        entry.last_run_id = run_id
                        entry.cancel_requested = False
                        self._refresh_state(entry)
                        try:
                            async for event in factory(entry.session):
                                event_count += 1
                                if isinstance(event, ErrorEvent) and not event.recoverable:
                                    yielded_error = event
                                if not await stream.put(event):
                                    break
                        except asyncio.CancelledError as exc:
                            exception = exc
                            status = RunStatus.CANCELLED
                        except Exception as exc:  # noqa: BLE001 - result carries raised session exceptions
                            exception = exc
                            status = RunStatus.FAILED
                        else:
                            if yielded_error is not None:
                                status = RunStatus.FAILED
                            elif entry.cancel_requested:
                                status = RunStatus.CANCELLED
                            else:
                                status = RunStatus.COMPLETED
                        finally:
                            if semaphore_acquired:
                                self._semaphore.release()
                                semaphore_acquired = False
                    if semaphore_acquired:
                        self._semaphore.release()
                        semaphore_acquired = False
        except asyncio.CancelledError as exc:
            exception = exc
            status = RunStatus.CANCELLED
        finally:
            if not pending_consumed:
                entry.pending_runs -= 1
            if current_run_set and entry.current_run_id == run_id:
                entry.current_run_id = None
                entry.current_stream = None
                entry.cancel_requested = False
            if status is RunStatus.FAILED:
                entry.last_error = yielded_error
                entry.last_exception = exception
            else:
                entry.last_error = None
                entry.last_exception = None
            self._refresh_state(entry)
            await stream.close()

        return RunResult(
            run_id=run_id,
            session_id=entry.session_id,
            status=status,
            yielded_error=yielded_error,
            exception=exception,
            event_count=event_count,
        )

    def _on_task_done(
        self,
        entry: _RegisteredSession,
        run_id: str,
        task: asyncio.Task[RunResult],
    ) -> None:
        entry.run_tasks.pop(run_id, None)
        self._tasks.discard(task)
        self._refresh_state(entry)

    def _claim_run_id(
        self,
        entry: _RegisteredSession,
        session_id: str,
        run_id: str | None,
    ) -> str:
        claimed_run_id = _new_run_id() if run_id is None else run_id
        if run_id is not None and not claimed_run_id.strip():
            raise ValueError("run_id must be non-blank when provided.")
        if claimed_run_id in entry.run_tasks or claimed_run_id in entry.seen_run_ids:
            raise DuplicateRunIdError(
                f"Run id {claimed_run_id!r} has already been submitted for session {session_id!r}."
            )
        entry.seen_run_ids.add(claimed_run_id)
        return claimed_run_id

    def _request_cancel(self, entry: _RegisteredSession) -> None:
        if entry.current_run_id is None:
            return
        entry.cancel_requested = True
        if entry.current_stream is not None:
            entry.current_stream.abort()
        self._refresh_state(entry)
        entry.session.cancel()

    def _require_session(self, session_id: str) -> _RegisteredSession:
        entry = self._sessions.get(session_id)
        if entry is None:
            raise UnknownSessionError(f"Session {session_id!r} is not registered.")
        return entry

    def _refresh_state(self, entry: _RegisteredSession) -> None:
        if entry.current_run_id is not None:
            if entry.cancel_requested:
                entry.state = PoolSessionState.CANCELLING
            else:
                entry.state = PoolSessionState.RUNNING
            return
        if entry.pending_runs > 0:
            entry.state = PoolSessionState.QUEUED
            return
        if entry.disposed:
            entry.state = PoolSessionState.CLOSED
            return
        if entry.last_error is not None or entry.last_exception is not None:
            entry.state = PoolSessionState.FAILED
            return
        entry.state = PoolSessionState.IDLE


__all__ = [
    "AgentPoolError",
    "AsyncAgentPool",
    "CodingSessionLike",
    "DuplicateRunIdError",
    "PoolClosedError",
    "PoolSessionSnapshot",
    "PoolSessionState",
    "RunHandle",
    "RunResult",
    "RunStatus",
    "SessionAlreadyRegisteredError",
    "SessionClosedError",
    "UnknownSessionError",
]
