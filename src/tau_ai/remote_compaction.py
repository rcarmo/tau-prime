"""Provider-native compaction contracts and persisted canonical state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from tau_agent.messages import AgentMessage
from tau_agent.tools import AgentTool
from tau_agent.types import JSONValue
from tau_ai.provider import CancellationToken

REMOTE_COMPACTION_KIND = "tau.remote_compaction"
REMOTE_COMPACTION_VERSION = 1
REMOTE_COMPACTION_SENTINEL = (
    "[Tau provider-native compaction state; opaque canonical context is replayed at request time.]"
)


@dataclass(frozen=True, slots=True)
class RemoteCompactionState:
    """Validated opaque provider state that must only be replayed compatibly."""

    provider: str
    model: str
    base_url: str
    output: tuple[dict[str, JSONValue], ...]

    def to_details(self) -> dict[str, JSONValue]:
        return {
            "kind": REMOTE_COMPACTION_KIND,
            "version": REMOTE_COMPACTION_VERSION,
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url.rstrip("/"),
            "output": [dict(item) for item in self.output],
        }

    @classmethod
    def from_details(cls, details: object) -> RemoteCompactionState | None:
        if not isinstance(details, dict):
            return None
        if details.get("kind") != REMOTE_COMPACTION_KIND or details.get("version") != 1:
            return None
        provider = details.get("provider")
        model = details.get("model")
        base_url = details.get("base_url")
        output = details.get("output")
        if not all(isinstance(item, str) and item for item in (provider, model, base_url)):
            return None
        if not isinstance(output, list) or not output:
            return None
        canonical: list[dict[str, JSONValue]] = []
        has_compaction = False
        for item in output:
            if not isinstance(item, dict):
                return None
            item_type = item.get("type")
            if item_type in {"compaction", "compaction_summary", "context_compaction"}:
                encrypted = item.get("encrypted_content")
                if not isinstance(encrypted, str) or not encrypted:
                    return None
                has_compaction = True
            canonical.append(item)
        if not has_compaction:
            return None
        return cls(
            provider=provider,  # type: ignore[arg-type]
            model=model,  # type: ignore[arg-type]
            base_url=base_url.rstrip("/"),  # type: ignore[union-attr]
            output=tuple(canonical),
        )


@runtime_checkable
class RemoteCompactionProvider(Protocol):
    """Optional capability implemented only by verified native endpoints."""

    async def compact_context(
        self,
        *,
        model: str,
        system: str,
        messages: list[AgentMessage],
        tools: list[AgentTool],
        previous: RemoteCompactionState | None = None,
        signal: CancellationToken | None = None,
    ) -> RemoteCompactionState | None:
        """Return canonical remote state, or None when unavailable."""
