"""Session and alias REST routes for Tau Web."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aiohttp import web

from tau_agent.types import JSONObject
from tau_web.routes.common import (
    config_for,
    json_response,
    optional_json_object,
    optional_nullable_text,
    optional_path,
    optional_text,
    parse_bool,
    raise_for_repository_error,
    require_found,
    require_json_body,
    require_text,
    services_for,
)
from tau_web.services import TauWebServices
from tau_web.sqlite.sessions import SessionRecord


@dataclass(frozen=True, slots=True)
class SessionResource:
    session_id: str
    workspace_id: str
    workspace_root: Path
    agent_name: str
    title: str | None
    provider_name: str
    model: str
    thinking_level: str | None
    active_leaf_entry_id: str | None
    created_at: str
    updated_at: str
    archived_at: str | None
    metadata: JSONObject


@dataclass(frozen=True, slots=True)
class SessionListResource:
    sessions: tuple[SessionResource, ...]


async def list_sessions(request: web.Request) -> web.Response:
    include_archived = parse_bool(
        request.query.get("include_archived"),
        field="include_archived",
        default=False,
    )
    services = services_for(request)
    records = await services.sessions.list(include_archived=include_archived)
    resources = tuple([await _session_resource(services, record) for record in records])
    return json_response(SessionListResource(sessions=resources))


async def create_session(request: web.Request) -> web.Response:
    body = await require_json_body(
        request,
        required_fields=("provider_name", "model"),
        optional_fields=(
            "workspace_root",
            "agent_name",
            "title",
            "thinking_level",
            "session_id",
            "metadata",
        ),
    )
    config = config_for(request)
    services = services_for(request)
    workspace_root = optional_path(body, "workspace_root") or config.cwd
    provider_name = require_text(body, "provider_name")
    model = require_text(body, "model")
    agent_name = optional_text(body, "agent_name")
    title = optional_text(body, "title")
    thinking_level = optional_text(body, "thinking_level")
    session_id = optional_text(body, "session_id")
    metadata = optional_json_object(body, "metadata")

    try:
        record = await services.sessions.create(
            workspace_root=workspace_root,
            provider_name=provider_name,
            model=model,
            agent_name=agent_name,
            title=title,
            thinking_level=thinking_level,
            session_id=session_id,
            metadata=metadata,
        )
    except Exception as exc:
        raise_for_repository_error(exc)

    return json_response(await _session_resource(services, record), status=201)


async def get_session(request: web.Request) -> web.Response:
    services = services_for(request)
    session_id = request.match_info["session_id"]
    record = require_found(
        await services.sessions.get(session_id),
        resource="session",
        identifier=session_id,
    )
    return json_response(await _session_resource(services, record))


async def patch_session(request: web.Request) -> web.Response:
    body = await require_json_body(
        request,
        optional_fields=(
            "agent_name",
            "provider_name",
            "model",
            "title",
            "expected_updated_at",
        ),
    )
    services = services_for(request)
    session_id = request.match_info["session_id"]
    agent_name = optional_text(body, "agent_name")
    provider_name = optional_text(body, "provider_name")
    model = optional_text(body, "model")
    title = optional_nullable_text(body, "title")
    title_provided = "title" in body
    expected_updated_at = optional_text(body, "expected_updated_at")

    try:
        record = await services.sessions.patch(
            session_id,
            agent_name=agent_name,
            provider_name=provider_name,
            model=model,
            title=title,
            title_provided=title_provided,
            expected_updated_at=expected_updated_at,
        )
    except Exception as exc:
        raise_for_repository_error(exc)

    return json_response(await _session_resource(services, record))


async def archive_session(request: web.Request) -> web.Response:
    services = services_for(request)
    session_id = request.match_info["session_id"]

    try:
        record = await services.sessions.archive(session_id)
    except Exception as exc:
        raise_for_repository_error(exc)

    return json_response(await _session_resource(services, record))


async def restore_session(request: web.Request) -> web.Response:
    body = await require_json_body(
        request,
        optional_fields=("agent_name",),
        allow_empty=True,
    )
    services = services_for(request)
    session_id = request.match_info["session_id"]
    agent_name = optional_text(body, "agent_name")

    try:
        record = await services.sessions.restore(session_id, agent_name=agent_name)
    except Exception as exc:
        raise_for_repository_error(exc)

    return json_response(await _session_resource(services, record))


async def resolve_alias(request: web.Request) -> web.Response:
    services = services_for(request)
    address = request.match_info["address"]
    record = require_found(
        await services.sessions.resolve(address),
        resource="session alias",
        identifier=address,
    )
    return json_response(await _session_resource(services, record))


async def _session_resource(services: TauWebServices, record: SessionRecord) -> SessionResource:
    workspace = await services.sessions.get_workspace(record.workspace_id)
    if workspace is None:
        raise RuntimeError(
            f"Unknown workspace for session {record.session_id}: {record.workspace_id}"
        )
    return SessionResource(
        session_id=record.session_id,
        workspace_id=record.workspace_id,
        workspace_root=workspace.root_path,
        agent_name=record.agent_name,
        title=record.title,
        provider_name=record.provider_name,
        model=record.model,
        thinking_level=record.thinking_level,
        active_leaf_entry_id=record.active_leaf_entry_id,
        created_at=record.created_at,
        updated_at=record.updated_at,
        archived_at=record.archived_at,
        metadata=record.metadata,
    )


def setup_routes(app: web.Application) -> None:
    app.router.add_get("/api/sessions", list_sessions)
    app.router.add_post("/api/sessions", create_session)
    app.router.add_post("/api/sessions/{session_id}/restore", restore_session)
    app.router.add_get("/api/sessions/{session_id}", get_session)
    app.router.add_patch("/api/sessions/{session_id}", patch_session)
    app.router.add_delete("/api/sessions/{session_id}", archive_session)
    app.router.add_get("/api/aliases/{address:.+}", resolve_alias)
