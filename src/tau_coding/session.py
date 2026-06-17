"""Persistent coding-session wrapper built on AgentHarness."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

from tau_agent import AgentEvent, AgentHarness, AgentHarnessConfig
from tau_agent.messages import AgentMessage
from tau_agent.session import (
    JsonlSessionStorage,
    LeafEntry,
    MessageEntry,
    ModelChangeEntry,
    SessionInfoEntry,
    SessionState,
    SessionStorage,
)
from tau_agent.tools import AgentTool
from tau_ai import ModelProvider
from tau_coding.commands import CommandRegistry, CommandResult, create_default_command_registry
from tau_coding.paths import TauPaths
from tau_coding.prompt_templates import PromptTemplate, load_prompt_templates
from tau_coding.resources import ResourceError, TauResourcePaths
from tau_coding.session_manager import SessionManager
from tau_coding.skills import Skill, expand_skill_command, load_skills
from tau_coding.system_prompt import (
    BuildSystemPromptOptions,
    ProjectContextFile,
    build_system_prompt,
)
from tau_coding.tools import create_coding_tools


@dataclass(frozen=True, slots=True)
class CodingSessionConfig:
    """Configuration for a persistent coding session."""

    provider: ModelProvider
    model: str
    storage: SessionStorage
    cwd: Path
    system: str | None = None
    custom_system_prompt: str | None = None
    append_system_prompt: str | None = None
    context_files: tuple[ProjectContextFile, ...] = ()
    tools: list[AgentTool] | None = None
    resource_paths: TauResourcePaths | None = None
    session_id: str | None = None
    session_manager: SessionManager | None = None
    command_registry: CommandRegistry | None = None


class CodingSession:
    """Tau's coding-agent environment wrapper.

    `AgentHarness` owns the in-memory agent brain. `CodingSession` owns the
    coding-session environment around it: durable session entries, default coding
    tools, and a small command seam for later phases.
    """

    def __init__(
        self,
        config: CodingSessionConfig,
        *,
        state: SessionState,
        harness: AgentHarness,
        last_parent_id: str | None,
        skills: tuple[Skill, ...] = (),
        prompt_templates: tuple[PromptTemplate, ...] = (),
        command_registry: CommandRegistry | None = None,
    ) -> None:
        self._config = config
        self._state = state
        self._harness = harness
        self._last_parent_id = last_parent_id
        self._skills = skills
        self._prompt_templates = prompt_templates
        self._command_registry = command_registry or create_default_command_registry()

    @classmethod
    async def load(cls, config: CodingSessionConfig) -> CodingSession:
        """Load a coding session from append-only storage."""
        entries = await config.storage.read_all()
        if not entries:
            info = SessionInfoEntry(cwd=str(config.cwd))
            model = ModelChangeEntry(parent_id=info.id, model=config.model)
            await config.storage.append(info)
            await config.storage.append(model)
            entries = [info, model]

        linear_state = SessionState.from_entries(entries)
        state = (
            SessionState.from_entries(entries, leaf_id=linear_state.active_leaf_id)
            if linear_state.active_leaf_id is not None
            else linear_state
        )
        tools = config.tools if config.tools is not None else create_coding_tools(cwd=config.cwd)
        resource_paths = config.resource_paths or TauResourcePaths(cwd=config.cwd)
        skills = tuple(load_skills(resource_paths))
        prompt_templates = tuple(load_prompt_templates(resource_paths))
        system = (
            config.system
            if config.system is not None
            else build_system_prompt(
                BuildSystemPromptOptions(
                    cwd=config.cwd,
                    tools=tools,
                    skills=skills,
                    custom_prompt=config.custom_system_prompt,
                    append_system_prompt=config.append_system_prompt,
                    context_files=config.context_files,
                )
            )
        )
        harness = AgentHarness(
            AgentHarnessConfig(
                provider=config.provider,
                model=state.model or config.model,
                system=system,
                tools=tools,
            ),
            messages=state.messages,
        )
        return cls(
            config,
            state=state,
            harness=harness,
            last_parent_id=_last_parent_id_from_state(state),
            skills=skills,
            prompt_templates=prompt_templates,
            command_registry=config.command_registry,
        )

    @property
    def cwd(self) -> Path:
        """Return the session working directory."""
        return self._config.cwd

    @property
    def model(self) -> str:
        """Return the active model for this session."""
        return self._harness.config.model

    @property
    def tools(self) -> tuple[AgentTool, ...]:
        """Return the tools available to the agent."""
        return tuple(self._harness.config.tools)

    @property
    def messages(self) -> tuple[AgentMessage, ...]:
        """Return the restored/current transcript."""
        return self._harness.messages

    @property
    def state(self) -> SessionState:
        """Return the last replayed durable session state."""
        return self._state

    @property
    def storage(self) -> SessionStorage:
        """Return the backing session storage."""
        return self._config.storage

    @property
    def skills(self) -> tuple[Skill, ...]:
        """Return loaded skills."""
        return self._skills

    @property
    def prompt_templates(self) -> tuple[PromptTemplate, ...]:
        """Return loaded prompt templates."""
        return self._prompt_templates

    @property
    def session_id(self) -> str | None:
        """Return this session's manager id, if indexed."""
        return self._config.session_id

    @property
    def session_manager(self) -> SessionManager | None:
        """Return the session manager, if available."""
        return self._config.session_manager

    def cancel(self) -> None:
        """Cancel the currently running agent turn, if any."""
        self._harness.cancel()

    def handle_command(self, text: str) -> CommandResult:
        """Handle minimal coding-session slash commands.

        This is intentionally tiny. Later phases can replace it with a full Pi-like
        command registry without changing the persistence boundary.
        """
        return self._command_registry.execute(self, text)

    def expand_prompt_text(self, text: str) -> str:
        """Expand prompt text using loaded markdown resources."""
        expanded_skill = expand_skill_command(text, self._skills)
        return expanded_skill if expanded_skill is not None else text

    async def prompt(self, content: str) -> AsyncIterator[AgentEvent]:
        """Append a user prompt, run the agent, and persist new messages."""
        try:
            expanded_content = self.expand_prompt_text(content)
        except ResourceError:
            raise
        before_count = len(self._harness.messages)
        async for event in self._harness.prompt(expanded_content):
            yield event
        await self._persist_new_messages(before_count)

    async def continue_(self) -> AsyncIterator[AgentEvent]:
        """Continue the agent from restored state and persist new messages."""
        before_count = len(self._harness.messages)
        async for event in self._harness.continue_():
            yield event
        await self._persist_new_messages(before_count)

    async def _persist_new_messages(self, before_count: int) -> None:
        new_messages = self._harness.messages[before_count:]
        last_message_entry_id: str | None = None
        for message in new_messages:
            entry = MessageEntry(parent_id=self._last_parent_id, message=message)
            await self._config.storage.append(entry)
            self._last_parent_id = entry.id
            last_message_entry_id = entry.id

        if last_message_entry_id is not None:
            leaf = LeafEntry(parent_id=last_message_entry_id, entry_id=last_message_entry_id)
            await self._config.storage.append(leaf)

        entries = await self._config.storage.read_all()
        self._state = SessionState.from_entries(entries)
        if self._config.session_id is not None and self._config.session_manager is not None:
            self._config.session_manager.touch_session(self._config.session_id, model=self.model)


def _last_parent_id_from_state(state: SessionState) -> str | None:
    if state.active_leaf_id is not None:
        return state.active_leaf_id
    if state.entries:
        return state.entries[-1].id
    return None


def default_session_path(cwd: Path) -> Path:
    """Return Tau's default user-home session path for a project cwd."""
    return TauPaths().default_session_path(cwd)


def jsonl_session_storage(path: str | Path) -> JsonlSessionStorage:
    """Convenience factory for local JSONL coding-session storage."""
    return JsonlSessionStorage(path)
