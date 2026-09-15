from __future__ import annotations

import json

import pytest
from aiohttp.test_utils import TestClient, TestServer

from tau_web.app import create_app
from tau_web.config import WebConfig


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


@pytest.mark.anyio
async def test_onboarding_persists_redacted_provider_selection(
    app_client: TestClient, web_config: WebConfig
) -> None:
    initial = await app_client.get("/api/onboarding")
    assert initial.status == 200
    initial_json = await initial.json()
    assert initial_json["configured"] is False
    assert "secret-key" not in json.dumps(initial_json)

    configured = await app_client.put(
        "/api/onboarding",
        json={"provider": "openai", "model": "gpt-5.5", "credential": "secret-key"},
    )
    assert configured.status == 200
    payload = await configured.json()
    assert payload["configured"] is True
    assert payload["default_provider"] == "openai"
    assert payload["default_model"] == "gpt-5.5"
    assert "secret-key" not in json.dumps(payload)

    credential_data = json.loads(
        (web_config.database_path.parent / "credentials.json").read_text(encoding="utf-8")
    )
    assert credential_data["openai"] == "secret-key"
    provider_data = json.loads(
        (web_config.database_path.parent / "providers.json").read_text(encoding="utf-8")
    )
    assert provider_data["default_provider"] == "openai"
    resumed = await app_client.get("/api/onboarding")
    resumed_json = await resumed.json()
    assert resumed_json["configured"] is True
    assert resumed_json["default_provider"] == "openai"


@pytest.mark.anyio
async def test_onboarding_rejects_invalid_input_without_writing_credentials(
    app_client: TestClient, web_config: WebConfig
) -> None:
    unknown_model = await app_client.put(
        "/api/onboarding",
        json={"provider": "openai", "model": "not-a-model", "credential": "secret"},
    )
    assert unknown_model.status == 400
    assert not (web_config.database_path.parent / "credentials.json").exists()

    blank = await app_client.put(
        "/api/onboarding",
        json={"provider": "openai", "model": "gpt-5.5", "credential": "  "},
    )
    assert blank.status == 400
    assert not (web_config.database_path.parent / "credentials.json").exists()
