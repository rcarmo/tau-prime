from __future__ import annotations

from typing import cast

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from tau_agent import AssistantMessage, UserMessage
from tau_agent.session import (
    CompactionEntry,
    LeafEntry,
    MessageEntry,
    ModelChangeEntry,
    ThinkingLevelChangeEntry,
)
from tau_web.app import SERVICES_KEY, create_app
from tau_web.config import WebConfig
from tau_web.services import TauWebServices


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def app(web_config: WebConfig) -> web.Application:
    return create_app(web_config)


@pytest.fixture
async def app_client(app: web.Application) -> TestClient:
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        yield client
    finally:
        await client.close()


@pytest.fixture
def services(app: web.Application, app_client: TestClient) -> TauWebServices:
    del app_client
    return cast(TauWebServices, app[SERVICES_KEY])


async def _create_durable_session(
    services: TauWebServices,
    *,
    session_id: str,
    model: str = "base-model",
    thinking_level: str | None = "low",
) -> str:
    record = await services.sessions.create(
        workspace_root=services.config.cwd,
        provider_name="test",
        model=model,
        agent_name=session_id,
        session_id=session_id,
        thinking_level=thinking_level,
    )
    return record.session_id


def _entry_ids(items: list[dict[str, object]]) -> list[str]:
    return [str(item["id"]) for item in items]


@pytest.mark.anyio
async def test_timeline_routes_entries_messages_branches_select_and_context(
    app_client: TestClient,
    services: TauWebServices,
) -> None:
    session_id = await _create_durable_session(
        services,
        session_id="timeline",
        model="base-model",
        thinking_level="low",
    )
    storage = services.session_storage(session_id)
    root = MessageEntry(
        id="root",
        timestamp=1.0,
        message=UserMessage(content="Root prompt"),
    )
    left = MessageEntry(
        id="left",
        parent_id="root",
        timestamp=2.0,
        message=AssistantMessage(content="Left branch"),
    )
    right = MessageEntry(
        id="right",
        parent_id="root",
        timestamp=3.0,
        message=AssistantMessage(content="Right branch"),
    )
    model = ModelChangeEntry(
        id="model",
        parent_id="left",
        timestamp=4.0,
        model="branch-model",
    )
    thinking = ThinkingLevelChangeEntry(
        id="thinking",
        parent_id="model",
        timestamp=5.0,
        thinking_level="high",
    )
    compact = CompactionEntry(
        id="compact",
        parent_id="thinking",
        timestamp=6.0,
        summary="Compacted left branch",
        replaces_entry_ids=["root", "left"],
    )
    selected = LeafEntry(
        id="selected-left",
        parent_id="compact",
        timestamp=7.0,
        entry_id="compact",
    )
    await storage.append_many([root, left, right, model, thinking, compact, selected])

    async with app_client.get(f"/api/sessions/{session_id}/entries") as response:
        assert response.status == 200
        payload = await response.json()

    assert _entry_ids(payload["entries"]) == [
        "root",
        "left",
        "right",
        "model",
        "thinking",
        "compact",
        "selected-left",
    ]
    assert [entry["type"] for entry in payload["entries"]] == [
        "message",
        "message",
        "message",
        "model_change",
        "thinking_level_change",
        "compaction",
        "leaf",
    ]

    async with app_client.get(
        f"/api/sessions/{session_id}/entries?leaf_entry_id=compact"
    ) as response:
        assert response.status == 200
        payload = await response.json()

    assert _entry_ids(payload["entries"]) == ["root", "left", "model", "thinking", "compact"]

    async with app_client.get(f"/api/sessions/{session_id}/messages") as response:
        assert response.status == 200
        payload = await response.json()

    assert payload["leaf_entry_id"] == "compact"
    assert _entry_ids(payload["messages"]) == ["root", "left"]
    assert [message["message"] for message in payload["messages"]] == [
        {"role": "user", "content": "Root prompt"},
        {"role": "assistant", "content": "Left branch", "tool_calls": []},
    ]

    async with app_client.get(
        f"/api/sessions/{session_id}/messages?leaf_entry_id=right"
    ) as response:
        assert response.status == 200
        payload = await response.json()

    assert payload["leaf_entry_id"] == "right"
    assert _entry_ids(payload["messages"]) == ["root", "right"]
    assert [message["message"] for message in payload["messages"]] == [
        {"role": "user", "content": "Root prompt"},
        {"role": "assistant", "content": "Right branch", "tool_calls": []},
    ]

    async with app_client.get(f"/api/sessions/{session_id}/branches") as response:
        assert response.status == 200
        payload = await response.json()

    assert payload == {
        "branches": [
            {"leaf_entry_id": "right", "active": False, "depth": 1, "timestamp": 3.0},
            {"leaf_entry_id": "compact", "active": True, "depth": 4, "timestamp": 6.0},
        ]
    }

    async with app_client.get(f"/api/sessions/{session_id}/context") as response:
        assert response.status == 200
        payload = await response.json()

    assert payload == {
        "entry_count": 5,
        "message_count": 2,
        "compaction_count": 1,
        "active_leaf_entry_id": "compact",
        "model": "branch-model",
        "thinking_level": "high",
    }

    async with app_client.post(
        f"/api/sessions/{session_id}/branches/select",
        json={"leaf_entry_id": "right"},
    ) as response:
        assert response.status == 200
        payload = await response.json()

    assert payload["leaf_entry_id"] == "right"
    assert payload["session"]["active_leaf_entry_id"] == "right"
    updated = await services.sessions.get(session_id)
    assert updated is not None
    assert updated.active_leaf_entry_id == "right"
    entries = await storage.read_all()
    assert isinstance(entries[-1], LeafEntry)
    assert entries[-1].parent_id == "right"
    assert entries[-1].entry_id == "right"

    async with app_client.post(
        f"/api/sessions/{session_id}/branches/select",
        json={"leaf_entry_id": None},
    ) as response:
        assert response.status == 200
        payload = await response.json()

    assert payload["leaf_entry_id"] is None
    assert payload["session"]["active_leaf_entry_id"] is None
    updated = await services.sessions.get(session_id)
    assert updated is not None
    assert updated.active_leaf_entry_id is None
    entries = await storage.read_all()
    assert isinstance(entries[-1], LeafEntry)
    assert entries[-1].parent_id is None
    assert entries[-1].entry_id is None

    async with app_client.get(f"/api/sessions/{session_id}/messages") as response:
        assert response.status == 200
        payload = await response.json()

    assert payload == {"leaf_entry_id": None, "messages": []}


@pytest.mark.anyio
async def test_timeline_routes_handle_empty_sessions(
    app_client: TestClient,
    services: TauWebServices,
) -> None:
    session_id = await _create_durable_session(
        services,
        session_id="empty-session",
        model="empty-model",
        thinking_level="minimal",
    )

    async with app_client.get(f"/api/sessions/{session_id}/entries") as response:
        assert response.status == 200
        entries_payload = await response.json()

    assert entries_payload == {"entries": []}

    async with app_client.get(f"/api/sessions/{session_id}/messages") as response:
        assert response.status == 200
        messages_payload = await response.json()

    assert messages_payload == {"leaf_entry_id": None, "messages": []}

    async with app_client.get(f"/api/sessions/{session_id}/branches") as response:
        assert response.status == 200
        branches_payload = await response.json()

    assert branches_payload == {"branches": []}

    async with app_client.get(f"/api/sessions/{session_id}/context") as response:
        assert response.status == 200
        context_payload = await response.json()

    assert context_payload == {
        "entry_count": 0,
        "message_count": 0,
        "compaction_count": 0,
        "active_leaf_entry_id": None,
        "model": "empty-model",
        "thinking_level": "minimal",
    }


@pytest.mark.anyio
async def test_timeline_routes_reject_unknown_sessions_unknown_leaves_and_invalid_select_bodies(
    app_client: TestClient,
    services: TauWebServices,
) -> None:
    session_id = await _create_durable_session(services, session_id="errors")
    storage = services.session_storage(session_id)
    await storage.append(
        MessageEntry(
            id="root",
            timestamp=1.0,
            message=UserMessage(content="Root prompt"),
        )
    )

    async with app_client.get("/api/sessions/missing/entries") as response:
        assert response.status == 404
        payload = await response.json()

    assert payload["error"]["code"] == "not_found"
    assert payload["error"]["message"] == "Unknown session: missing"

    async with app_client.get(
        f"/api/sessions/{session_id}/entries?leaf_entry_id=missing-leaf"
    ) as response:
        assert response.status == 404
        payload = await response.json()

    assert payload["error"]["code"] == "not_found"
    assert payload["error"]["message"] == "Unknown leaf entry: missing-leaf"

    async with app_client.get(
        f"/api/sessions/{session_id}/messages?leaf_entry_id=missing-leaf"
    ) as response:
        assert response.status == 404
        payload = await response.json()

    assert payload["error"]["code"] == "not_found"
    assert payload["error"]["message"] == "Unknown leaf entry: missing-leaf"

    async with app_client.post(
        f"/api/sessions/{session_id}/branches/select",
        json={"leaf_entry_id": "missing-leaf"},
    ) as response:
        assert response.status == 404
        payload = await response.json()

    assert payload["error"]["code"] == "not_found"
    assert payload["error"]["message"] == "Unknown leaf entry: missing-leaf"

    async with app_client.post(
        "/api/sessions/missing/branches/select",
        json={"leaf_entry_id": "root"},
    ) as response:
        assert response.status == 404
        payload = await response.json()

    assert payload["error"]["code"] == "not_found"
    assert payload["error"]["message"] == "Unknown session: missing"

    async with app_client.post(
        f"/api/sessions/{session_id}/branches/select",
        json={},
    ) as response:
        assert response.status == 400
        payload = await response.json()

    assert payload["error"]["code"] == "bad_request"
    assert payload["error"]["message"] == "Missing required field(s): leaf_entry_id."

    async with app_client.post(
        f"/api/sessions/{session_id}/branches/select",
        json={"leaf_entry_id": "root", "extra": True},
    ) as response:
        assert response.status == 400
        payload = await response.json()

    assert payload["error"]["code"] == "bad_request"
    assert payload["error"]["message"] == "Unknown field(s): extra."

    async with app_client.post(
        f"/api/sessions/{session_id}/branches/select",
        json={"leaf_entry_id": 1},
    ) as response:
        assert response.status == 400
        payload = await response.json()

    assert payload["error"]["code"] == "bad_request"
    assert payload["error"]["message"] == "Field 'leaf_entry_id' must be a string or null."

    async with app_client.post(
        f"/api/sessions/{session_id}/branches/select",
        json={"leaf_entry_id": "   "},
    ) as response:
        assert response.status == 400
        payload = await response.json()

    assert payload["error"]["code"] == "bad_request"
    assert payload["error"]["message"] == "Field 'leaf_entry_id' must not be blank."
