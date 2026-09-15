from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from tau_web.app import create_app
from tau_web.config import WebConfig


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def _start_client(app: web.Application) -> TestClient:
    client = TestClient(TestServer(app))
    await client.start_server()
    return client


@pytest.mark.anyio
async def test_session_routes_crud_archive_restore_and_alias_resolution(
    web_config: WebConfig,
) -> None:
    app = create_app(web_config)
    client = await _start_client(app)

    try:
        async with client.post(
            "/api/sessions",
            json={
                "provider_name": "anthropic",
                "model": "claude-sonnet",
                "agent_name": "MiXeD",
                "title": "Original",
                "thinking_level": "high",
                "metadata": {"chat_jid": "web:mixed", "labels": ["one", "two"]},
            },
        ) as response:
            assert response.status == 201
            created = await response.json()

        session_id = created["session_id"]
        assert created == {
            "session_id": session_id,
            "workspace_id": created["workspace_id"],
            "workspace_root": str(web_config.cwd),
            "agent_name": "MiXeD",
            "title": "Original",
            "provider_name": "anthropic",
            "model": "claude-sonnet",
            "thinking_level": "high",
            "active_leaf_entry_id": None,
            "created_at": created["created_at"],
            "updated_at": created["updated_at"],
            "archived_at": None,
            "metadata": {"chat_jid": "web:mixed", "labels": ["one", "two"]},
        }

        async with client.get("/api/sessions") as response:
            assert response.status == 200
            listed = await response.json()

        assert listed == {"sessions": [created]}

        async with client.get(f"/api/sessions/{session_id}") as response:
            assert response.status == 200
            fetched = await response.json()

        assert fetched == created

        async with client.get("/api/aliases/@mixed") as response:
            assert response.status == 200
            alias_hit = await response.json()

        assert alias_hit["session_id"] == session_id
        assert alias_hit["agent_name"] == "MiXeD"

        async with client.get("/api/aliases/chat_jid:web:mixed") as response:
            assert response.status == 200
            jid_hit = await response.json()

        assert jid_hit["session_id"] == session_id

        async with client.patch(
            f"/api/sessions/{session_id}",
            json={
                "agent_name": "Renamed",
                "provider_name": "openai",
                "model": "gpt-5",
                "title": "Updated",
                "expected_updated_at": created["updated_at"],
            },
        ) as response:
            assert response.status == 200
            updated = await response.json()

        assert updated["session_id"] == session_id
        assert updated["agent_name"] == "Renamed"
        assert updated["provider_name"] == "openai"
        assert updated["model"] == "gpt-5"
        assert updated["title"] == "Updated"
        assert updated["updated_at"] != created["updated_at"]

        async with client.delete(f"/api/sessions/{session_id}") as response:
            assert response.status == 200
            archived = await response.json()

        assert archived["session_id"] == session_id
        assert archived["archived_at"] is not None

        async with client.get("/api/sessions") as response:
            assert response.status == 200
            hidden = await response.json()

        assert hidden == {"sessions": []}

        async with client.get("/api/sessions?include_archived=true") as response:
            assert response.status == 200
            archived_list = await response.json()

        assert archived_list == {"sessions": [archived]}

        async with client.get("/api/aliases/@renamed") as response:
            assert response.status == 404
            missing_alias = await response.json()

        assert missing_alias["error"]["code"] == "not_found"

        async with client.post(
            f"/api/sessions/{session_id}/restore",
            json={"agent_name": "Restored"},
        ) as response:
            assert response.status == 200
            restored = await response.json()

        assert restored["session_id"] == session_id
        assert restored["archived_at"] is None
        assert restored["agent_name"] == "Restored"

        async with client.get("/api/aliases/@restored") as response:
            assert response.status == 200
            restored_alias = await response.json()

        assert restored_alias["session_id"] == session_id
    finally:
        await client.close()


@pytest.mark.anyio
async def test_session_routes_reject_duplicate_names_and_stale_revisions(
    web_config: WebConfig,
) -> None:
    app = create_app(web_config)
    client = await _start_client(app)

    try:
        async with client.post(
            "/api/sessions",
            json={
                "provider_name": "test",
                "model": "model",
                "agent_name": "Worker",
            },
        ) as response:
            assert response.status == 201
            created = await response.json()

        async with client.post(
            "/api/sessions",
            json={
                "provider_name": "test",
                "model": "model",
                "agent_name": "worker",
            },
        ) as response:
            assert response.status == 409
            duplicate = await response.json()

        assert duplicate["error"]["code"] == "conflict"
        assert "Active agent name already exists" in duplicate["error"]["message"]

        async with client.patch(
            f"/api/sessions/{created['session_id']}",
            json={
                "title": "Fresh",
                "expected_updated_at": created["updated_at"],
            },
        ) as response:
            assert response.status == 200
            fresh = await response.json()

        async with client.patch(
            f"/api/sessions/{created['session_id']}",
            json={
                "title": "Stale",
                "expected_updated_at": created["updated_at"],
            },
        ) as response:
            assert response.status == 409
            stale = await response.json()

        assert fresh["title"] == "Fresh"
        assert stale["error"]["code"] == "conflict"
        assert "expected updated_at" in stale["error"]["message"]
    finally:
        await client.close()


@pytest.mark.anyio
async def test_session_routes_validate_requests_and_return_404s(
    web_config: WebConfig,
) -> None:
    app = create_app(web_config)
    client = await _start_client(app)

    try:
        async with client.post(
            "/api/sessions",
            json={"provider_name": "test"},
        ) as response:
            assert response.status == 400
            missing = await response.json()

        assert missing["error"]["code"] == "bad_request"
        assert missing["error"]["message"] == "Missing required field(s): model."

        async with client.post(
            "/api/sessions",
            json={"provider_name": "test", "model": "model", "metadata": []},
        ) as response:
            assert response.status == 400
            bad_metadata = await response.json()

        assert bad_metadata["error"]["code"] == "bad_request"
        assert bad_metadata["error"]["message"] == "Field 'metadata' must be a JSON object."

        async with client.get("/api/sessions?include_archived=maybe") as response:
            assert response.status == 400
            bad_query = await response.json()

        assert bad_query["error"]["code"] == "bad_request"
        assert bad_query["error"]["message"] == (
            "Query parameter 'include_archived' must be a boolean."
        )

        async with client.get("/api/sessions/missing") as response:
            assert response.status == 404
            missing_session = await response.json()

        assert missing_session["error"]["code"] == "not_found"
        assert missing_session["error"]["message"] == "Unknown session: missing"
    finally:
        await client.close()
