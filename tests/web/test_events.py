from __future__ import annotations

from pathlib import Path
from typing import cast
from uuid import UUID

import pytest

from tau_agent import (
    AgentEndEvent,
    AgentEvent,
    AgentStartEvent,
    AgentToolResult,
    AssistantMessage,
    ErrorEvent,
    MessageDeltaEvent,
    MessageEndEvent,
    MessageStartEvent,
    MessageUpdateEvent,
    QueueUpdateEvent,
    RetryEvent,
    ThinkingDeltaEvent,
    ToolCall,
    ToolExecutionEndEvent,
    ToolExecutionStartEvent,
    ToolExecutionUpdateEvent,
    ToolResultMessage,
    TurnEndEvent,
    TurnStartEvent,
    UserMessage,
)
from tau_agent.provider_events import TextDeltaEvent as ProviderTextDeltaEvent
from tau_agent.types import JSONObject
from tau_web.events import EventProjector, WebEventEnvelope, build_web_event_envelope
from tau_web.sqlite.connection import SqliteDatabase
from tau_web.sqlite.repositories import TimelineMessageRepository
from tau_web.sqlite.sessions import SessionRepository


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def _create_session(database: SqliteDatabase, tmp_path: Path, session_id: str) -> None:
    await SessionRepository(database).create(
        workspace_root=tmp_path,
        provider_name="test",
        model="model",
        agent_name=session_id,
        session_id=session_id,
    )


def _payload_for(event: AgentEvent) -> JSONObject:
    payload = event.model_dump(mode="json")
    assert isinstance(payload, dict)
    return cast(JSONObject, payload)


_TOOL_CALL = ToolCall(id="call-1", name="read", arguments={"path": "README.md"})
_TOOL_RESULT = AgentToolResult(
    tool_call_id="call-1",
    name="read",
    ok=True,
    content="contents",
    data={"path": "README.md"},
)
_PARTIAL_MESSAGE = AssistantMessage(content="partial")

_EVENT_CASES = [
    pytest.param(AgentStartEvent(), "tau.agent.agent_start", id="agent-start"),
    pytest.param(AgentEndEvent(), "tau.agent.agent_end", id="agent-end"),
    pytest.param(TurnStartEvent(turn=2), "tau.agent.turn_start", id="turn-start"),
    pytest.param(TurnEndEvent(turn=2), "tau.agent.turn_end", id="turn-end"),
    pytest.param(
        RetryEvent(
            attempt=2,
            max_attempts=3,
            delay_seconds=1.25,
            message="retrying",
            data={"status_code": 503},
        ),
        "tau.agent.retry",
        id="retry",
    ),
    pytest.param(
        QueueUpdateEvent(steering=("adjust",), follow_up=("continue",)),
        "tau.agent.queue_update",
        id="queue-update",
    ),
    pytest.param(
        MessageStartEvent(message_role="tool"),
        "tau.agent.message_start",
        id="message-start",
    ),
    pytest.param(
        MessageUpdateEvent(
            message=_PARTIAL_MESSAGE,
            assistant_message_event=ProviderTextDeltaEvent(
                content_index=1,
                delta="hi",
                partial=_PARTIAL_MESSAGE,
            ),
        ),
        "tau.agent.message_update",
        id="message-update",
    ),
    pytest.param(
        MessageDeltaEvent(delta="hello"),
        "tau.agent.message_delta",
        id="message-delta",
    ),
    pytest.param(
        ThinkingDeltaEvent(delta="reasoning"),
        "tau.agent.thinking_delta",
        id="thinking-delta",
    ),
    pytest.param(
        MessageEndEvent(
            message=ToolResultMessage(
                tool_call_id="call-1",
                name="read",
                content="done",
                ok=True,
            )
        ),
        "tau.agent.message_end",
        id="message-end",
    ),
    pytest.param(
        ToolExecutionStartEvent(tool_call=_TOOL_CALL),
        "tau.agent.tool_execution_start",
        id="tool-execution-start",
    ),
    pytest.param(
        ToolExecutionUpdateEvent(
            tool_call_id="call-1",
            message="reading",
            data={"bytes": 12},
        ),
        "tau.agent.tool_execution_update",
        id="tool-execution-update",
    ),
    pytest.param(
        ToolExecutionEndEvent(result=_TOOL_RESULT),
        "tau.agent.tool_execution_end",
        id="tool-execution-end",
    ),
    pytest.param(
        ErrorEvent(message="boom", recoverable=True, data={"source": "provider"}),
        "tau.agent.error",
        id="error",
    ),
]


@pytest.mark.parametrize(("event", "expected_type"), _EVENT_CASES)
def test_build_web_event_envelope_preserves_agent_event_identity_and_payload(
    event: AgentEvent,
    expected_type: str,
) -> None:
    event_id = UUID("00000000-0000-0000-0000-000000000123")
    created_at = "2025-01-02T03:04:05+00:00"

    envelope = build_web_event_envelope(
        session_id="session-1",
        run_id="run-1",
        sequence=7,
        event=event,
        event_id=event_id,
        created_at=created_at,
    )

    assert envelope == WebEventEnvelope(
        event_id=event_id,
        type=expected_type,
        session_id="session-1",
        run_id="run-1",
        sequence=7,
        payload=_payload_for(event),
        created_at=created_at,
    )


@pytest.mark.anyio
async def test_event_projector_persists_message_end_idempotently_and_isolates_sessions(
    tmp_path: Path,
) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        await _create_session(database, tmp_path, "alpha")
        await _create_session(database, tmp_path, "beta")
        timeline = TimelineMessageRepository(database)
        projector = EventProjector(timeline)

        await projector.project(
            "alpha",
            "shared-run",
            1,
            MessageEndEvent(message=AssistantMessage(content="alpha message")),
        )
        await projector.project(
            "alpha",
            "shared-run",
            1,
            MessageEndEvent(message=AssistantMessage(content="alpha message")),
        )
        await projector.project(
            "beta",
            "shared-run",
            1,
            MessageEndEvent(message=AssistantMessage(content="beta message")),
        )

        alpha_timeline = await timeline.list(session_id="alpha")
        beta_timeline = await timeline.list(session_id="beta")

        assert [record.content for record in alpha_timeline] == ["alpha message"]
        assert [record.content for record in beta_timeline] == ["beta message"]
        assert alpha_timeline[0].public_id != beta_timeline[0].public_id


@pytest.mark.anyio
async def test_event_projector_observers_receive_envelope_without_blocking_persistence(
    tmp_path: Path,
) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        await _create_session(database, tmp_path, "alpha")
        timeline = TimelineMessageRepository(database)
        projector = EventProjector(timeline)
        observed: list[tuple[str, WebEventEnvelope, int]] = []

        async def failing_observer(envelope: WebEventEnvelope) -> None:
            observed.append(("failing", envelope, len(await timeline.list(session_id="alpha"))))
            raise RuntimeError("observer failed")

        async def healthy_observer(envelope: WebEventEnvelope) -> None:
            observed.append(("healthy", envelope, len(await timeline.list(session_id="alpha"))))

        projector.subscribe(failing_observer)
        projector.subscribe(healthy_observer)

        await projector.project(
            "alpha",
            "run-1",
            1,
            MessageEndEvent(message=UserMessage(content="hello")),
        )

        timeline_records = await timeline.list(session_id="alpha")

        assert [record.content for record in timeline_records] == ["hello"]
        assert [entry[0] for entry in observed] == ["failing", "healthy"]
        assert [entry[2] for entry in observed] == [1, 1]
        assert observed[0][1] is observed[1][1]
        assert observed[1][1].type == "tau.agent.message_end"
        assert observed[1][1].payload == {
            "type": "message_end",
            "message": {"role": "user", "content": "hello"},
        }
