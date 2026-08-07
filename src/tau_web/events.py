"""Canonical Tau Web event projection types and durable projector service."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, cast
from uuid import UUID, uuid4

from tau_agent import AgentEvent, MessageEndEvent
from tau_agent.types import JSONObject
from tau_ai.usage import usage_cost_microunits
from tau_coding.provider_catalog import catalog_model_pricing
from tau_web.sqlite.repositories import TimelineMessageRepository, UsageRepository
from tau_web.sqlite.sessions import SessionRepository

_CAMEL_BOUNDARY_1 = re.compile(r"(.)([A-Z][a-z]+)")
_CAMEL_BOUNDARY_2 = re.compile(r"([a-z0-9])([A-Z])")


@dataclass(frozen=True, slots=True)
class WebEventEnvelope:
    """Immutable canonical envelope projected from one agent event."""

    event_id: UUID
    type: str
    session_id: str
    run_id: str
    sequence: int
    payload: JSONObject
    created_at: str

    def __post_init__(self) -> None:
        if self.sequence <= 0:
            raise ValueError("Event sequence must be 1-based")


def build_invalidation_envelope(
    *,
    event_type: str,
    session_id: str,
    payload: JSONObject,
) -> WebEventEnvelope:
    """Build an ephemeral namespaced invalidation for broker fan-out."""
    if "." not in event_type:
        raise ValueError("Invalidation event types must be namespaced")
    return WebEventEnvelope(
        event_id=uuid4(),
        type=event_type,
        session_id=session_id,
        run_id="",
        sequence=1,
        payload=payload,
        created_at=datetime.now(UTC).isoformat(),
    )


class EventProjectorCallback(Protocol):
    """Async callback invoked once for each canonical runtime event."""

    async def __call__(
        self,
        session_id: str,
        run_id: str,
        sequence: int,
        event: AgentEvent,
    ) -> None: ...


class WebEventObserverCallback(Protocol):
    """Async observer notified after one envelope has been durably projected."""

    async def __call__(self, envelope: WebEventEnvelope) -> None: ...


class EventProjector:
    """Build canonical envelopes, persist durable projections, and fan out observers."""

    def __init__(
        self,
        timeline: TimelineMessageRepository,
        usage: UsageRepository | None = None,
        sessions: SessionRepository | None = None,
    ) -> None:
        self._timeline = timeline
        self._usage = usage
        self._sessions = sessions
        self._observers: list[WebEventObserverCallback] = []

    @property
    def timeline(self) -> TimelineMessageRepository:
        return self._timeline

    def subscribe(self, observer: WebEventObserverCallback) -> Callable[[], None]:
        self._observers.append(observer)

        def unsubscribe() -> None:
            try:
                self._observers.remove(observer)
            except ValueError:
                return

        return unsubscribe

    async def project(
        self,
        session_id: str,
        run_id: str,
        sequence: int,
        event: AgentEvent,
    ) -> None:
        envelope = build_web_event_envelope(
            session_id=session_id,
            run_id=run_id,
            sequence=sequence,
            event=event,
        )
        if isinstance(event, MessageEndEvent):
            await self._timeline.project_message_end(
                session_id=session_id,
                run_id=run_id,
                sequence=sequence,
                message=event.message,
                created_at=envelope.created_at,
            )
            if event.usage is not None and self._usage is not None and self._sessions is not None:
                session = await self._sessions.get(session_id)
                if session is not None:
                    pricing = catalog_model_pricing(session.provider_name, session.model)
                    cost = (
                        usage_cost_microunits(event.usage, pricing)
                        if pricing is not None
                        else None
                    )
                    await self._usage.record(
                        session_id,
                        run_id=run_id,
                        provider_name=session.provider_name,
                        model=session.model,
                        input_tokens=event.usage.input_tokens,
                        output_tokens=event.usage.output_tokens,
                        cached_input_tokens=event.usage.cache_read_tokens,
                        cache_write_tokens=event.usage.cache_write_tokens,
                        cache_write_1h_tokens=event.usage.cache_write_1h_tokens,
                        cost_microunits=cost,
                    )
        await self._notify_observers(envelope)

    async def _notify_observers(self, envelope: WebEventEnvelope) -> None:
        for observer in tuple(self._observers):
            try:
                await observer(envelope)
            except Exception:
                continue


def build_web_event_envelope(
    *,
    session_id: str,
    run_id: str,
    sequence: int,
    event: AgentEvent,
    event_id: UUID | None = None,
    created_at: str | None = None,
) -> WebEventEnvelope:
    """Build one immutable envelope around a canonical agent event."""
    payload = event.model_dump(mode="json", exclude_none=True)
    if not isinstance(payload, dict) or not all(isinstance(key, str) for key in payload):
        raise TypeError("Agent event payload must be a JSON object")
    return WebEventEnvelope(
        event_id=event_id or uuid4(),
        type=web_event_type(event),
        session_id=session_id,
        run_id=run_id,
        sequence=sequence,
        payload=cast(JSONObject, payload),
        created_at=created_at or _timestamp(),
    )


def canonical_agent_event_type(event: AgentEvent) -> str:
    """Return the stable canonical type name for one agent event."""
    discriminator = getattr(event, "type", None)
    if isinstance(discriminator, str) and discriminator.strip():
        return discriminator
    return _camel_to_snake(event.__class__.__name__)


def web_event_type(event: AgentEvent) -> str:
    """Return the Tau Web namespaced event type for one agent event."""
    return f"tau.agent.{canonical_agent_event_type(event)}"


def _camel_to_snake(name: str) -> str:
    first_pass = _CAMEL_BOUNDARY_1.sub(r"\1_\2", name)
    return _CAMEL_BOUNDARY_2.sub(r"\1_\2", first_pass).casefold()


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


__all__ = [
    "EventProjector",
    "EventProjectorCallback",
    "WebEventEnvelope",
    "WebEventObserverCallback",
    "build_web_event_envelope",
    "canonical_agent_event_type",
    "web_event_type",
]
