from __future__ import annotations

from typing import cast

import pytest
from aiohttp.test_utils import TestClient, TestServer

from tau_web.app import SERVICES_KEY, create_app
from tau_web.config import WebConfig
from tau_web.services import TauWebServices


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def app_client(web_config: WebConfig) -> TestClient:
    app = create_app(web_config)
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        yield client
    finally:
        await client.close()


def _services(client: TestClient) -> TauWebServices:
    return cast(TauWebServices, client.app[SERVICES_KEY])


async def _session(client: TestClient, session_id: str = "meta") -> dict[str, object]:
    services = _services(client)
    record = await services.sessions.create(
        workspace_root=services.config.cwd,
        provider_name="test",
        model="base",
        agent_name=session_id,
        session_id=session_id,
        thinking_level="low",
    )
    response = await client.get(f"/api/sessions/{record.session_id}")
    assert response.status == 200
    return await response.json()


@pytest.mark.anyio
async def test_settings_models_commands_and_session_controls(app_client: TestClient) -> None:
    session = await _session(app_client)

    settings = await app_client.get("/api/settings")
    assert settings.status == 200
    settings_json = await settings.json()
    assert "auth_token" not in settings_json
    assert settings_json["auth_required"] is False

    models = await app_client.get("/api/models")
    assert await models.json() == {
        "source": "sessions",
        "models": [{"provider_name": "test", "model": "base"}],
    }
    commands = await app_client.get("/api/commands")
    assert commands.status == 200
    assert (await commands.json())["source"] == "runtime"

    changed = await app_client.patch(
        "/api/sessions/meta/model",
        json={
            "provider_name": "other",
            "model": "new-model",
            "expected_updated_at": session["updated_at"],
        },
    )
    assert changed.status == 200
    changed_json = await changed.json()
    assert changed_json["model"] == "new-model"

    thinking = await app_client.patch(
        "/api/sessions/meta/thinking",
        json={"thinking_level": "high", "expected_updated_at": changed_json["updated_at"]},
    )
    assert thinking.status == 200
    context = await app_client.get("/api/sessions/meta/context")
    context_json = await context.json()
    assert context_json["model"] == "new-model"
    assert context_json["thinking_level"] == "high"

    stale = await app_client.patch(
        "/api/sessions/meta/model",
        json={
            "provider_name": "test",
            "model": "stale",
            "expected_updated_at": session["updated_at"],
        },
    )
    assert stale.status == 409


@pytest.mark.anyio
async def test_plan_usage_and_search_routes(app_client: TestClient) -> None:
    await _session(app_client)
    services = _services(app_client)

    empty_plan = await app_client.get("/api/sessions/meta/plan")
    assert (await empty_plan.json())["revision"] == 0
    plan_events, _ = services.broker.subscribe(session_id="meta")
    created = await app_client.put(
        "/api/sessions/meta/plan",
        json={
            "content": {"items": [{"step": "ship", "status": "pending"}]},
            "expected_revision": None,
        },
    )
    assert created.status == 200
    created_json = await created.json()
    assert created_json["revision"] == 1
    assert created_json["markdown"] == "- [ ] ship"
    event = await plan_events.next(timeout=0.1)
    assert event is not None
    assert event.envelope.type == "tau.plan.updated"
    assert event.envelope.payload == {"revision": 1}
    stale = await app_client.put(
        "/api/sessions/meta/plan",
        json={"content": {}, "expected_revision": 0},
    )
    assert stale.status == 409
    stale_json = await stale.json()
    assert stale_json["error"]["code"] == "plan_revision_conflict"
    assert stale_json["current"]["revision"] == 1

    await services.usage.record(
        "meta",
        provider_name="test",
        model="base",
        input_tokens=3,
        output_tokens=5,
        cached_input_tokens=2,
        cache_write_tokens=11,
        cache_write_1h_tokens=4,
        cost_microunits=7,
    )
    usage = await app_client.get("/api/sessions/meta/usage")
    assert usage.status == 200
    assert (await usage.json())["totals"] == {
        "input": 3,
        "output": 5,
        "cache_read": 2,
        "cache_write": 11,
        "cache_write_1h": 4,
        "cost": 7,
    }

    await services.fts.upsert(
        entity_type="message", entity_id="m1", session_id="meta", text="durable alpaca"
    )
    search = await app_client.get("/api/search", params={"q": "alpaca", "session_id": "meta"})
    assert search.status == 200
    assert (await search.json())["results"][0]["entity_id"] == "m1"
    assert (await app_client.get("/api/search", params={"q": " "})).status == 400
    assert (await app_client.get("/api/search", params={"q": "alpaca", "limit": "0"})).status == 400
