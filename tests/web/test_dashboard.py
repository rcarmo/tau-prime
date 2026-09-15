from __future__ import annotations

from typing import cast

import pytest
from aiohttp.test_utils import TestClient, TestServer

from tau_agent import (
    AssistantMessage,
    MessageDeltaEvent,
    MessageEndEvent,
    ThinkingDeltaEvent,
    ToolCall,
    ToolExecutionStartEvent,
    UserMessage,
)
from tau_agent.session import LeafEntry, MessageEntry
from tau_web.app import SERVICES_KEY, create_app
from tau_web.baseline_extensions.session_dashboard import DASHBOARD_EVENT_TYPE
from tau_web.config import WebConfig
from tau_web.services import TauWebServices
from tau_web.sse import GLOBAL_EVENT_SESSION_ID


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def app_client(web_config: WebConfig) -> TestClient:
    client = TestClient(TestServer(create_app(web_config)))
    await client.start_server()
    try:
        yield client
    finally:
        await client.close()


def _services(client: TestClient) -> TauWebServices:
    return cast(TauWebServices, client.app[SERVICES_KEY])


async def _create_session(
    services: TauWebServices,
    session_id: str,
    *,
    context_window_tokens: int | None = None,
) -> None:
    metadata = (
        {"context_window_tokens": context_window_tokens}
        if context_window_tokens is not None
        else None
    )
    await services.sessions.create(
        workspace_root=services.config.cwd / session_id,
        provider_name="test",
        model=f"model-{session_id}",
        agent_name=session_id,
        title=f"Session {session_id}",
        session_id=session_id,
        metadata=metadata,
    )


@pytest.mark.anyio
async def test_dashboard_aggregates_durable_session_state(app_client: TestClient) -> None:
    services = _services(app_client)
    await _create_session(services, "alpha", context_window_tokens=1_000)
    user_entry = MessageEntry(message=UserMessage(content="hello dashboard"))
    leaf = LeafEntry(parent_id=user_entry.id, entry_id=user_entry.id)
    await services.session_storage("alpha").append_many((user_entry, leaf))
    await services.timeline.project_message_end(
        "alpha",
        run_id="run-summary",
        sequence=1,
        message=AssistantMessage(content="Latest durable assistant summary"),
        created_at="2026-08-05T01:02:03+00:00",
    )
    await services.queues.enqueue(
        "alpha",
        queue_kind="follow_up",
        content={"content": "next"},
    )

    response = await app_client.get("/dashboard")
    assert response.status == 200
    assert response.headers["Cache-Control"] == "no-store"
    payload = await response.json()

    assert payload["page"] == 1
    assert payload["page_size"] == 8
    assert payload["total"] == 1
    assert payload["total_pages"] == 1
    tile = payload["sessions"][0]
    assert tile["session_id"] == "alpha"
    assert tile["agent_name"] == "alpha"
    assert tile["title"] == "Session alpha"
    assert tile["workspace"].endswith("/alpha")
    assert tile["activity_state"] == "idle"
    assert tile["pool_state"] is None
    assert tile["preview_kind"] == "summary"
    assert tile["preview"] == "Latest durable assistant summary"
    assert tile["latest_assistant_summary"] == "Latest durable assistant summary"
    assert tile["context_used_tokens"] > 0
    assert tile["context_window_tokens"] == 1_000
    assert tile["context_percent"] > 0
    assert tile["queue_count"] == 1
    assert tile["model"] == "model-alpha"
    assert tile["has_error"] is False


@pytest.mark.anyio
async def test_dashboard_live_preview_priority_and_global_invalidation(
    app_client: TestClient,
) -> None:
    services = _services(app_client)
    await _create_session(services, "alpha")
    await _create_session(services, "beta")
    subscription, _ = services.broker.subscribe(session_id="alpha")

    await services.projector.project("beta", "run-beta", 1, ThinkingDeltaEvent(delta="think"))
    invalidation = await subscription.next(timeout=0.1)
    assert invalidation is not None
    assert invalidation.envelope.type == DASHBOARD_EVENT_TYPE
    assert invalidation.envelope.session_id == GLOBAL_EVENT_SESSION_ID
    assert invalidation.envelope.payload == {"updated_session_id": "beta"}

    await services.projector.project(
        "beta",
        "run-beta",
        2,
        ToolExecutionStartEvent(
            tool_call=ToolCall(id="call-1", name="read", arguments={"path": "README.md"})
        ),
    )
    await services.projector.project("beta", "run-beta", 3, MessageDeltaEvent(delta="draft"))

    payload = await (await app_client.get("/dashboard", params={"page_size": "8"})).json()
    beta = next(item for item in payload["sessions"] if item["session_id"] == "beta")
    assert beta["preview_kind"] == "draft"
    assert beta["preview"] == "draft"

    await services.projector.project(
        "beta",
        "run-beta",
        4,
        MessageEndEvent(message=AssistantMessage(content="saved after stream")),
    )
    payload = await (await app_client.get("/dashboard")).json()
    beta = next(item for item in payload["sessions"] if item["session_id"] == "beta")
    assert beta["preview_kind"] == "summary"
    assert beta["preview"] == "saved after stream"


@pytest.mark.anyio
async def test_dashboard_paginates_and_validates_bounds(app_client: TestClient) -> None:
    services = _services(app_client)
    for index in range(9):
        await _create_session(services, f"session-{index}")

    response = await app_client.get("/dashboard", params={"page": "2", "page_size": "4"})
    payload = await response.json()
    assert response.status == 200
    assert payload["page"] == 2
    assert payload["page_size"] == 4
    assert payload["total"] == 9
    assert payload["total_pages"] == 3
    assert len(payload["sessions"]) == 4

    clamped = await (await app_client.get("/dashboard", params={"page": "99"})).json()
    assert clamped["page"] == clamped["total_pages"]
    assert (await app_client.get("/dashboard", params={"page": "0"})).status == 400
    assert (await app_client.get("/dashboard", params={"page_size": "51"})).status == 400
    assert (await app_client.get("/dashboard", params={"page": "nope"})).status == 400
