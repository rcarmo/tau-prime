"""Durable coordination between the async agent pool and runtime repositories."""

from __future__ import annotations

import asyncio
import re
from collections.abc import Callable
from dataclasses import dataclass

from tau_agent import UserAttachment, UserMessage
from tau_agent.types import JSONObject, JSONValue
from tau_coding.agent_pool import (
    AgentPoolError,
    AsyncAgentPool,
    CodingSessionLike,
    PoolSessionSnapshot,
    RunHandle,
    RunResult,
)
from tau_coding.agent_pool import (
    RunStatus as PoolRunStatus,
)
from tau_web.events import EventProjectorCallback, canonical_agent_event_type
from tau_web.sqlite.repositories import (
    AuditRepository,
    MediaRepository,
    QueueKind,
    QueueMessageRecord,
    QueueRepository,
    RecordNotFoundError,
    RunRecord,
    RunRepository,
    RunStatus,
)

_TERMINAL_RUN_STATUSES = frozenset({"completed", "cancelled", "failed", "interrupted"})
_QUEUEABLE_RUN_STATUSES = frozenset({"pending", "running"})
_MEDIA_REFERENCE_PATTERN = re.compile(r"\[media:([A-Za-z0-9._-]+)\]")


@dataclass(frozen=True, slots=True)
class DurableRunHandle:
    """Wait handle for one durable runtime submission."""

    run_id: str
    session_id: str
    _task: asyncio.Task[RunRecord]
    _release: Callable[[asyncio.Task[RunRecord]], None]

    async def wait(self) -> RunRecord:
        """Wait for the durable run record to reach its terminal state."""
        try:
            return await asyncio.shield(self._task)
        finally:
            if self._task.done():
                self._release(self._task)


class DurableAgentRuntime:
    """Persist pool-submitted runs and reconcile them to durable state."""

    def __init__(
        self,
        pool: AsyncAgentPool,
        runs: RunRepository,
        queues: QueueRepository,
        audit: AuditRepository,
        event_projector: EventProjectorCallback | None = None,
        media: MediaRepository | None = None,
    ) -> None:
        self._pool = pool
        self._runs = runs
        self._queues = queues
        self._audit = audit
        self._event_projector = event_projector
        self._media = media
        self._abort_run_ids: set[str] = set()
        self._driver_tasks: set[asyncio.Task[RunRecord]] = set()
        self._queue_locks: dict[str, asyncio.Lock] = {}
        self._shutdown_lock = asyncio.Lock()
        self._shutdown_complete = False

    def register_session(
        self,
        session_id: str,
        session: CodingSessionLike,
        *,
        owned: bool = False,
    ) -> PoolSessionSnapshot:
        """Register one session with the underlying pool."""
        return self._pool.register_session(session_id, session, owned=owned)

    async def submit_prompt(
        self,
        session_id: str,
        content: str,
        *,
        run_id: str | None = None,
    ) -> DurableRunHandle:
        """Create a durable pending row and submit one prompt run."""
        prompt = await self._hydrate_media_references(session_id, content)
        return await self._submit(
            session_id,
            lambda claimed_run_id: self._pool.submit_prompt(
                session_id,
                prompt,
                run_id=claimed_run_id,
            ),
            run_id=run_id,
        )

    async def submit_continue(
        self,
        session_id: str,
        *,
        run_id: str | None = None,
    ) -> DurableRunHandle:
        """Create a durable pending row and submit one continue run."""
        return await self._submit(
            session_id,
            lambda claimed_run_id: self._pool.submit_continue(
                session_id,
                run_id=claimed_run_id,
            ),
            run_id=run_id,
        )

    async def cancel(self, run_id: str) -> bool:
        """Request cooperative cancellation for the specified active run."""
        record = await self._require_run(run_id)
        if record.status in _TERMINAL_RUN_STATUSES:
            return False
        try:
            snapshot = self._pool.snapshot(record.session_id)
        except AgentPoolError:
            return False
        if snapshot.current_run_id != record.run_id:
            return False
        try:
            return self._pool.cancel_current_run(record.session_id)
        except AgentPoolError:
            return False

    async def abort(self, run_id: str) -> bool:
        """Request cancellation and force the specified active run to stop."""
        record = await self._require_run(run_id)
        if record.status in _TERMINAL_RUN_STATUSES:
            return False
        try:
            snapshot = self._pool.snapshot(record.session_id)
        except AgentPoolError:
            return False
        if snapshot.current_run_id != record.run_id:
            return False
        self._abort_run_ids.add(record.run_id)
        try:
            aborted = self._pool.abort_current_run(record.session_id)
        except AgentPoolError:
            self._abort_run_ids.discard(record.run_id)
            return False
        if not aborted:
            self._abort_run_ids.discard(record.run_id)
        return aborted

    async def retry(self, run_id: str) -> DurableRunHandle:
        """Resubmit one failed, interrupted, or cancelled run via continue."""
        previous = await self._require_run(run_id)
        if previous.status not in {"failed", "interrupted", "cancelled"}:
            raise ValueError("Only failed, interrupted, or cancelled runs can be retried.")
        handle = await self.submit_continue(previous.session_id)
        await self._audit.append(
            event_type="run.retry",
            actor_type="runtime",
            session_id=previous.session_id,
            request_id=handle.run_id,
            details={
                "previous_run_id": previous.run_id,
                "previous_status": previous.status,
                "new_run_id": handle.run_id,
            },
        )
        return handle

    async def enqueue(
        self,
        session_id: str,
        content: JSONValue,
        queue_kind: QueueKind = "follow_up",
        source_session_id: str | None = None,
    ) -> QueueMessageRecord:
        """Persist one durable queued message without dispatching it."""
        async with self._queue_lock(session_id):
            return await self._enqueue_locked(
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
        """Durably enqueue one steering message and dispatch it when it reaches FIFO head."""
        return await self._enqueue_for_run(
            run_id,
            content,
            queue_kind="steer",
            source_session_id=source_session_id,
        )

    async def follow_up(
        self,
        run_id: str,
        content: str,
        source_session_id: str | None = None,
    ) -> QueueMessageRecord:
        """Durably enqueue one follow-up message and dispatch it when it reaches FIFO head."""
        return await self._enqueue_for_run(
            run_id,
            content,
            queue_kind="follow_up",
            source_session_id=source_session_id,
        )

    async def dispatch_next(
        self,
        run_id: str,
        queue_kind: QueueKind,
    ) -> QueueMessageRecord | None:
        """Try to dispatch the current FIFO head for one run and queue kind."""
        initial = await self._require_run(run_id)
        async with self._queue_lock(initial.session_id):
            record = await self._require_run(run_id)
            self._require_queueable_run(record)
            queued = await self._queues.list(session_id=record.session_id, queue_kind=queue_kind)
            if not queued:
                return None
            return await self._dispatch_locked(record, queued[0])

    async def shutdown(self, *, cancel_timeout: float = 1.0) -> None:
        """Drain pool and driver tasks, closing owned sessions through the pool."""
        async with self._shutdown_lock:
            if self._shutdown_complete:
                return
            await self._pool.shutdown(cancel_timeout=cancel_timeout)
            await self._drain_driver_tasks()
            self._shutdown_complete = True

    async def _submit(
        self,
        session_id: str,
        submitter: Callable[[str], RunHandle],
        *,
        run_id: str | None,
    ) -> DurableRunHandle:
        created = await self._runs.create(
            session_id,
            run_id=run_id,
            status="pending",
            last_status={"phase": "pending"},
        )
        await self._append_transition(created, previous_status=None)
        try:
            pool_handle = submitter(created.run_id)
        except Exception as exc:
            failed = await self._runs.update_status(
                created.run_id,
                status="failed",
                last_status={"phase": "failed"},
                error=_exception_error("submission_failed", exc),
            )
            await self._append_transition(
                failed,
                previous_status=created.status,
                reason="submission_failed",
            )
            raise
        driver = asyncio.create_task(
            self._drive_run(created, pool_handle),
            name=f"tau-web-runtime:{created.session_id}:{created.run_id}",
        )
        self._driver_tasks.add(driver)
        return DurableRunHandle(
            run_id=created.run_id,
            session_id=created.session_id,
            _task=driver,
            _release=self._driver_tasks.discard,
        )

    async def _drive_run(self, created: RunRecord, handle: RunHandle) -> RunRecord:
        current = created
        last_event_type = created.last_event_type
        running_marked = False
        sequence = 0
        try:
            async for event in handle.events():
                sequence += 1
                event_type = canonical_agent_event_type(event)
                last_event_type = event_type
                previous_status = current.status
                current = await self._runs.update_status(
                    handle.run_id,
                    status="running",
                    last_event_type=event_type,
                    last_status={"phase": "running"},
                )
                if not running_marked:
                    await self._append_transition(current, previous_status=previous_status)
                    running_marked = True
                if self._event_projector is not None:
                    await self._event_projector(
                        current.session_id,
                        handle.run_id,
                        sequence,
                        event,
                    )
            result = await handle.wait()
            final_status = _terminal_status_for_result(
                result,
                interrupted=handle.run_id in self._abort_run_ids,
            )
            final = await self._runs.update_status(
                handle.run_id,
                status=final_status,
                last_event_type=last_event_type,
                last_status={"phase": final_status},
                error=_terminal_error(result, final_status),
            )
            await self._append_transition(final, previous_status=current.status)
            return final
        finally:
            self._abort_run_ids.discard(handle.run_id)

    async def _enqueue_for_run(
        self,
        run_id: str,
        content: str,
        *,
        queue_kind: QueueKind,
        source_session_id: str | None,
    ) -> QueueMessageRecord:
        initial = await self._require_run(run_id)
        async with self._queue_lock(initial.session_id):
            record = await self._require_run(run_id)
            self._require_queueable_run(record)
            queued = await self._enqueue_locked(
                record.session_id,
                content,
                queue_kind=queue_kind,
                source_session_id=source_session_id,
            )
            pending = await self._queues.list(session_id=record.session_id, queue_kind=queue_kind)
            if not pending:
                raise RuntimeError("Queued message disappeared before dispatch inspection")
            if pending[0].queue_id != queued.queue_id:
                await self._append_queue_audit(
                    "queue.defer",
                    queued,
                    run_id=record.run_id,
                    reason="backlog",
                )
                return queued
            return await self._dispatch_locked(record, queued)

    async def _enqueue_locked(
        self,
        session_id: str,
        content: JSONValue,
        *,
        queue_kind: QueueKind,
        source_session_id: str | None,
    ) -> QueueMessageRecord:
        record = await self._queues.enqueue(
            session_id,
            queue_kind=queue_kind,
            content=content,
            source_session_id=source_session_id,
        )
        await self._append_queue_audit("queue.enqueue", record)
        return record

    async def _dispatch_locked(
        self,
        run: RunRecord,
        queued: QueueMessageRecord,
    ) -> QueueMessageRecord:
        content = queued.content
        if not isinstance(content, str):
            raise ValueError(
                f"Queued message {queued.queue_id!r} for {queued.queue_kind!r} must have string "
                "content."
            )
        prompt = await self._hydrate_media_references(run.session_id, content)
        try:
            if queued.queue_kind == "steer":
                await self._pool.steer(run.session_id, prompt, current_run_id=run.run_id)
            else:
                await self._pool.follow_up(run.session_id, prompt, current_run_id=run.run_id)
        except RuntimeError as exc:
            return await self._defer_or_raise_queue_race(run, queued, exc)
        consumed = await self._queues.consume_exact(
            queued.queue_id,
            session_id=run.session_id,
            queue_kind=queued.queue_kind,
        )
        await self._append_queue_audit("queue.consume", consumed, run_id=run.run_id)
        return consumed

    async def _defer_or_raise_queue_race(
        self,
        run: RunRecord,
        queued: QueueMessageRecord,
        error: RuntimeError,
    ) -> QueueMessageRecord:
        snapshot = self._pool.snapshot(run.session_id)
        if snapshot.current_run_id == run.run_id:
            raise error
        reason = "no_active_run" if snapshot.current_run_id is None else "run_changed"
        await self._append_queue_audit(
            "queue.defer",
            queued,
            run_id=run.run_id,
            reason=reason,
            active_run_id=snapshot.current_run_id,
            error_message=str(error),
        )
        return queued

    async def _append_transition(
        self,
        record: RunRecord,
        *,
        previous_status: RunStatus | None,
        reason: str | None = None,
    ) -> None:
        details: dict[str, JSONValue] = {
            "run_id": record.run_id,
            "from_status": previous_status,
            "to_status": record.status,
        }
        if record.last_event_type is not None:
            details["last_event_type"] = record.last_event_type
        if record.error is not None:
            details["error"] = record.error
        if reason is not None:
            details["reason"] = reason
        await self._audit.append(
            event_type="run.transition",
            actor_type="runtime",
            session_id=record.session_id,
            request_id=record.run_id,
            details=details,
        )

    async def _append_queue_audit(
        self,
        event_type: str,
        record: QueueMessageRecord,
        *,
        run_id: str | None = None,
        reason: str | None = None,
        active_run_id: str | None = None,
        error_message: str | None = None,
    ) -> None:
        details: dict[str, JSONValue] = {
            "queue_id": record.queue_id,
            "queue_kind": record.queue_kind,
            "position": record.position,
            "content": record.content,
        }
        if record.source_session_id is not None:
            details["source_session_id"] = record.source_session_id
        if record.consumed_at is not None:
            details["consumed_at"] = record.consumed_at
        if run_id is not None:
            details["run_id"] = run_id
        if reason is not None:
            details["reason"] = reason
        if active_run_id is not None:
            details["active_run_id"] = active_run_id
        if error_message is not None:
            details["error_message"] = error_message
        await self._audit.append(
            event_type=event_type,
            actor_type="runtime",
            session_id=record.session_id,
            request_id=record.queue_id,
            details=details,
        )

    async def _drain_driver_tasks(self) -> None:
        while self._driver_tasks:
            pending = tuple(self._driver_tasks)
            results = await asyncio.gather(*pending, return_exceptions=True)
            for task in pending:
                self._driver_tasks.discard(task)
            for result in results:
                if isinstance(result, BaseException):
                    raise result

    async def _require_run(self, run_id: str) -> RunRecord:
        record = await self._runs.get(run_id)
        if record is None:
            raise RecordNotFoundError(f"Unknown run: {run_id}")
        return record

    async def _hydrate_media_references(
        self,
        session_id: str,
        content: str,
    ) -> str | UserMessage:
        """Resolve composer media markers into transient provider image data."""
        if self._media is None:
            return content
        media_ids = tuple(dict.fromkeys(_MEDIA_REFERENCE_PATTERN.findall(content)))
        if not media_ids:
            return content

        attachments: list[UserAttachment] = []
        for media_id in media_ids:
            item = await self._media.get_item(media_id)
            if item is None or item.deleted_at is not None:
                raise ValueError(f"Unknown media item: {media_id}")
            if item.session_id not in {None, session_id}:
                raise ValueError(f"Media item {media_id!r} belongs to another session")
            blob = await self._media.get_blob(item.blob_id)
            if blob is None:
                raise ValueError(f"Unknown media blob: {item.blob_id}")
            await self._media.add_reference(
                media_id,
                reference_type="session",
                reference_id=session_id,
            )
            attachments.append(
                UserAttachment(
                    media_id=item.media_id,
                    filename=item.filename,
                    media_type=item.media_type,
                    size_bytes=len(blob.content),
                    data=blob.content,
                )
            )
        return UserMessage(content=content, attachments=attachments)

    def _queue_lock(self, session_id: str) -> asyncio.Lock:
        lock = self._queue_locks.get(session_id)
        if lock is None:
            lock = asyncio.Lock()
            self._queue_locks[session_id] = lock
        return lock

    def _require_queueable_run(self, record: RunRecord) -> None:
        if record.status not in _QUEUEABLE_RUN_STATUSES:
            raise ValueError("Only pending or running runs can accept queued messages.")


def _terminal_status_for_result(result: RunResult, *, interrupted: bool) -> RunStatus:
    if result.status is PoolRunStatus.COMPLETED:
        return "completed"
    if result.status is PoolRunStatus.CANCELLED:
        return "interrupted" if interrupted else "cancelled"
    return "failed"


def _terminal_error(result: RunResult, status: RunStatus) -> JSONObject | None:
    if status != "failed":
        return None
    if result.yielded_error is not None:
        details: dict[str, JSONValue] = {
            "code": "agent_error",
            "message": result.yielded_error.message,
            "recoverable": result.yielded_error.recoverable,
        }
        if result.yielded_error.data is not None:
            details["data"] = result.yielded_error.data
        return details
    if result.exception is not None:
        return _exception_error("run_failed", result.exception)
    return {"code": "run_failed", "message": "Run failed without an error payload"}


def _exception_error(code: str, exception: BaseException) -> JSONObject:
    return {
        "code": code,
        "message": str(exception) or exception.__class__.__name__,
        "exception_type": exception.__class__.__name__,
    }


__all__ = ["DurableAgentRuntime", "DurableRunHandle"]
