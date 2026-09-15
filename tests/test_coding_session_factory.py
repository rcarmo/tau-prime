from __future__ import annotations

import asyncio
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import pytest

import tau_coding as tau_coding_package
from tau_agent.session import JsonlSessionStorage
from tau_agent.tools import AgentTool, AgentToolResult, ToolCancellationToken
from tau_agent.types import JSONValue
from tau_ai import FakeProvider, LLMObserver, ModelProvider
from tau_coding.coding_session_factory import (
    CodingSessionCompactionConfig,
    CodingSessionFactory,
    CodingSessionFactoryBinding,
    CodingSessionFactoryConfig,
    CodingSessionFactoryRequest,
    CodingSessionPromptConfig,
)
from tau_coding.commands import CommandRegistry
from tau_coding.paths import TauPaths
from tau_coding.provider_config import (
    OpenAICompatibleProviderConfig,
    ProviderConfig,
    ProviderConfigError,
    ProviderSettings,
)
from tau_coding.resources import TauResourcePaths
from tau_coding.session import CodingSession, CodingSessionConfig
from tau_coding.session_manager import SessionManager
from tau_coding.system_prompt import ProjectContextFile
from tau_coding.thinking import DEFAULT_THINKING_LEVEL, ThinkingLevel


async def _tool_executor(
    arguments: Mapping[str, JSONValue],
    signal: ToolCancellationToken | None = None,
) -> AgentToolResult:
    del arguments, signal
    return AgentToolResult(tool_call_id="call-1", name="demo", ok=True, content="done")


def _tool() -> AgentTool:
    return AgentTool(
        name="demo",
        description="Demo tool.",
        input_schema={},
        executor=_tool_executor,
    )


def test_package_root_exports_factory_types() -> None:
    assert tau_coding_package.CodingSessionCompactionConfig is CodingSessionCompactionConfig
    assert tau_coding_package.CodingSessionFactory is CodingSessionFactory
    assert tau_coding_package.CodingSessionFactoryBinding is CodingSessionFactoryBinding
    assert tau_coding_package.CodingSessionFactoryConfig is CodingSessionFactoryConfig
    assert tau_coding_package.CodingSessionFactoryRequest is CodingSessionFactoryRequest
    assert tau_coding_package.CodingSessionPromptConfig is CodingSessionPromptConfig


def test_bind_resolves_default_provider_and_thinking_level(tmp_path: Path) -> None:
    provider_config = OpenAICompatibleProviderConfig(
        name="local",
        api_key_env="LOCAL_API_KEY",
        credential_name=None,
        models=("qwen",),
        default_model="qwen",
        thinking_levels=("off", "high"),
        thinking_models=("qwen",),
        thinking_default="high",
    )
    provider_settings = ProviderSettings(default_provider="local", providers=(provider_config,))
    built_provider = FakeProvider([])
    seen: list[tuple[ProviderConfig, str, ThinkingLevel | None]] = []

    def provider_builder(
        provider: ProviderConfig,
        *,
        model: str,
        thinking_level: ThinkingLevel | None = None,
        llm_observer: LLMObserver | None = None,
    ) -> ModelProvider:
        seen.append((provider, model, thinking_level))
        assert llm_observer is None
        return built_provider

    factory = CodingSessionFactory(
        provider_settings=provider_settings,
        provider_builder=provider_builder,
    )

    binding = factory.bind(
        CodingSessionFactoryRequest(
            cwd=tmp_path,
            storage=JsonlSessionStorage(tmp_path / "session.jsonl"),
        )
    )

    assert binding.provider is built_provider
    assert binding.provider_name == "local"
    assert binding.model == "qwen"
    assert binding.thinking_level == "high"
    assert binding.provider_config == provider_config
    assert binding.provider_settings == provider_settings
    assert seen == [(provider_config, "qwen", "high")]


def test_bind_loads_provider_settings_with_resource_paths(tmp_path: Path) -> None:
    tau_paths = TauPaths(home=tmp_path / ".tau", agents_home=tmp_path / ".agents")
    provider_settings = ProviderSettings(
        providers=(
            OpenAICompatibleProviderConfig(
                name="openai",
                models=("gpt-5",),
                default_model="gpt-5",
            ),
        )
    )
    seen_paths: list[TauPaths | None] = []

    def provider_settings_loader(paths: TauPaths | None = None) -> ProviderSettings:
        seen_paths.append(paths)
        return provider_settings

    factory = CodingSessionFactory(
        config=CodingSessionFactoryConfig(
            resource_paths=TauResourcePaths(root=tau_paths.home, paths=tau_paths)
        ),
        provider_settings_loader=provider_settings_loader,
        provider_builder=lambda provider, **_: FakeProvider([]),
    )

    binding = factory.bind(
        CodingSessionFactoryRequest(
            cwd=tmp_path,
            storage=JsonlSessionStorage(tmp_path / "session.jsonl"),
        )
    )

    assert seen_paths == [tau_paths]
    assert binding.provider_name == "openai"
    assert binding.model == "gpt-5"
    assert binding.provider_settings == provider_settings


def test_build_config_applies_factory_defaults(tmp_path: Path) -> None:
    tool = _tool()
    command_registry = CommandRegistry()
    context_file = ProjectContextFile(path="AGENTS.md", content="Follow the rules.")
    resource_paths = TauResourcePaths(root=tmp_path / ".tau")
    provider_config = OpenAICompatibleProviderConfig(
        name="openai",
        models=("gpt-5",),
        default_model="gpt-5",
    )
    provider_settings = ProviderSettings(providers=(provider_config,))
    observer = cast(LLMObserver, object())
    session_manager = SessionManager(
        TauPaths(home=tmp_path / ".tau-home", agents_home=tmp_path / ".agents-home")
    )
    built_provider = FakeProvider([])
    seen: list[tuple[ProviderConfig, str, ThinkingLevel | None, LLMObserver | None]] = []

    def provider_builder(
        provider: ProviderConfig,
        *,
        model: str,
        thinking_level: ThinkingLevel | None = None,
        llm_observer: LLMObserver | None = None,
    ) -> ModelProvider:
        seen.append((provider, model, thinking_level, llm_observer))
        return built_provider

    factory = CodingSessionFactory(
        config=CodingSessionFactoryConfig(
            prompts=CodingSessionPromptConfig(
                system="System prompt",
                custom_system_prompt="Custom prompt",
                append_system_prompt="Append prompt",
                context_files=(context_file,),
            ),
            tools=(tool,),
            resource_paths=resource_paths,
            command_registry=command_registry,
            compaction=CodingSessionCompactionConfig(
                auto_compact_token_threshold=512,
                auto_compact_enabled=False,
                provider_compaction_enabled=False,
                compaction_strategy="summary",
            ),
            thinking_level="low",
            shell_command_prefix="source ~/.profile &&",
            llm_observer=observer,
        ),
        provider_settings=provider_settings,
        provider_builder=provider_builder,
    )
    binding = factory.bind(
        CodingSessionFactoryRequest(
            cwd=tmp_path,
            storage=JsonlSessionStorage(tmp_path / "session.jsonl"),
            session_id="session-1",
            session_manager=session_manager,
            index_on_first_persist=True,
        )
    )

    config = factory.build_config(binding)

    assert binding.provider is built_provider
    assert binding.provider_name == "openai"
    assert binding.model == "gpt-5"
    assert binding.provider_config == provider_config
    assert binding.provider_settings == provider_settings
    assert binding.session_manager is session_manager
    assert seen == [(provider_config, "gpt-5", "low", observer)]
    assert config.provider is binding.provider
    assert config.model == "gpt-5"
    assert config.storage is binding.storage
    assert config.cwd == tmp_path
    assert config.system == "System prompt"
    assert config.custom_system_prompt == "Custom prompt"
    assert config.append_system_prompt == "Append prompt"
    assert config.context_files == (context_file,)
    assert config.tools == [tool]
    assert config.resource_paths == resource_paths
    assert config.session_id == "session-1"
    assert config.session_manager is session_manager
    assert config.command_registry is command_registry
    assert config.provider_name == "openai"
    assert config.provider_settings == provider_settings
    assert config.runtime_provider_config == provider_config
    assert config.auto_compact_token_threshold == 512
    assert config.auto_compact_enabled is False
    assert config.provider_compaction_enabled is False
    assert config.compaction_strategy == "summary"
    assert config.thinking_level == "low"
    assert config.index_on_first_persist is True
    assert config.shell_command_prefix == "source ~/.profile &&"
    assert config.llm_observer is observer


def test_bind_rejects_missing_provider_selection_with_clear_error(tmp_path: Path) -> None:
    factory = CodingSessionFactory(
        provider_settings=ProviderSettings(default_provider="missing", providers=())
    )

    with pytest.raises(ProviderConfigError, match="Unknown provider: missing"):
        factory.bind(
            CodingSessionFactoryRequest(
                cwd=tmp_path,
                storage=JsonlSessionStorage(tmp_path / "session.jsonl"),
            )
        )


@pytest.mark.anyio
async def test_load_builds_real_session_with_default_config(tmp_path: Path) -> None:
    factory = CodingSessionFactory()
    session = await factory.load(
        CodingSessionFactoryRequest(
            cwd=tmp_path,
            storage=JsonlSessionStorage(tmp_path / "session.jsonl"),
            provider=FakeProvider([]),
            provider_name="openai",
            model="gpt-5",
        )
    )

    try:
        assert session.model == "gpt-5"
        assert session.command_registry.get("quit") is not None
        tool_names = {tool.name for tool in session.tools}
        assert {"read", "sh"}.issubset(tool_names)
        assert session.system_prompt.strip()
    finally:
        await session.aclose()


def test_load_delegates_to_session_loader(tmp_path: Path) -> None:
    expected_session = cast(CodingSession, object())
    seen_configs: list[CodingSessionConfig] = []

    async def session_loader(config: CodingSessionConfig) -> CodingSession:
        seen_configs.append(config)
        return expected_session

    factory = CodingSessionFactory(session_loader=session_loader)
    session = asyncio.run(
        factory.load(
            CodingSessionFactoryRequest(
                cwd=tmp_path,
                storage=JsonlSessionStorage(tmp_path / "session.jsonl"),
                provider=FakeProvider([]),
                provider_name="openai",
                model="gpt-5",
                session_id="session-1",
            )
        )
    )

    assert session is expected_session
    assert len(seen_configs) == 1
    assert seen_configs[0].provider_name == "openai"
    assert seen_configs[0].model == "gpt-5"
    assert seen_configs[0].session_id == "session-1"
    assert seen_configs[0].thinking_level == DEFAULT_THINKING_LEVEL
