from pathlib import Path

from tau_coding.commands import CommandRegistry, SlashCommand, create_default_command_registry
from tau_coding.paths import TauPaths
from tau_coding.session_manager import SessionManager
from tau_coding.skills import Skill
from tau_coding.tools import create_coding_tools


class FakeSession:
    def __init__(self, tmp_path: Path, manager: SessionManager | None = None) -> None:
        self.cwd = tmp_path
        self.model = "fake-model"
        self.tools = tuple(create_coding_tools(cwd=tmp_path))
        self.skills = (
            Skill(
                name="review",
                path=tmp_path / "review.md",
                content="Review code",
                description="Review code",
            ),
        )
        self.prompt_templates = ()
        self.session_id = "session-1"
        self.session_manager: SessionManager | None = manager


def test_registry_ignores_ordinary_prompts_and_skill_expansion(tmp_path: Path) -> None:
    registry = create_default_command_registry()
    session = FakeSession(tmp_path)

    assert registry.execute(session, "hello").handled is False
    assert registry.execute(session, "/skill:review fix this").handled is False


def test_help_lists_registered_commands(tmp_path: Path) -> None:
    result = create_default_command_registry().execute(FakeSession(tmp_path), "/help")

    assert result.handled is True
    assert result.message is not None
    assert "/help" in result.message
    assert "/clear" in result.message
    assert "/skills" in result.message


def test_exit_and_clear_return_control_flags(tmp_path: Path) -> None:
    registry = create_default_command_registry()
    session = FakeSession(tmp_path)

    assert registry.execute(session, "/exit").exit_requested is True
    assert registry.execute(session, "/q").exit_requested is True
    assert registry.execute(session, "/clear").clear_requested is True


def test_status_includes_session_details(tmp_path: Path) -> None:
    result = create_default_command_registry().execute(FakeSession(tmp_path), "/status")

    assert result.message is not None
    assert "Model: fake-model" in result.message
    assert f"CWD: {tmp_path}" in result.message
    assert "Tools: 4" in result.message
    assert "Skills: 1" in result.message
    assert "Session: session-1" in result.message


def test_skills_lists_loaded_skills(tmp_path: Path) -> None:
    result = create_default_command_registry().execute(FakeSession(tmp_path), "/skills")

    assert result.message is not None
    assert "Available skills:" in result.message
    assert "- review: Review code" in result.message
    assert "/skill:review" not in result.message


def test_sessions_lists_indexed_sessions(tmp_path: Path) -> None:
    manager = SessionManager(TauPaths(home=tmp_path / ".tau", agents_home=tmp_path / ".agents"))
    record = manager.create_session(cwd=tmp_path, model="fake-model", title="Test session")
    session = FakeSession(tmp_path, manager=manager)

    result = create_default_command_registry().execute(session, "/sessions")

    assert result.message is not None
    assert "Indexed sessions:" in result.message
    assert record.id in result.message
    assert "Test session" in result.message


def test_unknown_command_returns_message(tmp_path: Path) -> None:
    result = create_default_command_registry().execute(FakeSession(tmp_path), "/missing")

    assert result.handled is True
    assert result.message == "Unknown command: /missing"


def test_registry_rejects_duplicate_commands_and_aliases() -> None:
    registry = CommandRegistry()
    command = SlashCommand(
        name="test",
        usage="/test",
        description="Test",
        handler=lambda context: create_default_command_registry().execute(context.session, "/help"),
    )
    registry.register(command)

    try:
        registry.register(command)
    except ValueError as exc:
        assert "Duplicate slash command" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("expected duplicate command to fail")
