from __future__ import annotations

import asyncio
from uuid import UUID

import pytest

from tau_agent import (
    ErrorEvent,
    MessageDeltaEvent,
    ThinkingDeltaEvent,
    ToolExecutionUpdateEvent,
    TurnEndEvent,
)
from tau_web.events import WebEventEnvelope, build_invalidation_envelope, build_web_event_envelope
from tau_web.sse import GLOBAL_EVENT_SESSION_ID, EventBroker, EventSubscription


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _envelope(
    *,
    event_id_seed: int,
    session_id: str,
    run_id: str,
    sequence: int,
    event: MessageDeltaEvent
    | ThinkingDeltaEvent
    | ToolExecutionUpdateEvent
    | TurnEndEvent
    | ErrorEvent,
) -> WebEventEnvelope:
    return build_web_event_envelope(
        session_id=session_id,
        run_id=run_id,
        sequence=sequence,
        event=event,
        event_id=UUID(int=event_id_seed),
    )


@pytest.mark.anyio
async def test_event_broker_async_load_smoke_never_blocks_and_keeps_subscriptions_bounded() -> None:
    subscriber_capacity = 2
    broker = EventBroker(replay_capacity=128, subscriber_capacity=subscriber_capacity)

    draining_subscription, _ = broker.subscribe(session_id="gamma")

    slow_alpha: list[EventSubscription] = [
        broker.subscribe(session_id="alpha")[0] for _ in range(12)
    ]
    slow_beta: list[EventSubscription] = [broker.subscribe(session_id="beta")[0] for _ in range(10)]
    slow_all: list[EventSubscription] = [broker.subscribe()[0] for _ in range(10)]

    total_subscribers = 1 + len(slow_alpha) + len(slow_beta) + len(slow_all)
    assert total_subscribers >= 32

    stop_draining = asyncio.Event()
    drained_events = []

    async def drain_active_subscription() -> None:
        while True:
            next_event = await draining_subscription.next(timeout=0.05)
            if next_event is None:
                if stop_draining.is_set() or draining_subscription.closed:
                    return
                continue
            drained_events.append(next_event)

    drain_task = asyncio.create_task(drain_active_subscription())

    sequence_by_session = {"alpha": 0, "beta": 0, "gamma": 0}
    next_event_id_seed = 0

    def next_sequence(session_id: str) -> int:
        sequence_by_session[session_id] += 1
        return sequence_by_session[session_id]

    def allocate_event_id_seed() -> int:
        nonlocal next_event_id_seed
        next_event_id_seed += 1
        return next_event_id_seed

    async def publish_workload() -> tuple[int, object, object]:
        published_count = 0

        first_high = await broker.publish(
            _envelope(
                event_id_seed=allocate_event_id_seed(),
                session_id="alpha",
                run_id="run-alpha",
                sequence=next_sequence("alpha"),
                event=ErrorEvent(message="alpha-high-1"),
            )
        )
        second_high = await broker.publish(
            _envelope(
                event_id_seed=allocate_event_id_seed(),
                session_id="alpha",
                run_id="run-alpha",
                sequence=next_sequence("alpha"),
                event=TurnEndEvent(turn=1),
            )
        )
        await broker.publish(
            _envelope(
                event_id_seed=allocate_event_id_seed(),
                session_id="alpha",
                run_id="run-alpha",
                sequence=next_sequence("alpha"),
                event=ErrorEvent(message="alpha-high-2"),
            )
        )
        published_count += 3

        for index in range(2_000):
            selector = index % 6
            if selector == 0:
                envelope = _envelope(
                    event_id_seed=allocate_event_id_seed(),
                    session_id="gamma",
                    run_id="run-gamma",
                    sequence=next_sequence("gamma"),
                    event=MessageDeltaEvent(delta=f"gamma-{index}"),
                )
            elif selector == 1:
                envelope = _envelope(
                    event_id_seed=allocate_event_id_seed(),
                    session_id="beta",
                    run_id="run-beta",
                    sequence=next_sequence("beta"),
                    event=ThinkingDeltaEvent(delta=f"beta-{index}"),
                )
            elif selector == 2:
                envelope = _envelope(
                    event_id_seed=allocate_event_id_seed(),
                    session_id="alpha",
                    run_id="run-alpha",
                    sequence=next_sequence("alpha"),
                    event=ToolExecutionUpdateEvent(
                        tool_call_id="tool-alpha",
                        message=f"step-{index}",
                        data={"index": index},
                    ),
                )
            elif selector == 3:
                envelope = _envelope(
                    event_id_seed=allocate_event_id_seed(),
                    session_id="gamma",
                    run_id="run-gamma",
                    sequence=next_sequence("gamma"),
                    event=TurnEndEvent(turn=index + 2),
                )
            elif selector == 4:
                envelope = build_invalidation_envelope(
                    event_type="tau.dashboard.updated",
                    session_id=GLOBAL_EVENT_SESSION_ID,
                    payload={"revision": index},
                )
            else:
                envelope = _envelope(
                    event_id_seed=allocate_event_id_seed(),
                    session_id="alpha",
                    run_id="run-alpha",
                    sequence=next_sequence("alpha"),
                    event=ErrorEvent(message=f"alpha-error-{index}"),
                )

            await broker.publish(envelope)
            published_count += 1
            await asyncio.sleep(0)

        return published_count, first_high, second_high

    published_count, first_high, second_high = await asyncio.wait_for(
        publish_workload(), timeout=5.0
    )

    stop_draining.set()
    await asyncio.wait_for(drain_task, timeout=1.0)

    assert broker.cursor == published_count

    overflow_subscription = slow_alpha[0]
    assert overflow_subscription.closed is True
    assert overflow_subscription.overflowed is True
    assert await overflow_subscription.next(timeout=0.1) == first_high
    assert await overflow_subscription.next(timeout=0.1) == second_high
    assert await overflow_subscription.next(timeout=0.0) is None

    assert draining_subscription.closed is False
    assert drained_events

    received_cursors = [event.cursor for event in drained_events]
    assert received_cursors == sorted(received_cursors)
    assert len(set(received_cursors)) == len(received_cursors)

    received_session_ids = {event.envelope.session_id for event in drained_events}
    assert received_session_ids <= {"gamma", GLOBAL_EVENT_SESSION_ID}
    assert "gamma" in received_session_ids
    assert GLOBAL_EVENT_SESSION_ID in received_session_ids

    remaining_subscriptions: list[tuple[EventSubscription, str | None]] = [
        *((subscription, "alpha") for subscription in slow_alpha[1:]),
        *((subscription, "beta") for subscription in slow_beta),
        *((subscription, None) for subscription in slow_all),
    ]

    for subscription, expected_session in remaining_subscriptions:
        pending_events = 0
        while True:
            event = await subscription.next(timeout=0.0)
            if event is None:
                break
            pending_events += 1
            if expected_session is not None:
                assert event.envelope.session_id in {expected_session, GLOBAL_EVENT_SESSION_ID}

        assert pending_events <= subscriber_capacity
