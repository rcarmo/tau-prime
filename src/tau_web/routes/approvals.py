"""Browser tool-permission and security-audit REST routes."""

from __future__ import annotations

from dataclasses import asdict

from aiohttp import web

from tau_web.middleware import REQUEST_ID_KEY
from tau_web.routes.common import (
    json_response,
    require_found,
    require_json_body,
    require_non_empty_text,
    services_for,
)


def setup_routes(app: web.Application) -> None:
    app.router.add_get("/api/sessions/{session_id}/approvals", list_approvals)
    app.router.add_post("/api/approvals/{approval_id}", resolve_approval)
    app.router.add_get("/api/audit", list_audit_records)


async def list_approvals(request: web.Request) -> web.Response:
    services = services_for(request)
    session_id = request.match_info["session_id"]
    require_found(
        await services.sessions.get(session_id), resource="session", identifier=session_id
    )
    pending = services.approvals.list_pending(session_id=session_id)
    return json_response({"approvals": [item.to_json() for item in pending]})


async def resolve_approval(request: web.Request) -> web.Response:
    body = await require_json_body(request, required_fields=("decision",))
    decision = require_non_empty_text(body, "decision")
    if decision not in {"allow", "deny"}:
        raise web.HTTPBadRequest(reason="Approval decision must be 'allow' or 'deny'.")
    services = services_for(request)
    approval_id = request.match_info["approval_id"]
    resolved = await services.approvals.resolve(
        approval_id,
        decision,
        actor_id=request.remote,
        request_id=request.get(REQUEST_ID_KEY),
    )
    require_found(resolved, resource="tool approval", identifier=approval_id)
    return json_response({"approval_id": approval_id, "decision": decision})


async def list_audit_records(request: web.Request) -> web.Response:
    raw_limit = request.query.get("limit", "100")
    try:
        limit = int(raw_limit)
    except ValueError as exc:
        raise web.HTTPBadRequest(reason="Audit limit must be an integer.") from exc
    if not 1 <= limit <= 500:
        raise web.HTTPBadRequest(reason="Audit limit must be between 1 and 500.")
    records = await services_for(request).audit.list(
        session_id=request.query.get("session_id"),
        limit=limit,
    )
    return json_response({"records": [asdict(record) for record in records]})


__all__ = ["setup_routes"]
