"""Host-owned browser permission prompts for agent tool execution."""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from math import isfinite
from typing import Literal
from uuid import uuid4

from tau_agent.tools import AgentTool, ToolApprovalCallback, ToolCall, ToolCancellationToken
from tau_agent.types import JSONObject
from tau_web.events import build_invalidation_envelope
from tau_web.security import redact_json
from tau_web.sqlite.repositories import AuditRepository
from tau_web.sse import EventBroker

ApprovalDecision = Literal["allow", "deny"]


@dataclass(frozen=True, slots=True)
class ToolApprovalRequest:
    approval_id: str
    session_id: str
    tool_call_id: str
    tool_name: str
    description: str
    arguments: JSONObject
    created_at: str

    def to_json(self) -> JSONObject:
        return asdict(self)


@dataclass(slots=True)
class _PendingApproval:
    request: ToolApprovalRequest
    future: asyncio.Future[bool]
    resolving: bool = False


class ToolApprovalManager:
    """Coordinate redacted browser prompts without persisting raw tool arguments."""

    def __init__(
        self,
        audit: AuditRepository,
        broker: EventBroker,
        *,
        timeout_seconds: float = 300.0,
    ) -> None:
        if not isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("Tool approval timeout must be positive and finite")
        self._audit = audit
        self._broker = broker
        self._timeout_seconds = timeout_seconds
        self._pending: dict[str, _PendingApproval] = {}
        self._closed = False

    def callback_for(self, session_id: str) -> ToolApprovalCallback:
        """Return one approval callback bound to a durable session."""

        async def approve(
            tool_call: ToolCall,
            tool: AgentTool,
            signal: ToolCancellationToken | None = None,
        ) -> bool:
            return await self.request(session_id, tool_call, tool, signal=signal)

        return approve

    def list_pending(self, *, session_id: str | None = None) -> tuple[ToolApprovalRequest, ...]:
        """Return pending requests in creation order, optionally for one session."""
        requests = (
            pending.request
            for pending in self._pending.values()
            if not pending.future.done()
            and not pending.resolving
            and (session_id is None or pending.request.session_id == session_id)
        )
        return tuple(
            sorted(requests, key=lambda request: (request.created_at, request.approval_id))
        )

    async def request(
        self,
        session_id: str,
        tool_call: ToolCall,
        tool: AgentTool,
        *,
        signal: ToolCancellationToken | None = None,
    ) -> bool:
        """Publish and await one browser decision, failing closed on cancellation."""
        if self._closed:
            return False
        arguments = redact_json(tool_call.arguments)
        if not isinstance(arguments, dict):
            raise TypeError("Tool arguments must remain a JSON object after redaction")
        request = ToolApprovalRequest(
            approval_id=uuid4().hex,
            session_id=session_id,
            tool_call_id=tool_call.id,
            tool_name=tool.name,
            description=tool.description,
            arguments=arguments,
            created_at=datetime.now(UTC).isoformat(),
        )
        future: asyncio.Future[bool] = asyncio.get_running_loop().create_future()
        self._pending[request.approval_id] = _PendingApproval(request=request, future=future)
        deadline = asyncio.get_running_loop().time() + self._timeout_seconds
        try:
            await self._audit.append(
                event_type="tool.approval.requested",
                actor_type="runtime",
                session_id=session_id,
                details={
                    "approval_id": request.approval_id,
                    "tool_call_id": request.tool_call_id,
                    "tool_name": request.tool_name,
                    "arguments": request.arguments,
                },
            )
            await self._publish("tau.approval.requested", request, decision=None)
            while not future.done():
                if signal is not None and signal.is_cancelled():
                    await self.cancel(request.approval_id, actor_id="runtime-cancel")
                    break
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    await self.cancel(request.approval_id, actor_id="runtime-timeout")
                    break
                await asyncio.wait((future,), timeout=min(0.2, remaining))
            return future.result()
        except asyncio.CancelledError:
            if not future.done():
                await asyncio.shield(
                    self.cancel(request.approval_id, actor_id="runtime-abort")
                )
            raise
        finally:
            self._pending.pop(request.approval_id, None)

    async def resolve(
        self,
        approval_id: str,
        decision: ApprovalDecision,
        *,
        actor_id: str | None = None,
        request_id: str | None = None,
    ) -> ToolApprovalRequest | None:
        """Resolve one pending prompt exactly once and audit the decision."""
        pending = self._pending.get(approval_id)
        if pending is None or pending.future.done() or pending.resolving:
            return None
        pending.resolving = True
        try:
            await self._record_resolution(
                pending.request,
                decision,
                actor_id=actor_id,
                request_id=request_id,
            )
        except BaseException:
            pending.resolving = False
            raise
        pending.future.set_result(decision == "allow")
        return pending.request

    async def cancel(
        self,
        approval_id: str,
        *,
        actor_id: str | None = "runtime-cancel",
        request_id: str | None = None,
    ) -> ToolApprovalRequest | None:
        """Fail closed by denying one pending approval."""
        return await self.resolve(
            approval_id,
            "deny",
            actor_id=actor_id,
            request_id=request_id,
        )

    async def shutdown(self) -> None:
        """Deny outstanding requests during host shutdown."""
        if self._closed:
            return
        self._closed = True
        for approval_id in tuple(self._pending):
            await self.cancel(approval_id, actor_id="runtime-shutdown")

    async def close(self) -> None:
        """Backward-compatible alias for :meth:`shutdown`."""
        await self.shutdown()

    async def _record_resolution(
        self,
        request: ToolApprovalRequest,
        decision: ApprovalDecision,
        *,
        actor_id: str | None,
        request_id: str | None = None,
    ) -> None:
        runtime_actors = {
            "runtime-abort",
            "runtime-cancel",
            "runtime-shutdown",
            "runtime-timeout",
        }
        await self._audit.append(
            event_type="tool.approval.resolved",
            actor_type="browser" if actor_id not in runtime_actors else "runtime",
            actor_id=actor_id,
            session_id=request.session_id,
            request_id=request_id,
            details={
                "approval_id": request.approval_id,
                "tool_call_id": request.tool_call_id,
                "tool_name": request.tool_name,
                "decision": decision,
            },
        )
        await self._publish("tau.approval.resolved", request, decision=decision)

    async def _publish(
        self,
        event_type: str,
        request: ToolApprovalRequest,
        *,
        decision: ApprovalDecision | None,
    ) -> None:
        payload = request.to_json()
        if decision is not None:
            payload["decision"] = decision
        await self._broker.publish(
            build_invalidation_envelope(
                event_type=event_type,
                session_id=request.session_id,
                payload=payload,
            )
        )


__all__ = ["ApprovalDecision", "ToolApprovalManager", "ToolApprovalRequest"]
