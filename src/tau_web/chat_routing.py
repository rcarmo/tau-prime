"""Local named-session chat routing for Tau Web."""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from time import monotonic
from typing import Never
from uuid import uuid4

from tau_agent.types import JSONObject, JSONValue
from tau_coding.agent_pool import AgentPoolError, AsyncAgentPool
from tau_web.runtime import DurableAgentRuntime, DurableRunHandle
from tau_web.sqlite.repositories import (
    DeliveryMode,
    DeliveryRecord,
    DeliveryRepository,
    RunRecord,
)
from tau_web.sqlite.sessions import SessionRecord, SessionRepository, validate_agent_name


@dataclass(frozen=True, slots=True)
class ChatDispatchResult:
    """Durable outcome for one routed chat submission."""

    delivery: DeliveryRecord
    run_id: str | None = None
    queue_id: str | None = None
    deduped: bool = False

    @property
    def delivery_id(self) -> str:
        return self.delivery.delivery_id

    @property
    def mode(self) -> DeliveryMode:
        return self.delivery.mode

    @property
    def status(self) -> str:
        return self.delivery.status

    @property
    def transport(self) -> str:
        return self.delivery.transport

    @property
    def target_session_id(self) -> str | None:
        return self.delivery.target_session_id

    @property
    def target_address(self) -> str | None:
        return self.delivery.target_address

    @property
    def error(self) -> JSONObject | None:
        return self.delivery.error


class ChatRoutingError(RuntimeError):
    """Raised when a durable chat delivery is rejected or fails dispatch."""

    def __init__(self, delivery: DeliveryRecord) -> None:
        self.delivery = delivery
        error = delivery.error or {}

        raw_code = error.get("code")
        self.code = raw_code if isinstance(raw_code, str) and raw_code else "chat_routing_error"

        raw_message = error.get("message")
        self._message = (
            raw_message if isinstance(raw_message, str) and raw_message else "Chat routing failed."
        )

        raw_details = error.get("details")
        self.details = _object_or_empty(raw_details)
        super().__init__(self._message)

    @property
    def message(self) -> str:
        return self._message

    @property
    def error(self) -> JSONObject | None:
        return self.delivery.error


@dataclass(frozen=True, slots=True)
class _TargetSelection:
    address: str
    transport: str
    is_remote: bool


@dataclass(frozen=True, slots=True)
class _ReplyContext:
    in_reply_to: str | None = None
    ancestry: tuple[str, ...] = ()
    hop_count: int = 0


@dataclass(slots=True)
class _IdempotencyLockState:
    lock: asyncio.Lock
    users: int = 0


@dataclass(slots=True)
class _SourceRateLimitState:
    lock: asyncio.Lock
    attempts: deque[float]


class ChatRouter:
    """Resolve local named-session targets and durably dispatch chat messages."""

    def __init__(
        self,
        sessions: SessionRepository,
        deliveries: DeliveryRepository,
        runtime: DurableAgentRuntime,
        pool: AsyncAgentPool,
        *,
        max_hops: int = 8,
        max_deliveries_per_window: int = 30,
        rate_window_seconds: float = 60,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if max_hops < 1:
            raise ValueError("Max hops must be at least 1.")
        if max_deliveries_per_window < 1:
            raise ValueError("Max deliveries per window must be positive.")
        if rate_window_seconds <= 0:
            raise ValueError("Rate window seconds must be positive.")
        self._sessions = sessions
        self._deliveries = deliveries
        self._runtime = runtime
        self._pool = pool
        self._max_hops = max_hops
        self._max_deliveries_per_window = max_deliveries_per_window
        self._rate_window_seconds = rate_window_seconds
        self._clock = clock or _default_clock
        self._idempotency_locks: dict[tuple[str, str], _IdempotencyLockState] = {}
        self._idempotency_registry_lock = asyncio.Lock()
        self._rate_limit_states: dict[str, _SourceRateLimitState] = {}
        self._rate_limit_registry_lock = asyncio.Lock()
        self._receipt_tasks: set[asyncio.Task[None]] = set()
        self._receipt_exceptions: list[BaseException] = []

    async def resolve_target(
        self,
        *,
        target_address: str | None = None,
        target_chat_jid: str | None = None,
        target_agent_name: str | None = None,
    ) -> tuple[str, SessionRecord | None]:
        """Return the canonical target address and any active local session it resolves to."""
        selection = _select_target(
            target_address=target_address,
            target_chat_jid=target_chat_jid,
            target_agent_name=target_agent_name,
        )
        if selection.is_remote:
            return selection.address, None
        return selection.address, await self._sessions.resolve(selection.address)

    async def drain_receipts(self) -> tuple[BaseException, ...]:
        """Wait for all router-owned receipt tasks and return any collected exceptions."""
        while self._receipt_tasks:
            pending = tuple(self._receipt_tasks)
            await asyncio.gather(*pending, return_exceptions=True)
        return self._consume_receipt_exceptions()

    async def shutdown_receipts(
        self,
        *,
        cancel: bool = False,
        timeout: float | None = None,
    ) -> tuple[BaseException, ...]:
        """Drain or cancel router-owned receipt tasks without shutting down runtime resources."""
        if timeout is not None and timeout <= 0:
            raise ValueError("Receipt shutdown timeout must be positive.")
        if cancel:
            await self._cancel_receipt_tasks()
            return self._consume_receipt_exceptions()
        if timeout is None:
            return await self.drain_receipts()

        deadline = self._clock() + timeout
        while self._receipt_tasks:
            remaining = deadline - self._clock()
            if remaining <= 0:
                break
            done, _ = await asyncio.wait(
                tuple(self._receipt_tasks),
                timeout=remaining,
                return_when=asyncio.FIRST_COMPLETED,
            )
            if done:
                await asyncio.gather(*done, return_exceptions=True)
        if self._receipt_tasks:
            await self._cancel_receipt_tasks()
        return self._consume_receipt_exceptions()

    async def send(
        self,
        source_session_id: str,
        content: str,
        *,
        target_address: str | None = None,
        target_chat_jid: str | None = None,
        target_agent_name: str | None = None,
        mode: DeliveryMode = "auto",
        idempotency_key: str | None = None,
        in_reply_to: str | None = None,
    ) -> ChatDispatchResult:
        """Create one delivery row, resolve its local target, and dispatch by mode.

        Rate limiting counts one new dispatch attempt after the source session and target
        selector validate, before reply lineage or target resolution. That intentionally
        counts later durable rejections consistently, while idempotent replays bypass the
        counter entirely.
        """
        if mode not in {"auto", "queue", "steer"}:
            raise ValueError(f"Unsupported delivery mode: {mode}")

        normalized_idempotency_key = (
            _require_non_blank(idempotency_key, field="Idempotency key")
            if idempotency_key is not None
            else None
        )
        await self._require_active_source_session(source_session_id)
        selection = _select_target(
            target_address=target_address,
            target_chat_jid=target_chat_jid,
            target_agent_name=target_agent_name,
        )
        if normalized_idempotency_key is None:
            retry_after = await self._reserve_dispatch_attempt(source_session_id)
            reply = await self._resolve_reply_context(
                source_session_id=source_session_id,
                in_reply_to=in_reply_to,
            )
            return await self._create_and_dispatch(
                source_session_id=source_session_id,
                content=content,
                selection=selection,
                mode=mode,
                idempotency_key=None,
                reply=reply,
                rate_limit_retry_after=retry_after,
            )

        async with self._idempotency_lock(selection.transport, normalized_idempotency_key):
            existing = await self._deliveries.find_by_idempotency(
                selection.transport,
                normalized_idempotency_key,
            )
            if existing is not None:
                return ChatDispatchResult(delivery=existing, deduped=True)
            retry_after = await self._reserve_dispatch_attempt(source_session_id)
            reply = await self._resolve_reply_context(
                source_session_id=source_session_id,
                in_reply_to=in_reply_to,
            )
            return await self._create_and_dispatch(
                source_session_id=source_session_id,
                content=content,
                selection=selection,
                mode=mode,
                idempotency_key=normalized_idempotency_key,
                reply=reply,
                rate_limit_retry_after=retry_after,
            )

    async def _create_and_dispatch(
        self,
        *,
        source_session_id: str,
        content: str,
        selection: _TargetSelection,
        mode: DeliveryMode,
        idempotency_key: str | None,
        reply: _ReplyContext,
        rate_limit_retry_after: float | None,
    ) -> ChatDispatchResult:
        claimed_delivery_id = uuid4().hex if idempotency_key is not None else None
        created = await self._deliveries.create(
            source_session_id=source_session_id,
            mode=mode,
            content=content,
            target_address=selection.address,
            delivery_id=claimed_delivery_id,
            transport=selection.transport,
            idempotency_key=idempotency_key,
            in_reply_to=reply.in_reply_to,
            ancestry=reply.ancestry,
            hop_count=reply.hop_count,
            status="pending",
        )
        if claimed_delivery_id is not None and created.delivery_id != claimed_delivery_id:
            return ChatDispatchResult(delivery=created, deduped=True)
        if rate_limit_retry_after is not None:
            await self._reject(
                created,
                code="rate_limit_exceeded",
                message="The source session exceeded the configured dispatch rate limit.",
                retry_after=rate_limit_retry_after,
            )
        if created.hop_count > self._max_hops:
            await self._reject(
                created,
                code="hop_limit_exceeded",
                message="Reply delivery exceeded the configured hop limit.",
                hop_count=created.hop_count,
                max_hops=self._max_hops,
            )
        return await self._dispatch_created(
            created,
            source_session_id=source_session_id,
            content=content,
            selection=selection,
            mode=mode,
        )

    async def _dispatch_created(
        self,
        created: DeliveryRecord,
        *,
        source_session_id: str,
        content: str,
        selection: _TargetSelection,
        mode: DeliveryMode,
    ) -> ChatDispatchResult:
        if selection.is_remote:
            await self._reject(
                created,
                code="remote_transport_unsupported",
                message="Remote chat routing is not supported yet.",
                target_address=selection.address,
                transport=selection.transport,
            )

        target = await self._sessions.resolve(selection.address)
        if target is None:
            await self._reject(
                created,
                code="target_not_found",
                message="The target session is not active.",
                target_address=selection.address,
            )

        resolved = await self._deliveries.resolve_target(created.delivery_id, target.session_id)
        await self._reject_if_delivery_cycle(resolved)
        try:
            snapshot = self._pool.snapshot(target.session_id)
        except AgentPoolError:
            await self._reject(
                resolved,
                code="target_not_active",
                message="The target session is not active.",
                target_address=selection.address,
            )

        if mode == "auto":
            try:
                handle = await self._runtime.submit_prompt(target.session_id, content)
            except Exception:
                await self._fail(
                    resolved,
                    code="dispatch_failed",
                    message="The target session could not be dispatched.",
                    target_address=selection.address,
                )

            dispatched = await self._deliveries.update_status(
                resolved.delivery_id,
                status="dispatched",
            )
            self._spawn_auto_receipt_task(dispatched, handle)
            return ChatDispatchResult(delivery=dispatched, run_id=handle.run_id)

        if mode == "queue":
            try:
                queued = await self._runtime.enqueue(
                    target.session_id,
                    content,
                    queue_kind="follow_up",
                    source_session_id=source_session_id,
                )
            except Exception:
                await self._fail(
                    resolved,
                    code="queue_failed",
                    message="The target session could not accept the queued message.",
                    target_address=selection.address,
                )

            accepted = await self._deliveries.update_status(
                resolved.delivery_id,
                status="accepted",
            )
            return ChatDispatchResult(delivery=accepted, queue_id=queued.queue_id)

        current_run_id = snapshot.current_run_id
        if current_run_id is None:
            await self._reject(
                resolved,
                code="target_not_running",
                message="The target session is not running.",
                target_address=selection.address,
            )

        try:
            queued = await self._runtime.steer(
                current_run_id,
                content,
                source_session_id=source_session_id,
            )
        except Exception:
            await self._fail(
                resolved,
                code="steer_failed",
                message="The target session could not accept the steering message.",
                target_address=selection.address,
            )

        if queued.consumed_at is not None:
            updated = await self._deliveries.update_status(
                resolved.delivery_id,
                status="completed",
            )
        else:
            updated = await self._deliveries.update_status(
                resolved.delivery_id,
                status="accepted",
            )
        return ChatDispatchResult(
            delivery=updated,
            run_id=current_run_id,
            queue_id=queued.queue_id,
        )

    @asynccontextmanager
    async def _idempotency_lock(
        self,
        transport: str,
        idempotency_key: str,
    ) -> AsyncIterator[None]:
        registry_key = (transport, idempotency_key)
        async with self._idempotency_registry_lock:
            entry = self._idempotency_locks.get(registry_key)
            if entry is None:
                entry = _IdempotencyLockState(lock=asyncio.Lock())
                self._idempotency_locks[registry_key] = entry
            entry.users += 1
        await entry.lock.acquire()
        try:
            yield
        finally:
            entry.lock.release()
            async with self._idempotency_registry_lock:
                entry.users -= 1
                current = self._idempotency_locks.get(registry_key)
                if entry.users == 0 and current is entry and not entry.lock.locked():
                    self._idempotency_locks.pop(registry_key, None)

    async def _resolve_reply_context(
        self,
        *,
        source_session_id: str,
        in_reply_to: str | None,
    ) -> _ReplyContext:
        if in_reply_to is None:
            return _ReplyContext()
        parent_delivery_id = _require_non_blank(in_reply_to, field="Reply delivery id")
        parent = await self._deliveries.get(parent_delivery_id)
        if parent is None:
            raise ValueError(f"Reply parent delivery does not exist: {parent_delivery_id}")
        if parent.target_session_id != source_session_id:
            raise ValueError("Reply source session must match the parent delivery target session.")
        ancestry = (*parent.ancestry, parent.delivery_id)
        return _ReplyContext(
            in_reply_to=parent.delivery_id,
            ancestry=ancestry,
            hop_count=len(ancestry),
        )

    async def _load_ancestry_deliveries(
        self,
        delivery: DeliveryRecord,
    ) -> tuple[DeliveryRecord, ...]:
        if delivery.hop_count != len(delivery.ancestry):
            await self._reject(
                delivery,
                code="invalid_ancestry",
                message="Reply ancestry is malformed.",
            )
        if delivery.in_reply_to is None:
            if delivery.ancestry:
                await self._reject(
                    delivery,
                    code="invalid_ancestry",
                    message="Reply ancestry is malformed.",
                )
            return ()

        expected_ancestry: tuple[str, ...] = ()
        ancestors: list[DeliveryRecord] = []
        for ancestor_delivery_id in delivery.ancestry:
            ancestor = await self._deliveries.get(ancestor_delivery_id)
            if ancestor is None:
                await self._reject(
                    delivery,
                    code="invalid_ancestry",
                    message="Reply ancestry references a missing delivery.",
                    missing_delivery_id=ancestor_delivery_id,
                )
            if ancestor.ancestry != expected_ancestry:
                await self._reject(
                    delivery,
                    code="invalid_ancestry",
                    message="Reply ancestry chain is malformed.",
                    ancestor_delivery_id=ancestor.delivery_id,
                )
            ancestors.append(ancestor)
            expected_ancestry = (*expected_ancestry, ancestor.delivery_id)

        if not ancestors or ancestors[-1].delivery_id != delivery.in_reply_to:
            await self._reject(
                delivery,
                code="invalid_ancestry",
                message="Reply ancestry must end with the parent delivery.",
                in_reply_to=delivery.in_reply_to,
            )
        return tuple(ancestors)

    async def _reject_if_delivery_cycle(self, delivery: DeliveryRecord) -> None:
        if delivery.target_session_id is None or not delivery.ancestry:
            return
        for ancestor in await self._load_ancestry_deliveries(delivery):
            if ancestor.target_session_id is None:
                await self._reject(
                    delivery,
                    code="invalid_ancestry",
                    message="Reply ancestry includes an unresolved ancestor delivery.",
                    ancestor_delivery_id=ancestor.delivery_id,
                )
            if ancestor.target_session_id == delivery.target_session_id:
                await self._reject(
                    delivery,
                    code="delivery_cycle",
                    message="Reply delivery would revisit a previous target session.",
                    target_session_id=delivery.target_session_id,
                    ancestor_delivery_id=ancestor.delivery_id,
                )

    async def _require_active_source_session(self, source_session_id: str) -> SessionRecord:
        source = await self._sessions.resolve(f"session:{source_session_id}")
        if source is None:
            raise ValueError("Source session must exist and be active.")
        try:
            self._pool.snapshot(source.session_id)
        except AgentPoolError:
            raise ValueError("Source session must exist and be active.") from None
        return source

    async def _reserve_dispatch_attempt(self, source_session_id: str) -> float | None:
        state = await self._source_rate_limit_state(source_session_id)
        async with state.lock:
            now = self._clock()
            window_start = now - self._rate_window_seconds
            while state.attempts and state.attempts[0] <= window_start:
                state.attempts.popleft()
            if len(state.attempts) >= self._max_deliveries_per_window:
                return max(0.0, state.attempts[0] + self._rate_window_seconds - now)
            state.attempts.append(now)
            return None

    async def _source_rate_limit_state(self, source_session_id: str) -> _SourceRateLimitState:
        async with self._rate_limit_registry_lock:
            state = self._rate_limit_states.get(source_session_id)
            if state is None:
                state = _SourceRateLimitState(lock=asyncio.Lock(), attempts=deque())
                self._rate_limit_states[source_session_id] = state
            return state

    def _spawn_auto_receipt_task(
        self,
        delivery: DeliveryRecord,
        handle: DurableRunHandle,
    ) -> None:
        task = asyncio.create_task(
            self._await_auto_receipt(delivery, handle),
            name=(
                f"tau-web-chat-receipt:{delivery.target_session_id or 'unknown'}:"
                f"{delivery.delivery_id}"
            ),
        )
        self._receipt_tasks.add(task)
        task.add_done_callback(self._on_receipt_task_done)

    async def _await_auto_receipt(
        self,
        delivery: DeliveryRecord,
        handle: DurableRunHandle,
    ) -> None:
        run = await handle.wait()
        if run.status == "completed":
            await self._deliveries.update_status(delivery.delivery_id, status="completed")
            return
        if run.status in {"cancelled", "failed", "interrupted"}:
            await self._deliveries.update_status(
                delivery.delivery_id,
                status="failed",
                error=_target_run_error(run, target_address=delivery.target_address),
            )
            return
        raise RuntimeError(f"Unexpected target run status for receipt handling: {run.status}")

    def _on_receipt_task_done(self, task: asyncio.Task[None]) -> None:
        self._receipt_tasks.discard(task)
        try:
            exception = task.exception()
        except asyncio.CancelledError:
            return
        if exception is not None:
            self._receipt_exceptions.append(exception)

    async def _cancel_receipt_tasks(self) -> None:
        pending = tuple(self._receipt_tasks)
        if not pending:
            return
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

    def _consume_receipt_exceptions(self) -> tuple[BaseException, ...]:
        exceptions = tuple(self._receipt_exceptions)
        self._receipt_exceptions.clear()
        return exceptions

    async def _reject(
        self,
        delivery: DeliveryRecord,
        *,
        code: str,
        message: str,
        **details: JSONValue,
    ) -> Never:
        rejected = await self._deliveries.update_status(
            delivery.delivery_id,
            status="rejected",
            error=_error_payload(code, message, **details),
        )
        raise ChatRoutingError(rejected)

    async def _fail(
        self,
        delivery: DeliveryRecord,
        *,
        code: str,
        message: str,
        **details: JSONValue,
    ) -> Never:
        failed = await self._deliveries.update_status(
            delivery.delivery_id,
            status="failed",
            error=_error_payload(code, message, **details),
        )
        raise ChatRoutingError(failed)


def _select_target(
    *,
    target_address: str | None,
    target_chat_jid: str | None,
    target_agent_name: str | None,
) -> _TargetSelection:
    selectors: list[tuple[str, _TargetSelection]] = []

    if target_agent_name is not None and target_agent_name.strip():
        selectors.append(("target_agent_name", _agent_name_selection(target_agent_name)))
    if target_chat_jid is not None and target_chat_jid.strip():
        selectors.append(("target_chat_jid", _chat_jid_selection(target_chat_jid)))
    if target_address is not None and target_address.strip():
        selectors.append(("target_address", _address_selection(target_address)))

    if len(selectors) != 1:
        provided = ", ".join(name for name, _ in selectors) or "none"
        raise ValueError(f"Exactly one non-blank target selector is required; received {provided}.")

    return selectors[0][1]


def _agent_name_selection(value: str) -> _TargetSelection:
    return _TargetSelection(
        address=f"@{validate_agent_name(value)}",
        transport="local",
        is_remote=False,
    )


def _chat_jid_selection(value: str) -> _TargetSelection:
    chat_jid = _canonical_chat_jid_value(value)
    return _TargetSelection(
        address=f"chat_jid:{chat_jid}",
        transport="local",
        is_remote=False,
    )


def _address_selection(value: str) -> _TargetSelection:
    address = _require_non_blank(value, field="Target address")
    if "!" not in address:
        return _TargetSelection(
            address=_canonical_local_address(address),
            transport="local",
            is_remote=False,
        )
    if address.count("!") != 1:
        raise ValueError("Target address must contain at most one transport hop.")
    raw_transport, _, raw_destination = address.partition("!")
    transport = _non_blank(raw_transport) or "remote"
    destination = _canonical_local_address(
        _require_non_blank(raw_destination, field="Remote target address")
    )
    return _TargetSelection(
        address=f"{transport}!{destination}",
        transport=transport,
        is_remote=True,
    )


def _canonical_local_address(value: str) -> str:
    normalized = _require_non_blank(value, field="Target address")
    if normalized.startswith("@"):
        return f"@{validate_agent_name(normalized)}"
    if normalized.startswith("chat_jid:"):
        return f"chat_jid:{_canonical_chat_jid_value(normalized)}"
    if normalized.startswith("session:"):
        session_id = _require_non_blank(normalized.removeprefix("session:"), field="Session id")
        return f"session:{session_id}"
    return normalized


def _canonical_chat_jid_value(value: str) -> str:
    normalized = _require_non_blank(value, field="Chat JID")
    if normalized.startswith("chat_jid:"):
        normalized = normalized.removeprefix("chat_jid:")
    return _require_non_blank(normalized, field="Chat JID")


def _require_non_blank(value: str, *, field: str) -> str:
    normalized = _non_blank(value)
    if normalized is None:
        raise ValueError(f"{field} must be non-blank.")
    return normalized


def _non_blank(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized if normalized else None


def _error_payload(code: str, message: str, **details: JSONValue) -> JSONObject:
    payload: JSONObject = {
        "code": code,
        "message": message,
    }
    if details:
        payload["details"] = details
    return payload


def _target_run_error(run: RunRecord, *, target_address: str | None) -> JSONObject:
    details: dict[str, JSONValue] = {
        "run_id": run.run_id,
        "target_session_id": run.session_id,
    }
    if target_address is not None:
        details["target_address"] = target_address
    if run.error is not None:
        details["run_error"] = run.error

    if run.status == "cancelled":
        return _error_payload("target_run_cancelled", "The target run was cancelled.", **details)
    if run.status == "failed":
        return _error_payload("target_run_failed", "The target run failed.", **details)
    if run.status == "interrupted":
        return _error_payload(
            "target_run_interrupted", "The target run was interrupted.", **details
        )
    raise ValueError(f"Target run status {run.status!r} does not map to a delivery failure.")


def _object_or_empty(value: JSONValue | None) -> JSONObject:
    if value is None:
        return {}
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return value
    return {}


def _default_clock() -> float:
    try:
        return asyncio.get_running_loop().time()
    except RuntimeError:
        return monotonic()
