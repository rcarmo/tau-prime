"""Local named-session chat routing for Tau Web."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Never

from tau_agent.types import JSONObject, JSONValue
from tau_coding.agent_pool import AgentPoolError, AsyncAgentPool
from tau_web.runtime import DurableAgentRuntime
from tau_web.sqlite.repositories import DeliveryMode, DeliveryRecord, DeliveryRepository
from tau_web.sqlite.sessions import SessionRecord, SessionRepository, validate_agent_name


@dataclass(frozen=True, slots=True)
class ChatDispatchResult:
    """Durable outcome for one routed chat submission."""

    delivery: DeliveryRecord
    run_id: str | None = None
    queue_id: str | None = None

    @property
    def delivery_id(self) -> str:
        return self.delivery.delivery_id

    @property
    def mode(self) -> DeliveryMode:
        return self.delivery.mode

    @property
    def status(self) -> str:
        return self.delivery.status

    @property
    def transport(self) -> str:
        return self.delivery.transport

    @property
    def target_session_id(self) -> str | None:
        return self.delivery.target_session_id

    @property
    def target_address(self) -> str | None:
        return self.delivery.target_address

    @property
    def error(self) -> JSONObject | None:
        return self.delivery.error


class ChatRoutingError(RuntimeError):
    """Raised when a durable chat delivery is rejected or fails dispatch."""

    def __init__(self, delivery: DeliveryRecord) -> None:
        self.delivery = delivery
        error = delivery.error or {}

        raw_code = error.get("code")
        self.code = raw_code if isinstance(raw_code, str) and raw_code else "chat_routing_error"

        raw_message = error.get("message")
        self._message = (
            raw_message if isinstance(raw_message, str) and raw_message else "Chat routing failed."
        )

        raw_details = error.get("details")
        self.details = _object_or_empty(raw_details)
        super().__init__(self._message)

    @property
    def message(self) -> str:
        return self._message

    @property
    def error(self) -> JSONObject | None:
        return self.delivery.error


@dataclass(frozen=True, slots=True)
class _TargetSelection:
    address: str
    transport: str
    is_remote: bool


class ChatRouter:
    """Resolve local named-session targets and durably dispatch chat messages."""

    def __init__(
        self,
        sessions: SessionRepository,
        deliveries: DeliveryRepository,
        runtime: DurableAgentRuntime,
        pool: AsyncAgentPool,
    ) -> None:
        self._sessions = sessions
        self._deliveries = deliveries
        self._runtime = runtime
        self._pool = pool

    async def resolve_target(
        self,
        *,
        target_address: str | None = None,
        target_chat_jid: str | None = None,
        target_agent_name: str | None = None,
    ) -> tuple[str, SessionRecord | None]:
        """Return the canonical target address and any active local session it resolves to."""
        selection = _select_target(
            target_address=target_address,
            target_chat_jid=target_chat_jid,
            target_agent_name=target_agent_name,
        )
        if selection.is_remote:
            return selection.address, None
        return selection.address, await self._sessions.resolve(selection.address)

    async def send(
        self,
        source_session_id: str,
        content: str,
        *,
        target_address: str | None = None,
        target_chat_jid: str | None = None,
        target_agent_name: str | None = None,
        mode: DeliveryMode = "auto",
    ) -> ChatDispatchResult:
        """Create one delivery row, resolve its local target, and dispatch by mode."""
        if mode not in {"auto", "queue", "steer"}:
            raise ValueError(f"Unsupported delivery mode: {mode}")

        await self._require_active_source_session(source_session_id)
        selection = _select_target(
            target_address=target_address,
            target_chat_jid=target_chat_jid,
            target_agent_name=target_agent_name,
        )
        created = await self._deliveries.create(
            source_session_id=source_session_id,
            mode=mode,
            content=content,
            target_address=selection.address,
            transport=selection.transport,
            status="pending",
        )

        if selection.is_remote:
            await self._reject(
                created,
                code="remote_transport_unsupported",
                message="Remote chat routing is not supported yet.",
                target_address=selection.address,
                transport=selection.transport,
            )

        target = await self._sessions.resolve(selection.address)
        if target is None:
            await self._reject(
                created,
                code="target_not_found",
                message="The target session is not active.",
                target_address=selection.address,
            )

        resolved = await self._deliveries.resolve_target(created.delivery_id, target.session_id)
        try:
            snapshot = self._pool.snapshot(target.session_id)
        except AgentPoolError:
            await self._reject(
                resolved,
                code="target_not_active",
                message="The target session is not active.",
                target_address=selection.address,
            )

        if mode == "auto":
            try:
                handle = await self._runtime.submit_prompt(target.session_id, content)
            except Exception:
                await self._fail(
                    resolved,
                    code="dispatch_failed",
                    message="The target session could not be dispatched.",
                    target_address=selection.address,
                )

            dispatched = await self._deliveries.update_status(
                resolved.delivery_id,
                status="dispatched",
            )
            return ChatDispatchResult(delivery=dispatched, run_id=handle.run_id)

        if mode == "queue":
            try:
                queued = await self._runtime.enqueue(
                    target.session_id,
                    content,
                    queue_kind="follow_up",
                    source_session_id=source_session_id,
                )
            except Exception:
                await self._fail(
                    resolved,
                    code="queue_failed",
                    message="The target session could not accept the queued message.",
                    target_address=selection.address,
                )

            accepted = await self._deliveries.update_status(
                resolved.delivery_id,
                status="accepted",
            )
            return ChatDispatchResult(delivery=accepted, queue_id=queued.queue_id)

        current_run_id = snapshot.current_run_id
        if current_run_id is None:
            await self._reject(
                resolved,
                code="target_not_running",
                message="The target session is not running.",
                target_address=selection.address,
            )

        try:
            queued = await self._runtime.steer(
                current_run_id,
                content,
                source_session_id=source_session_id,
            )
        except Exception:
            await self._fail(
                resolved,
                code="steer_failed",
                message="The target session could not accept the steering message.",
                target_address=selection.address,
            )

        if queued.consumed_at is not None:
            updated = await self._deliveries.update_status(
                resolved.delivery_id,
                status="completed",
            )
        else:
            updated = await self._deliveries.update_status(
                resolved.delivery_id,
                status="accepted",
            )
        return ChatDispatchResult(
            delivery=updated,
            run_id=current_run_id,
            queue_id=queued.queue_id,
        )

    async def _require_active_source_session(self, source_session_id: str) -> SessionRecord:
        source = await self._sessions.resolve(f"session:{source_session_id}")
        if source is None:
            raise ValueError("Source session must exist and be active.")
        try:
            self._pool.snapshot(source.session_id)
        except AgentPoolError:
            raise ValueError("Source session must exist and be active.") from None
        return source

    async def _reject(
        self,
        delivery: DeliveryRecord,
        *,
        code: str,
        message: str,
        **details: JSONValue,
    ) -> Never:
        rejected = await self._deliveries.update_status(
            delivery.delivery_id,
            status="rejected",
            error=_error_payload(code, message, **details),
        )
        raise ChatRoutingError(rejected)

    async def _fail(
        self,
        delivery: DeliveryRecord,
        *,
        code: str,
        message: str,
        **details: JSONValue,
    ) -> Never:
        failed = await self._deliveries.update_status(
            delivery.delivery_id,
            status="failed",
            error=_error_payload(code, message, **details),
        )
        raise ChatRoutingError(failed)


def _select_target(
    *,
    target_address: str | None,
    target_chat_jid: str | None,
    target_agent_name: str | None,
) -> _TargetSelection:
    selectors: list[tuple[str, _TargetSelection]] = []

    if target_agent_name is not None and target_agent_name.strip():
        selectors.append(("target_agent_name", _agent_name_selection(target_agent_name)))
    if target_chat_jid is not None and target_chat_jid.strip():
        selectors.append(("target_chat_jid", _chat_jid_selection(target_chat_jid)))
    if target_address is not None and target_address.strip():
        selectors.append(("target_address", _address_selection(target_address)))

    if len(selectors) != 1:
        provided = ", ".join(name for name, _ in selectors) or "none"
        raise ValueError(f"Exactly one non-blank target selector is required; received {provided}.")

    return selectors[0][1]


def _agent_name_selection(value: str) -> _TargetSelection:
    return _TargetSelection(
        address=f"@{validate_agent_name(value)}",
        transport="local",
        is_remote=False,
    )


def _chat_jid_selection(value: str) -> _TargetSelection:
    chat_jid = _canonical_chat_jid_value(value)
    return _TargetSelection(
        address=f"chat_jid:{chat_jid}",
        transport="local",
        is_remote=False,
    )


def _address_selection(value: str) -> _TargetSelection:
    address = _require_non_blank(value, field="Target address")
    if "!" not in address:
        return _TargetSelection(
            address=_canonical_local_address(address),
            transport="local",
            is_remote=False,
        )
    if address.count("!") != 1:
        raise ValueError("Target address must contain at most one transport hop.")
    raw_transport, _, raw_destination = address.partition("!")
    transport = _non_blank(raw_transport) or "remote"
    destination = _canonical_local_address(
        _require_non_blank(raw_destination, field="Remote target address")
    )
    return _TargetSelection(
        address=f"{transport}!{destination}",
        transport=transport,
        is_remote=True,
    )


def _canonical_local_address(value: str) -> str:
    normalized = _require_non_blank(value, field="Target address")
    if normalized.startswith("@"):
        return f"@{validate_agent_name(normalized)}"
    if normalized.startswith("chat_jid:"):
        return f"chat_jid:{_canonical_chat_jid_value(normalized)}"
    if normalized.startswith("session:"):
        session_id = _require_non_blank(normalized.removeprefix("session:"), field="Session id")
        return f"session:{session_id}"
    return normalized


def _canonical_chat_jid_value(value: str) -> str:
    normalized = _require_non_blank(value, field="Chat JID")
    if normalized.startswith("chat_jid:"):
        normalized = normalized.removeprefix("chat_jid:")
    return _require_non_blank(normalized, field="Chat JID")


def _require_non_blank(value: str, *, field: str) -> str:
    normalized = _non_blank(value)
    if normalized is None:
        raise ValueError(f"{field} must be non-blank.")
    return normalized


def _non_blank(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized if normalized else None


def _error_payload(code: str, message: str, **details: JSONValue) -> JSONObject:
    payload: JSONObject = {
        "code": code,
        "message": message,
    }
    if details:
        payload["details"] = details
    return payload


def _object_or_empty(value: JSONValue | None) -> JSONObject:
    if value is None:
        return {}
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return value
    return {}
