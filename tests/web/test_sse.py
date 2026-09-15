from __future__ import annotations

import asyncio
from uuid import UUID

import pytest

from tau_agent import (
    AgentEndEvent,
    AgentEvent,
    ErrorEvent,
    MessageDeltaEvent,
    MessageEndEvent,
    ThinkingDeltaEvent,
    ToolExecutionUpdateEvent,
    TurnEndEvent,
    UserMessage,
)
from tau_web.baseline_extensions.meters import METERS_EVENT_TYPE
from tau_web.events import WebEventEnvelope, build_invalidation_envelope, build_web_event_envelope
from tau_web.sse import GLOBAL_EVENT_SESSION_ID, BrokerEvent, EventBroker


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _envelope(
    event: AgentEvent,
    *,
    session_id: str = "alpha",
    run_id: str = "run-1",
    sequence: int,
) -> WebEventEnvelope:
    return build_web_event_envelope(
        session_id=session_id,
        run_id=run_id,
        sequence=sequence,
        event=event,
        event_id=UUID(int=sequence),
        created_at=f"2025-01-01T00:00:{sequence:02d}+00:00",
    )


@pytest.mark.anyio
async def test_event_broker_replays_retained_events_and_filters_by_session() -> None:
    broker = EventBroker(replay_capacity=4, subscriber_capacity=4)

    alpha_start = await broker.publish(_envelope(MessageDeltaEvent(delta="alpha-1"), sequence=1))
    await broker.publish(
        _envelope(MessageDeltaEvent(delta="beta-1"), session_id="beta", run_id="run-2", sequence=1)
    )
    alpha_end = await broker.publish(_envelope(TurnEndEvent(turn=1), sequence=2))

    subscription, replay = broker.subscribe(session_id="alpha", last_event_id=0)

    assert replay.snapshot_required is False
    assert replay.cursor == alpha_end.cursor
    assert replay.events == (alpha_start, alpha_end)
    assert await subscription.next(timeout=0.0) is None


@pytest.mark.anyio
async def test_event_broker_stale_detection_respects_session_filter_and_ahead_cursors() -> None:
    broker = EventBroker(replay_capacity=2, subscriber_capacity=2)

    await broker.publish(
        _envelope(MessageDeltaEvent(delta="beta-1"), session_id="beta", run_id="run-2", sequence=1)
    )
    await broker.publish(
        _envelope(MessageDeltaEvent(delta="beta-2"), session_id="beta", run_id="run-2", sequence=2)
    )
    alpha_subscription, alpha_replay = broker.subscribe(session_id="alpha", last_event_id=0)

    assert alpha_replay.snapshot_required is False
    assert alpha_replay.events == ()
    assert alpha_replay.cursor == broker.cursor
    assert await alpha_subscription.next(timeout=0.0) is None

    await broker.publish(_envelope(MessageDeltaEvent(delta="alpha-1"), sequence=1))
    await broker.publish(_envelope(MessageDeltaEvent(delta="alpha-2"), sequence=2))
    await broker.publish(_envelope(MessageDeltaEvent(delta="alpha-3"), sequence=3))

    stale_subscription, stale_replay = broker.subscribe(session_id="alpha", last_event_id=0)

    assert stale_replay.snapshot_required is True
    assert stale_replay.events == ()
    assert stale_replay.cursor == broker.cursor
    assert await stale_subscription.next(timeout=0.0) is None

    ahead_subscription, ahead_replay = broker.subscribe(
        session_id="alpha",
        last_event_id=broker.cursor + 1,
    )

    assert ahead_replay.snapshot_required is True
    assert ahead_replay.events == ()
    assert ahead_replay.cursor == broker.cursor
    assert await ahead_subscription.next(timeout=0.0) is None


@pytest.mark.anyio
async def test_event_broker_coalesces_low_priority_deltas_and_tool_updates_when_full() -> None:
    broker = EventBroker(replay_capacity=8, subscriber_capacity=1)

    delta_subscription, _ = broker.subscribe(session_id="alpha")
    await broker.publish(_envelope(MessageDeltaEvent(delta="hel"), sequence=1))
    await broker.publish(_envelope(MessageDeltaEvent(delta="lo"), sequence=2))

    merged_delta = await delta_subscription.next(timeout=0.1)

    assert merged_delta is not None
    assert merged_delta.cursor == broker.cursor
    assert merged_delta.envelope.payload["type"] == "message_delta"
    assert merged_delta.envelope.payload["delta"] == "hello"
    assert await delta_subscription.next(timeout=0.0) is None

    tool_subscription, _ = broker.subscribe(session_id="alpha", last_event_id=broker.cursor)
    await broker.publish(
        _envelope(
            ToolExecutionUpdateEvent(tool_call_id="call-1", message="reading", data={"bytes": 1}),
            sequence=3,
        )
    )
    latest_tool_update = await broker.publish(
        _envelope(
            ToolExecutionUpdateEvent(tool_call_id="call-1", message="done", data={"bytes": 2}),
            sequence=4,
        )
    )

    merged_tool = await tool_subscription.next(timeout=0.1)

    assert merged_tool == latest_tool_update
    assert merged_tool.envelope.payload["message"] == "done"
    assert merged_tool.envelope.payload["data"] == {"bytes": 2}
    assert await tool_subscription.next(timeout=0.0) is None


@pytest.mark.anyio
async def test_event_broker_evicts_oldest_low_and_marks_high_only_overflow() -> None:
    broker = EventBroker(replay_capacity=8, subscriber_capacity=2)

    subscription, _ = broker.subscribe(session_id="alpha")
    first_low = await broker.publish(_envelope(MessageDeltaEvent(delta="a"), sequence=1))
    high_message_end = await broker.publish(
        _envelope(MessageEndEvent(message=UserMessage(content="done")), sequence=2)
    )
    high_agent_end = await broker.publish(_envelope(AgentEndEvent(), sequence=3))

    first_delivered = await subscription.next(timeout=0.1)
    second_delivered = await subscription.next(timeout=0.1)

    assert first_delivered != first_low
    assert first_delivered == high_message_end
    assert second_delivered == high_agent_end
    assert await subscription.next(timeout=0.0) is None

    overflow_broker = EventBroker(replay_capacity=8, subscriber_capacity=1)
    overflow_subscription, _ = overflow_broker.subscribe(session_id="alpha")
    first_high = await overflow_broker.publish(_envelope(ErrorEvent(message="boom"), sequence=4))
    await overflow_broker.publish(_envelope(TurnEndEvent(turn=2), sequence=5))
    assert overflow_subscription.closed is True
    assert overflow_subscription.overflowed is True
    assert await overflow_subscription.next(timeout=0.1) == first_high
    assert await overflow_subscription.next(timeout=0.0) is None


@pytest.mark.anyio
async def test_slow_subscriber_never_blocks_other_subscribers() -> None:
    broker = EventBroker(replay_capacity=8, subscriber_capacity=1)

    slow_subscription, _ = broker.subscribe(session_id="alpha")
    fast_subscription, _ = broker.subscribe(session_id="alpha")

    first_high = await broker.publish(_envelope(ErrorEvent(message="first"), sequence=1))
    assert await fast_subscription.next(timeout=0.1) == first_high

    second_high = await broker.publish(_envelope(AgentEndEvent(), sequence=2))

    assert slow_subscription.closed is True
    assert slow_subscription.overflowed is True
    assert await fast_subscription.next(timeout=0.1) == second_high
    assert await slow_subscription.next(timeout=0.1) == first_high
    assert await slow_subscription.next(timeout=0.0) is None
    assert await fast_subscription.next(timeout=0.0) is None


@pytest.mark.anyio
async def test_event_broker_delivers_global_meter_events_to_all_subscriptions_and_replay() -> None:
    broker = EventBroker(replay_capacity=4, subscriber_capacity=4)
    global_envelope = build_invalidation_envelope(
        event_type=METERS_EVENT_TYPE,
        session_id=GLOBAL_EVENT_SESSION_ID,
        payload={"cpu_percent": 12.5},
    )

    all_subscription, _ = broker.subscribe()
    alpha_subscription, _ = broker.subscribe(session_id="alpha")
    beta_subscription, _ = broker.subscribe(session_id="beta")

    published = await broker.publish(global_envelope)

    assert (await all_subscription.next(timeout=0.1)) == published
    assert (await alpha_subscription.next(timeout=0.1)) == published
    assert (await beta_subscription.next(timeout=0.1)) == published

    replay_subscription, replay = broker.subscribe(session_id="alpha", last_event_id=0)

    assert replay.snapshot_required is False
    assert replay.events == (published,)
    assert replay.events[0].envelope.session_id == GLOBAL_EVENT_SESSION_ID
    assert await replay_subscription.next(timeout=0.0) is None


@pytest.mark.anyio
async def test_event_broker_marks_session_replay_stale_after_global_event_drops() -> None:
    broker = EventBroker(replay_capacity=1, subscriber_capacity=2)
    await broker.publish(
        build_invalidation_envelope(
            event_type=METERS_EVENT_TYPE,
            session_id=GLOBAL_EVENT_SESSION_ID,
            payload={"cpu_percent": 10.0},
        )
    )
    await broker.publish(_envelope(TurnEndEvent(turn=1), session_id="beta", sequence=1))

    subscription, replay = broker.subscribe(session_id="alpha", last_event_id=0)

    assert replay.snapshot_required is True
    assert replay.events == ()
    assert await subscription.next(timeout=0.0) is None


@pytest.mark.anyio
async def test_event_broker_coalesces_global_meter_events_when_full() -> None:
    broker = EventBroker(replay_capacity=8, subscriber_capacity=1)
    subscription, _ = broker.subscribe(session_id="alpha")

    first = await broker.publish(
        build_invalidation_envelope(
            event_type=METERS_EVENT_TYPE,
            session_id=GLOBAL_EVENT_SESSION_ID,
            payload={"cpu_percent": 10.0},
        )
    )
    latest = await broker.publish(
        build_invalidation_envelope(
            event_type=METERS_EVENT_TYPE,
            session_id=GLOBAL_EVENT_SESSION_ID,
            payload={"cpu_percent": 20.0},
        )
    )

    delivered = await subscription.next(timeout=0.1)

    assert delivered is not None
    assert delivered != first
    assert delivered == latest
    assert delivered.envelope.type == METERS_EVENT_TYPE
    assert delivered.envelope.payload == {"cpu_percent": 20.0}
    assert await subscription.next(timeout=0.0) is None


@pytest.mark.anyio
async def test_event_broker_close_wakes_waiters_and_timeout_returns_none() -> None:
    broker = EventBroker(replay_capacity=2, subscriber_capacity=1)
    subscription, _ = broker.subscribe(session_id="alpha")

    assert await subscription.next(timeout=0.0) is None

    waiter = asyncio.create_task(subscription.next(timeout=60.0))
    await asyncio.sleep(0)

    broker.close()

    assert await asyncio.wait_for(waiter, timeout=1.0) is None
    assert subscription.closed is True
    assert broker.closed is True


def test_broker_event_rejects_non_positive_cursors() -> None:
    with pytest.raises(ValueError, match="positive"):
        BrokerEvent(
            cursor=0,
            envelope=_envelope(ThinkingDeltaEvent(delta="x"), sequence=1),
        )
