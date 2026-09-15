"""Regression coverage for replaying tool history across providers."""

from tau_agent.messages import AssistantMessage, ToolResultMessage
from tau_agent.tools import ToolCall
from tau_ai.anthropic import _anthropic_messages
from tau_ai.openai_compatible import _messages_to_openai, _messages_to_responses_input
from tau_ai.tool_call_ids import portable_tool_call_id


def _foreign_history(tool_call_id: str) -> list[AssistantMessage | ToolResultMessage]:
    return [
        AssistantMessage(
            content="Reading the file.",
            tool_calls=[ToolCall(id=tool_call_id, name="read", arguments={"path": "README.md"})],
        ),
        ToolResultMessage(
            tool_call_id=tool_call_id,
            name="read",
            content="contents",
            ok=True,
        ),
    ]


def test_portable_tool_call_id_preserves_safe_ids_and_hashes_foreign_ids() -> None:
    assert portable_tool_call_id("call_safe-1") == "call_safe-1"
    assert portable_tool_call_id("call|provider/item") == portable_tool_call_id(
        "call|provider/item"
    )
    assert portable_tool_call_id("call|provider/item").startswith("tc_")
    assert portable_tool_call_id("call|provider/item") != portable_tool_call_id(
        "call|provider/other"
    )
    assert len(portable_tool_call_id("x" * 100)) <= 64


def test_anthropic_compiles_foreign_tool_history_with_matching_portable_ids() -> None:
    foreign_id = "call_123|fc_opaque/provider"
    payload = _anthropic_messages(_foreign_history(foreign_id))

    tool_use = payload[0]["content"][1]
    tool_result = payload[1]["content"][0]
    assert tool_use["id"] == portable_tool_call_id(foreign_id)
    assert tool_result["tool_use_id"] == tool_use["id"]


def test_openai_chat_compiles_foreign_tool_history_with_matching_portable_ids() -> None:
    foreign_id = "anthropic.tool/use:opaque"
    payload = _messages_to_openai(_foreign_history(foreign_id))

    tool_call = payload[0]["tool_calls"][0]
    tool_result = payload[1]
    assert tool_call["id"] == portable_tool_call_id(foreign_id)
    assert tool_result["tool_call_id"] == tool_call["id"]


def test_openai_responses_compiles_foreign_history_with_matching_portable_ids() -> None:
    foreign_id = "anthropic.tool/use:opaque"
    payload = _messages_to_responses_input(_foreign_history(foreign_id))

    function_call = next(
        item for item in payload if isinstance(item, dict) and item.get("type") == "function_call"
    )
    output = next(
        item
        for item in payload
        if isinstance(item, dict) and item.get("type") == "function_call_output"
    )
    assert function_call["call_id"] == portable_tool_call_id(foreign_id)
    assert output["call_id"] == function_call["call_id"]
