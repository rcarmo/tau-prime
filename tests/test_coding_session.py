from pathlib import Path

import pytest

from tau_agent import AssistantMessage, ToolCall, ToolResultMessage, UserMessage
from tau_agent.session import (
    JsonlSessionStorage,
    LeafEntry,
    MessageEntry,
    ModelChangeEntry,
    SessionInfoEntry,
)
from tau_ai import FakeProvider, ProviderResponseEndEvent, ProviderResponseStartEvent
from tau_coding import (
    CodingSession,
    CodingSessionConfig,
    SessionManager,
    TauPaths,
    TauResourcePaths,
)


async def _collect_session_events(session_stream: object) -> list[object]:
    return [event async for event in session_stream]  # type: ignore[attr-defined]


def _config(
    tmp_path: Path, provider: FakeProvider, storage: JsonlSessionStorage
) -> CodingSessionConfig:
    return CodingSessionConfig(
        provider=provider,
        model="fake",
        system="You are Tau.",
        storage=storage,
        cwd=tmp_path,
    )


@pytest.mark.anyio
async def test_load_empty_session_appends_metadata(tmp_path: Path) -> None:
    storage = JsonlSessionStorage(tmp_path / "session.jsonl")

    session = await CodingSession.load(_config(tmp_path, FakeProvider([]), storage))

    entries = await storage.read_all()
    assert isinstance(entries[0], SessionInfoEntry)
    assert entries[0].cwd == str(tmp_path)
    assert entries[1] == ModelChangeEntry(
        id=entries[1].id, parent_id=entries[0].id, model="fake", timestamp=entries[1].timestamp
    )
    assert session.messages == ()
    assert session.state.model == "fake"
    assert session.cwd == tmp_path
    assert session.model == "fake"
    assert [tool.name for tool in session.tools] == ["read", "write", "edit", "bash"]


@pytest.mark.anyio
async def test_prompt_persists_user_assistant_and_leaf_entries(tmp_path: Path) -> None:
    storage = JsonlSessionStorage(tmp_path / "session.jsonl")
    provider = FakeProvider(
        [
            [
                ProviderResponseStartEvent(model="fake"),
                ProviderResponseEndEvent(message=AssistantMessage(content="Hi")),
            ]
        ]
    )
    session = await CodingSession.load(_config(tmp_path, provider, storage))

    _events = await _collect_session_events(session.prompt("Hello"))

    entries = await storage.read_all()
    message_entries = [entry for entry in entries if entry.type == "message"]
    assert [entry.message for entry in message_entries] == [
        UserMessage(content="Hello"),
        AssistantMessage(content="Hi"),
    ]
    assert entries[-1].type == "leaf"
    assert entries[-1].entry_id == message_entries[-1].id
    assert session.messages == (UserMessage(content="Hello"), AssistantMessage(content="Hi"))


@pytest.mark.anyio
async def test_load_restores_existing_transcript(tmp_path: Path) -> None:
    storage = JsonlSessionStorage(tmp_path / "session.jsonl")
    user_entry = MessageEntry(id="user", message=UserMessage(content="Earlier"))
    assistant_entry = MessageEntry(
        id="assistant",
        parent_id="user",
        message=AssistantMessage(content="Restored"),
    )
    await storage.append(user_entry)
    await storage.append(assistant_entry)

    session = await CodingSession.load(_config(tmp_path, FakeProvider([]), storage))

    assert session.messages == (
        UserMessage(content="Earlier"),
        AssistantMessage(content="Restored"),
    )


@pytest.mark.anyio
async def test_load_restores_active_leaf_branch(tmp_path: Path) -> None:
    storage = JsonlSessionStorage(tmp_path / "session.jsonl")
    root = MessageEntry(id="root", message=UserMessage(content="Root"))
    left = MessageEntry(
        id="left",
        parent_id="root",
        message=AssistantMessage(content="Inactive branch"),
    )
    right = MessageEntry(
        id="right",
        parent_id="root",
        message=AssistantMessage(content="Active branch"),
    )
    await storage.append(root)
    await storage.append(left)
    await storage.append(right)
    await storage.append(LeafEntry(entry_id="right"))

    session = await CodingSession.load(_config(tmp_path, FakeProvider([]), storage))

    assert session.messages == (
        UserMessage(content="Root"),
        AssistantMessage(content="Active branch"),
    )
    assert session.state.active_leaf_id == "right"


@pytest.mark.anyio
async def test_continue_persists_only_new_messages(tmp_path: Path) -> None:
    storage = JsonlSessionStorage(tmp_path / "session.jsonl")
    await storage.append(MessageEntry(id="user", message=UserMessage(content="Continue me")))
    provider = FakeProvider(
        [
            [
                ProviderResponseStartEvent(model="fake"),
                ProviderResponseEndEvent(message=AssistantMessage(content="Continued")),
            ]
        ]
    )
    session = await CodingSession.load(_config(tmp_path, provider, storage))

    _events = await _collect_session_events(session.continue_())

    entries = await storage.read_all()
    message_entries = [entry for entry in entries if entry.type == "message"]
    assert [entry.message for entry in message_entries] == [
        UserMessage(content="Continue me"),
        AssistantMessage(content="Continued"),
    ]


@pytest.mark.anyio
async def test_tool_results_are_persisted(tmp_path: Path) -> None:
    storage = JsonlSessionStorage(tmp_path / "session.jsonl")
    tool_call = ToolCall(id="call-1", name="missing", arguments={})
    provider = FakeProvider(
        [
            [
                ProviderResponseStartEvent(model="fake"),
                ProviderResponseEndEvent(
                    message=AssistantMessage(content="Using tool", tool_calls=[tool_call]),
                    finish_reason="tool_calls",
                ),
            ],
            [
                ProviderResponseStartEvent(model="fake"),
                ProviderResponseEndEvent(message=AssistantMessage(content="Done")),
            ],
        ]
    )
    session = await CodingSession.load(_config(tmp_path, provider, storage))

    _events = await _collect_session_events(session.prompt("Use a tool"))

    messages = [entry.message for entry in await storage.read_all() if entry.type == "message"]
    assert any(isinstance(message, ToolResultMessage) for message in messages)


@pytest.mark.anyio
async def test_session_preserves_explicit_empty_system_prompt(tmp_path: Path) -> None:
    storage = JsonlSessionStorage(tmp_path / "session.jsonl")
    provider = FakeProvider(
        [
            [
                ProviderResponseStartEvent(model="fake"),
                ProviderResponseEndEvent(message=AssistantMessage(content="Done")),
            ]
        ]
    )
    config = CodingSessionConfig(
        provider=provider,
        model="fake",
        system="",
        storage=storage,
        cwd=tmp_path,
    )
    session = await CodingSession.load(config)

    _events = await _collect_session_events(session.prompt("Hello"))

    assert provider.calls[0][1] == ""


@pytest.mark.anyio
async def test_session_builds_system_prompt_when_system_is_omitted(tmp_path: Path) -> None:
    resource_root = tmp_path / "resources"
    skills_dir = resource_root / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "testing.md").write_text(
        "---\ndescription: Test code\n---\n# Testing",
        encoding="utf-8",
    )
    storage = JsonlSessionStorage(tmp_path / "session.jsonl")
    provider = FakeProvider(
        [
            [
                ProviderResponseStartEvent(model="fake"),
                ProviderResponseEndEvent(message=AssistantMessage(content="Done")),
            ]
        ]
    )
    config = CodingSessionConfig(
        provider=provider,
        model="fake",
        storage=storage,
        cwd=tmp_path,
        resource_paths=TauResourcePaths(root=resource_root, agents_root=None),
    )
    session = await CodingSession.load(config)

    _events = await _collect_session_events(session.prompt("Hello"))

    assert "Available tools:\n- read: Read file contents" in provider.calls[0][1]
    assert "<available_skills>" in provider.calls[0][1]
    assert "<name>testing</name>" in provider.calls[0][1]


@pytest.mark.anyio
async def test_session_touches_session_manager_after_persisting_messages(tmp_path: Path) -> None:
    storage = JsonlSessionStorage(tmp_path / "session.jsonl")
    manager = SessionManager(TauPaths(home=tmp_path / ".tau", agents_home=tmp_path / ".agents"))
    record = manager.create_session(cwd=tmp_path, model="fake")
    provider = FakeProvider(
        [
            [
                ProviderResponseStartEvent(model="fake"),
                ProviderResponseEndEvent(message=AssistantMessage(content="Done")),
            ]
        ]
    )
    config = CodingSessionConfig(
        provider=provider,
        model="fake",
        system="You are Tau.",
        storage=storage,
        cwd=tmp_path,
        session_id=record.id,
        session_manager=manager,
        resource_paths=TauResourcePaths(root=tmp_path / "resources", agents_root=None),
    )
    session = await CodingSession.load(config)

    _events = await _collect_session_events(session.prompt("Hello"))

    updated = manager.get_session(record.id)
    assert updated is not None
    assert updated.updated_at >= record.updated_at


@pytest.mark.anyio
async def test_session_loads_and_expands_skills(tmp_path: Path) -> None:
    resource_root = tmp_path / "resources"
    skills_dir = resource_root / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "testing.md").write_text("# Testing\nRun pytest.", encoding="utf-8")
    storage = JsonlSessionStorage(tmp_path / "session.jsonl")
    provider = FakeProvider(
        [
            [
                ProviderResponseStartEvent(model="fake"),
                ProviderResponseEndEvent(message=AssistantMessage(content="Done")),
            ]
        ]
    )
    config = CodingSessionConfig(
        provider=provider,
        model="fake",
        system="You are Tau.",
        storage=storage,
        cwd=tmp_path,
        resource_paths=TauResourcePaths(root=resource_root, agents_root=None),
    )
    session = await CodingSession.load(config)

    _events = await _collect_session_events(session.prompt("/skill:testing add tests"))

    assert [skill.name for skill in session.skills] == ["testing"]
    assert '<skill name="testing">' in provider.calls[0][2][0].content
    assert "User request:\nadd tests" in provider.calls[0][2][0].content
    assert session.handle_command("/skill:testing").handled is False


def test_minimal_commands_are_handled(tmp_path: Path) -> None:
    session = CodingSession(
        _config(tmp_path, FakeProvider([]), JsonlSessionStorage(tmp_path / "session.jsonl")),
        state=object(),  # type: ignore[arg-type]
        harness=object(),  # type: ignore[arg-type]
        last_parent_id=None,
    )

    assert session.handle_command("hello").handled is False
    assert session.handle_command("/help").message is not None
    assert "/help" in session.handle_command("/help").message
    assert session.handle_command("/clear").clear_requested is True
    assert session.handle_command("/exit").exit_requested is True
    assert session.handle_command("/unknown").message == "Unknown command: /unknown"
