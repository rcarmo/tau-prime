import httpx
import pytest

from tau_agent.messages import UserMessage
from tau_ai import AnthropicConfig, AnthropicProvider, ProviderResponseEndEvent
from tau_ai.anthropic import _parse_sse_line


@pytest.mark.parametrize("line", ["", "   ", "event: ping", "data:", "data:   ", "  data:   "])
def test_parse_sse_line_ignores_empty_or_non_data_frames(line: str) -> None:
    assert _parse_sse_line(line) is None


def test_parse_sse_line_returns_trimmed_data_payload() -> None:
    assert _parse_sse_line('  data: {"type":"message_stop"}  ') == '{"type":"message_stop"}'


@pytest.mark.anyio
async def test_anthropic_stream_ignores_empty_data_frames() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text=(
                "event: ping\n"
                "data:\n\n"
                "data:   \n\n"
                'data: {"type":"message_start","message":{"content":[]}}\n\n'
                'data: {"type":"content_block_delta","index":0,'
                '"delta":{"type":"text_delta","text":"ok"}}\n\n'
                'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"}}\n\n'
                'data: {"type":"message_stop"}\n\n'
            ),
            headers={"content-type": "text/event-stream"},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = AnthropicProvider(
            AnthropicConfig(api_key="test-key", base_url="https://api.anthropic.test/v1"),
            client=client,
        )
        events = [
            event
            async for event in provider.stream_response(
                model="claude-test",
                system="You are Tau.",
                messages=[UserMessage(content="respond")],
                tools=[],
            )
        ]

    assert [event.type for event in events] == ["response_start", "text_delta", "response_end"]
    assert isinstance(events[-1], ProviderResponseEndEvent)
    assert events[-1].message.content == "ok"
