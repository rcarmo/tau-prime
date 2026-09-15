from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest

from tau_agent.session import JsonlSessionStorage
from tau_agent.tools import AgentTool, AgentToolResult, ToolCancellationToken
from tau_agent.types import JSONValue
from tau_ai import FakeProvider
from tau_coding.coding_session_factory import (
    CodingSessionFactory,
    CodingSessionFactoryConfig,
    CodingSessionFactoryRequest,
)
from tau_coding.session import CodingSession, CodingSessionConfig


async def _execute(
    arguments: Mapping[str, JSONValue],
    signal: ToolCancellationToken | None = None,
) -> AgentToolResult:
    del arguments, signal
    return AgentToolResult(tool_call_id="", name="extra", ok=True, content="ok")


def _tool(name: str) -> AgentTool:
    return AgentTool(name=name, description=name, input_schema={}, executor=_execute)


@pytest.mark.anyio
async def test_turn_context_is_refreshed_without_polluting_user_messages(
    tmp_path: Path,
) -> None:
    provider = FakeProvider([[], []])
    contexts = iter(("<tau-session-plan revision=\"1\">one</tau-session-plan>",
                     "<tau-session-plan revision=\"2\">two</tau-session-plan>"))

    async def turn_context() -> str:
        return next(contexts)

    session = await CodingSession.load(
        CodingSessionConfig(
            provider=provider,
            model="fake",
            storage=JsonlSessionStorage(tmp_path / "session.jsonl"),
            cwd=tmp_path,
            system="base system",
            turn_context_provider=turn_context,
        )
    )

    _ = [event async for event in session.prompt("first")]
    _ = [event async for event in session.prompt("second")]

    assert provider.calls[0][1] == (
        'base system\n\n<tau-session-plan revision="1">one</tau-session-plan>'
    )
    assert provider.calls[1][1] == (
        'base system\n\n<tau-session-plan revision="2">two</tau-session-plan>'
    )
    assert "revision=\"1\"" not in provider.calls[1][1]
    assert [message.content for message in session.messages] == ["first", "second"]


@pytest.mark.anyio
async def test_factory_appends_session_specific_tools_to_default_and_explicit_sets(
    tmp_path: Path,
) -> None:
    def extra_tools(binding: object) -> tuple[AgentTool, ...]:
        del binding
        return (_tool("plan"),)

    request = CodingSessionFactoryRequest(
        cwd=tmp_path,
        storage=JsonlSessionStorage(tmp_path / "default.jsonl"),
        session_id="session-1",
        provider=FakeProvider([]),
        provider_name="fake",
        model="fake",
    )
    default_session = await CodingSessionFactory(
        CodingSessionFactoryConfig(extra_tools_factory=extra_tools)
    ).load(request)
    assert "read" in {tool.name for tool in default_session.tools}
    assert "plan" in {tool.name for tool in default_session.tools}

    explicit_request = CodingSessionFactoryRequest(
        cwd=tmp_path,
        storage=JsonlSessionStorage(tmp_path / "explicit.jsonl"),
        session_id="session-2",
        provider=FakeProvider([]),
        provider_name="fake",
        model="fake",
    )
    explicit_session = await CodingSessionFactory(
        CodingSessionFactoryConfig(
            tools=(_tool("custom"),),
            extra_tools_factory=extra_tools,
        )
    ).load(explicit_request)
    assert {tool.name for tool in explicit_session.tools} == {"custom", "plan"}
