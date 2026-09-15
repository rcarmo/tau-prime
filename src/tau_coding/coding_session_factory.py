"""Reusable factory for building and loading coding sessions."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol

from tau_agent.session import SessionStorage
from tau_agent.tools import AgentTool
from tau_ai import LLMObserver, ModelProvider
from tau_coding.commands import CommandRegistry
from tau_coding.live_session_manager import CodingSessionManager
from tau_coding.paths import TauPaths
from tau_coding.provider_config import (
    ProviderConfig,
    ProviderConfigError,
    ProviderSettings,
    load_provider_settings,
    provider_default_thinking_level,
    resolve_provider_selection,
)
from tau_coding.provider_runtime import create_model_provider
from tau_coding.resources import TauResourcePaths
from tau_coding.session import CodingSession, CodingSessionConfig
from tau_coding.system_prompt import ProjectContextFile
from tau_coding.thinking import DEFAULT_THINKING_LEVEL, ThinkingLevel


class _ProviderSettingsLoader(Protocol):
    """Load provider settings for one factory-bound session."""

    def __call__(self, paths: TauPaths | None = None) -> ProviderSettings:
        """Return provider settings for the active Tau paths."""
        ...


class _ModelProviderBuilder(Protocol):
    """Build a runtime model provider from durable provider config."""

    def __call__(
        self,
        provider: ProviderConfig,
        *,
        model: str,
        thinking_level: ThinkingLevel | None = None,
        llm_observer: LLMObserver | None = None,
    ) -> ModelProvider:
        """Create a provider ready for ``CodingSessionConfig``."""
        ...


type ExtraToolsFactory = Callable[
    ["CodingSessionFactoryBinding"], Sequence[AgentTool]
]
type TurnContextProvider = Callable[[], Awaitable[str | None]]
type TurnContextProviderFactory = Callable[
    ["CodingSessionFactoryBinding"], TurnContextProvider | None
]


class _CodingSessionLoader(Protocol):
    """Async loader that turns ``CodingSessionConfig`` into a session."""

    def __call__(self, config: CodingSessionConfig) -> Awaitable[CodingSession]:
        """Load one coding session from the provided config."""
        ...


@dataclass(frozen=True, slots=True)
class CodingSessionPromptConfig:
    """Immutable prompt defaults shared across sessions."""

    system: str | None = None
    custom_system_prompt: str | None = None
    append_system_prompt: str | None = None
    context_files: tuple[ProjectContextFile, ...] = ()


@dataclass(frozen=True, slots=True)
class CodingSessionCompactionConfig:
    """Immutable compaction defaults shared across sessions."""

    auto_compact_token_threshold: int | None = None
    auto_compact_enabled: bool = True
    provider_compaction_enabled: bool = True
    compaction_strategy: Literal["summary", "pipelined"] = "pipelined"


@dataclass(frozen=True, slots=True)
class CodingSessionFactoryConfig:
    """Immutable defaults applied to every loaded coding session."""

    prompts: CodingSessionPromptConfig = field(default_factory=CodingSessionPromptConfig)
    tools: tuple[AgentTool, ...] | None = None
    extra_tools_factory: ExtraToolsFactory | None = None
    turn_context_provider_factory: TurnContextProviderFactory | None = None
    resource_paths: TauResourcePaths | None = None
    command_registry: CommandRegistry | None = None
    compaction: CodingSessionCompactionConfig = field(default_factory=CodingSessionCompactionConfig)
    thinking_level: ThinkingLevel | None = None
    # Prepended to default sh tool commands for the current sandbox execution setting.
    shell_command_prefix: str | None = None
    llm_observer: LLMObserver | None = None


@dataclass(frozen=True, slots=True)
class CodingSessionFactoryRequest:
    """Per-session inputs supplied to ``CodingSessionFactory``."""

    cwd: Path
    storage: SessionStorage
    session_id: str | None = None
    session_manager: CodingSessionManager | None = None
    provider_config: ProviderConfig | None = None
    provider_name: str | None = None
    model: str | None = None
    index_on_first_persist: bool = False
    provider: ModelProvider | None = None


@dataclass(frozen=True, slots=True)
class CodingSessionFactoryBinding:
    """Resolved per-session inputs ready for ``CodingSessionConfig`` creation."""

    cwd: Path
    storage: SessionStorage
    provider: ModelProvider
    provider_name: str
    model: str
    thinking_level: ThinkingLevel
    session_id: str | None = None
    session_manager: CodingSessionManager | None = None
    provider_config: ProviderConfig | None = None
    provider_settings: ProviderSettings | None = None
    index_on_first_persist: bool = False


class CodingSessionFactory:
    """Build and load ``CodingSession`` instances without duplicating load logic."""

    def __init__(
        self,
        config: CodingSessionFactoryConfig | None = None,
        *,
        provider_settings: ProviderSettings | None = None,
        provider_settings_loader: _ProviderSettingsLoader = load_provider_settings,
        provider_builder: _ModelProviderBuilder = create_model_provider,
        session_loader: _CodingSessionLoader = CodingSession.load,
    ) -> None:
        self._config = config or CodingSessionFactoryConfig()
        self._provider_settings = provider_settings
        self._provider_settings_loader = provider_settings_loader
        self._provider_builder = provider_builder
        self._session_loader = session_loader

    @property
    def config(self) -> CodingSessionFactoryConfig:
        """Return immutable factory defaults."""
        return self._config

    def bind(self, request: CodingSessionFactoryRequest) -> CodingSessionFactoryBinding:
        """Resolve one per-session request into a concrete binding."""
        provider_settings = self._provider_settings
        provider_config = request.provider_config
        provider_name = request.provider_name
        model = request.model

        if provider_config is None and (
            provider_settings is not None
            or request.provider is None
            or provider_name is None
            or model is None
        ):
            provider_settings = provider_settings or self._provider_settings_loader(
                _provider_settings_paths(self._config.resource_paths)
            )
            selection = resolve_provider_selection(
                provider_settings,
                provider_name=provider_name,
                model=model,
            )
            provider_config = selection.provider
            provider_name = selection.provider.name
            model = selection.model

        if provider_config is not None:
            provider_name = provider_name or provider_config.name
            model = model or provider_config.default_model

        if provider_name is None:
            raise ValueError("provider_name must be supplied or resolvable from provider settings")
        if not model:
            raise ProviderConfigError(f"Provider {provider_name} does not define a default model")

        thinking_level = self._config.thinking_level
        if thinking_level is None and provider_config is not None:
            thinking_level = provider_default_thinking_level(provider_config, model=model)
        if thinking_level is None:
            thinking_level = DEFAULT_THINKING_LEVEL

        provider = request.provider
        if provider is None:
            if provider_config is None:
                raise ValueError(
                    "provider_config or provider settings are required "
                    "when provider is not injected"
                )
            provider = self._provider_builder(
                provider_config,
                model=model,
                thinking_level=thinking_level,
                llm_observer=self._config.llm_observer,
            )

        return CodingSessionFactoryBinding(
            cwd=request.cwd,
            storage=request.storage,
            provider=provider,
            provider_name=provider_name,
            model=model,
            thinking_level=thinking_level,
            session_id=request.session_id,
            session_manager=request.session_manager,
            provider_config=provider_config,
            provider_settings=provider_settings,
            index_on_first_persist=request.index_on_first_persist,
        )

    def build_config(self, binding: CodingSessionFactoryBinding) -> CodingSessionConfig:
        """Build a ``CodingSessionConfig`` from resolved factory inputs."""
        extra_tools = (
            tuple(self._config.extra_tools_factory(binding))
            if self._config.extra_tools_factory is not None
            else ()
        )
        turn_context_provider = (
            self._config.turn_context_provider_factory(binding)
            if self._config.turn_context_provider_factory is not None
            else None
        )
        return CodingSessionConfig(
            provider=binding.provider,
            model=binding.model,
            storage=binding.storage,
            cwd=binding.cwd,
            system=self._config.prompts.system,
            custom_system_prompt=self._config.prompts.custom_system_prompt,
            append_system_prompt=self._config.prompts.append_system_prompt,
            context_files=self._config.prompts.context_files,
            tools=list(self._config.tools) if self._config.tools is not None else None,
            extra_tools=extra_tools,
            turn_context_provider=turn_context_provider,
            resource_paths=self._config.resource_paths,
            session_id=binding.session_id,
            session_manager=binding.session_manager,
            command_registry=self._config.command_registry,
            provider_name=binding.provider_name,
            provider_settings=binding.provider_settings,
            runtime_provider_config=binding.provider_config,
            auto_compact_token_threshold=(self._config.compaction.auto_compact_token_threshold),
            auto_compact_enabled=self._config.compaction.auto_compact_enabled,
            provider_compaction_enabled=self._config.compaction.provider_compaction_enabled,
            compaction_strategy=self._config.compaction.compaction_strategy,
            thinking_level=binding.thinking_level,
            index_on_first_persist=binding.index_on_first_persist,
            shell_command_prefix=self._config.shell_command_prefix,
            llm_observer=self._config.llm_observer,
        )

    async def load(self, request: CodingSessionFactoryRequest) -> CodingSession:
        """Resolve one request, build ``CodingSessionConfig``, and await load."""
        binding = self.bind(request)
        return await self._session_loader(self.build_config(binding))


def _provider_settings_paths(resource_paths: TauResourcePaths | None) -> TauPaths | None:
    """Derive Tau home paths used while loading provider settings."""
    if resource_paths is None:
        return None
    if resource_paths.paths is not None:
        return resource_paths.paths
    if resource_paths.agents_root is None:
        return TauPaths(home=resource_paths.root)
    return TauPaths(home=resource_paths.root, agents_home=resource_paths.agents_root)


__all__ = [
    "CodingSessionCompactionConfig",
    "CodingSessionFactory",
    "CodingSessionFactoryBinding",
    "CodingSessionFactoryConfig",
    "CodingSessionFactoryRequest",
    "CodingSessionPromptConfig",
    "ExtraToolsFactory",
    "TurnContextProvider",
    "TurnContextProviderFactory",
]
