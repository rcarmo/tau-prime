from __future__ import annotations

import json

import httpx
import pytest

from tau_agent.messages import UserMessage
from tau_ai import OpenAICompatibleConfig, OpenAICompatibleProvider, RemoteCompactionState


@pytest.mark.anyio
async def test_openai_native_compaction_uses_verified_endpoint() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "output": [
                    {
                        "type": "compaction",
                        "encrypted_content": "opaque-state",
                    }
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenAICompatibleProvider(
            OpenAICompatibleConfig(
                api_key="test-key",
                base_url="https://api.openai.com/v1",
            ),
            client=client,
        )
        state = await provider.compact_context(
            model="gpt-5.4",
            system="You are Tau.",
            messages=[UserMessage(content="Keep this context")],
            tools=[],
        )

    assert state is not None
    assert state.output[0]["encrypted_content"] == "opaque-state"
    assert requests[0].url == httpx.URL("https://api.openai.com/v1/responses/compact")
    assert requests[0].headers["authorization"] == "Bearer test-key"
    body = json.loads(requests[0].content)
    assert body["model"] == "gpt-5.4"
    assert "stream" not in body


@pytest.mark.anyio
async def test_openai_native_compaction_rejects_unverified_proxy() -> None:
    provider = OpenAICompatibleProvider(
        OpenAICompatibleConfig(api_key="test-key", base_url="https://proxy.example/v1")
    )

    assert (
        await provider.compact_context(
            model="gpt-5.4",
            system="You are Tau.",
            messages=[UserMessage(content="Context")],
            tools=[],
        )
        is None
    )


def test_remote_compaction_state_requires_encrypted_canonical_item() -> None:
    assert (
        RemoteCompactionState.from_details(
            {
                "kind": "tau.remote_compaction",
                "version": 1,
                "provider": "openai",
                "model": "gpt-5.4",
                "base_url": "https://api.openai.com/v1",
                "output": [{"type": "message", "content": "not canonical"}],
            }
        )
        is None
    )
