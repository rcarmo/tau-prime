"""Core SSE event broker primitives for Tau Web."""

from __future__ import annotations

import asyncio
from collections import deque
from contextlib import suppress
from dataclasses import dataclass, field, replace

from tau_agent.types import JSONObject
from tau_web.events import WebEventEnvelope

GLOBAL_EVENT_SESSION_ID = "__tau_global__"
"""Internal pseudo-session id for host-wide events such as meters updates."""

_LOW_EVENT_TYPES = frozenset(
    {
        "message_delta",
        "thinking_delta",
        "tool_execution_update",
        "tau.meters.updated",
        "tau.dashboard.updated",
    }
)
_DELTA_EVENT_TYPES = frozenset({"message_delta", "thinking_delta"})


@dataclass(frozen=True, slots=True)
class BrokerEvent:
    """One broker-assigned cursor paired with its immutable web envelope."""

    cursor: int
    envelope: WebEventEnvelope

    def __post_init__(self) -> None:
        if self.cursor <= 0:
            raise ValueError("Broker cursor must be positive")


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """Initial replay snapshot returned alongside a live subscription."""

    events: tuple[BrokerEvent, ...]
    snapshot_required: bool
    cursor: int

    def __post_init__(self) -> None:
        if self.cursor < 0:
            raise ValueError("Replay cursor must be non-negative")


@dataclass(slots=True)
class _SubscriberState:
    broker: EventBroker
    session_id: str | None
    capacity: int
    queue: deque[BrokerEvent] = field(default_factory=deque)
    waiter: asyncio.Future[None] | None = None
    closed: bool = False
    overflowed: bool = False


class EventSubscription:
    """One live broker subscription with bounded per-subscriber buffering."""

    def __init__(self, state: _SubscriberState) -> None:
        self._state = state

    @property
    def broker(self) -> EventBroker:
        return self._state.broker

    @property
    def closed(self) -> bool:
        return self._state.closed

    @property
    def overflowed(self) -> bool:
        return self._state.overflowed

    async def next(self, timeout: float | None = None) -> BrokerEvent | None:
        if timeout is not None and timeout < 0:
            raise ValueError("Subscription timeout must be non-negative")

        state = self._state
        while True:
            if state.queue:
                return state.queue.popleft()
            if state.closed:
                return None
            if state.waiter is not None and not state.waiter.done():
                raise RuntimeError("Concurrent next() calls are not supported")

            waiter: asyncio.Future[None] = asyncio.get_running_loop().create_future()
            state.waiter = waiter
            try:
                if timeout is None:
                    await waiter
                else:
                    await asyncio.wait_for(waiter, timeout)
            except TimeoutError:
                if state.waiter is waiter:
                    state.waiter = None
                waiter.cancel()
                return None
            except BaseException:
                if state.waiter is waiter:
                    state.waiter = None
                waiter.cancel()
                raise
            else:
                if state.waiter is waiter:
                    state.waiter = None

    def close(self) -> None:
        self.broker._close_subscription(self._state)


class EventBroker:
    """Bounded replay and fan-out broker for canonical Tau web events."""

    def __init__(self, *, replay_capacity: int = 256, subscriber_capacity: int = 256) -> None:
        if replay_capacity < 1:
            raise ValueError("Replay capacity must be at least 1")
        if subscriber_capacity < 1:
            raise ValueError("Subscriber capacity must be at least 1")

        self._replay_capacity = replay_capacity
        self._subscriber_capacity = subscriber_capacity
        self._cursor = 0
        self._closed = False
        self._replay: deque[BrokerEvent] = deque()
        self._subscriptions: list[_SubscriberState] = []
        self._replay_drop_floor = 0
        self._global_drop_floor = 0
        self._session_drop_floors: dict[str, int] = {}

    @property
    def cursor(self) -> int:
        return self._cursor

    @property
    def closed(self) -> bool:
        return self._closed

    async def publish(self, envelope: WebEventEnvelope) -> BrokerEvent:
        if self._closed:
            raise RuntimeError("EventBroker is closed")

        self._cursor += 1
        broker_event = BrokerEvent(cursor=self._cursor, envelope=envelope)
        self._append_replay(broker_event)
        for state in tuple(self._subscriptions):
            if not _matches_session(state.session_id, envelope.session_id):
                continue
            self._enqueue(state, broker_event)
        return broker_event

    def subscribe(
        self,
        *,
        session_id: str | None = None,
        last_event_id: int | None = None,
    ) -> tuple[EventSubscription, ReplayResult]:
        if last_event_id is not None and last_event_id < 0:
            raise ValueError("Last-Event-ID must be non-negative")

        current_cursor = self._cursor
        snapshot_required = False
        replay_events: tuple[BrokerEvent, ...] = ()

        if last_event_id is not None:
            if last_event_id > current_cursor:
                snapshot_required = True
            else:
                drop_floor = self._drop_floor_for(session_id)
                if last_event_id < drop_floor:
                    snapshot_required = True
                else:
                    replay_events = tuple(
                        event
                        for event in self._replay
                        if event.cursor > last_event_id
                        and _matches_session(session_id, event.envelope.session_id)
                    )

        state = _SubscriberState(
            broker=self,
            session_id=session_id,
            capacity=self._subscriber_capacity,
            closed=self._closed,
        )
        if not self._closed:
            self._subscriptions.append(state)
        return EventSubscription(state), ReplayResult(
            events=replay_events,
            snapshot_required=snapshot_required,
            cursor=current_cursor,
        )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for state in tuple(self._subscriptions):
            self._close_state(state, remove=False)
        self._subscriptions.clear()

    def _append_replay(self, broker_event: BrokerEvent) -> None:
        if len(self._replay) >= self._replay_capacity:
            dropped = self._replay.popleft()
            self._replay_drop_floor = dropped.cursor
            session_id = dropped.envelope.session_id
            if session_id == GLOBAL_EVENT_SESSION_ID:
                self._global_drop_floor = dropped.cursor
            else:
                self._session_drop_floors[session_id] = dropped.cursor
        self._replay.append(broker_event)

    def _drop_floor_for(self, session_id: str | None) -> int:
        if session_id is None:
            return self._replay_drop_floor
        return max(
            self._global_drop_floor,
            self._session_drop_floors.get(session_id, 0),
        )

    def _enqueue(self, state: _SubscriberState, broker_event: BrokerEvent) -> None:
        if state.closed:
            return

        queue = state.queue
        if len(queue) < state.capacity:
            queue.append(broker_event)
            self._wake(state)
            return

        if _is_low_event(broker_event) and queue:
            merged = _coalesce_tail(queue[-1], broker_event)
            if merged is not None:
                queue[-1] = merged
                self._wake(state)
                return

        oldest_low_index = _oldest_low_index(queue)
        if oldest_low_index is not None:
            del queue[oldest_low_index]
            queue.append(broker_event)
            self._wake(state)
            return

        self._close_state(state, overflow=True, remove=True)

    def _close_subscription(self, state: _SubscriberState) -> None:
        self._close_state(state, remove=True)

    def _close_state(
        self,
        state: _SubscriberState,
        *,
        overflow: bool = False,
        remove: bool,
    ) -> None:
        if overflow:
            state.overflowed = True
        if state.closed and not remove:
            return

        state.closed = True
        if remove:
            with suppress(ValueError):
                self._subscriptions.remove(state)
        self._wake(state)

    def _wake(self, state: _SubscriberState) -> None:
        waiter = state.waiter
        if waiter is None or waiter.done():
            return
        state.waiter = None
        waiter.set_result(None)


def _matches_session(expected: str | None, actual: str) -> bool:
    if actual == GLOBAL_EVENT_SESSION_ID:
        return True
    return expected is None or expected == actual


def _payload_event_type(envelope: WebEventEnvelope) -> str | None:
    event_type = envelope.payload.get("type")
    if isinstance(event_type, str) and event_type:
        return event_type
    if envelope.type.startswith("tau.agent."):
        return envelope.type.removeprefix("tau.agent.")
    if envelope.type.startswith("tau."):
        return envelope.type
    return None


def _is_low_event(event: BrokerEvent) -> bool:
    event_type = _payload_event_type(event.envelope)
    return event_type in _LOW_EVENT_TYPES


def _oldest_low_index(queue: deque[BrokerEvent]) -> int | None:
    for index, event in enumerate(queue):
        if _is_low_event(event):
            return index
    return None


def _coalesce_tail(existing: BrokerEvent, incoming: BrokerEvent) -> BrokerEvent | None:
    existing_type = _payload_event_type(existing.envelope)
    incoming_type = _payload_event_type(incoming.envelope)
    if existing_type is None or existing_type != incoming_type:
        return None
    if existing_type not in _LOW_EVENT_TYPES:
        return None
    if existing.envelope.session_id != incoming.envelope.session_id:
        return None
    if existing.envelope.run_id != incoming.envelope.run_id:
        return None

    if existing_type in _DELTA_EVENT_TYPES:
        existing_delta = existing.envelope.payload.get("delta")
        incoming_delta = incoming.envelope.payload.get("delta")
        if not isinstance(existing_delta, str) or not isinstance(incoming_delta, str):
            return None
        merged_payload: JSONObject = dict(incoming.envelope.payload)
        merged_payload["delta"] = existing_delta + incoming_delta
        return BrokerEvent(
            cursor=incoming.cursor,
            envelope=replace(incoming.envelope, payload=merged_payload),
        )

    if existing_type == "tool_execution_update":
        existing_tool_call_id = existing.envelope.payload.get("tool_call_id")
        incoming_tool_call_id = incoming.envelope.payload.get("tool_call_id")
        if existing_tool_call_id != incoming_tool_call_id:
            return None
        return incoming

    if existing_type in {"tau.meters.updated", "tau.dashboard.updated"}:
        return incoming

    return None


__all__ = [
    "BrokerEvent",
    "EventBroker",
    "EventSubscription",
    "GLOBAL_EVENT_SESSION_ID",
    "ReplayResult",
]
