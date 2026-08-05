"""Metadata, settings, model, usage, plan, and search REST routes."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Final, cast

from aiohttp import web

from tau_agent.session import LeafEntry, ModelChangeEntry, ThinkingLevelChangeEntry
from tau_agent.types import JSONObject, JSONValue
from tau_coding.commands import create_default_command_registry
from tau_coding.plan import (
    PlanConflictError,
    PlanItem,
    PlanSnapshot,
    PlanStatus,
    parse_plan_markdown,
    render_plan_markdown,
)
from tau_coding.thinking import normalize_thinking_level
from tau_web.events import build_invalidation_envelope
from tau_web.plan import SqlitePlanStore
from tau_web.routes.common import (
    config_for,
    json_response,
    raise_for_repository_error,
    require_found,
    require_json_body,
    require_non_empty_text,
    services_for,
)
from tau_web.routes.sessions import session_resource
from tau_web.services import TauWebServices
from tau_web.sqlite.repositories import UsageRecord
from tau_web.sqlite.sessions import SessionRecord

_WEB_COMMAND_NAMES: Final[tuple[str, ...]] = (
    "new",
    "session",
    "model",
    "thinking",
    "compact",
    "clear",
)
_PLAN_UPDATED_BY: Final[str] = "tau-web"
_DEFAULT_SEARCH_LIMIT: Final[int] = 20


@dataclass(frozen=True, slots=True)
class SettingsResource:
    host: str
    port: int
    cwd: str
    database_path: str
    max_active_runs: int
    max_request_size: int
    auth_required: bool
    allowed_origins: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ModelDescriptor:
    provider_name: str
    model: str


@dataclass(frozen=True, slots=True)
class ModelsResponse:
    source: str
    models: tuple[ModelDescriptor, ...]


@dataclass(frozen=True, slots=True)
class CommandDescriptor:
    name: str
    usage: str
    description: str


@dataclass(frozen=True, slots=True)
class CommandsResponse:
    source: str
    commands: tuple[CommandDescriptor, ...]


@dataclass(frozen=True, slots=True)
class PlanResource:
    session_id: str
    content: JSONObject
    items: tuple[PlanItem, ...]
    markdown: str
    revision: int
    updated_at: str | None
    updated_by: str | None


@dataclass(frozen=True, slots=True)
class UsageTotals:
    input: int
    output: int
    cache_read: int
    cache_write: int
    cost: int


@dataclass(frozen=True, slots=True)
class UsageResponse:
    records: tuple[UsageRecord, ...]
    totals: UsageTotals


async def get_settings(request: web.Request) -> web.Response:
    config = config_for(request)
    database_path = config.database_path
    if database_path is None:
        raise RuntimeError("WebConfig.database_path must not be None")
    return json_response(
        SettingsResource(
            host=config.host,
            port=config.port,
            cwd=str(config.cwd),
            database_path=str(database_path),
            max_active_runs=config.max_active_runs,
            max_request_size=config.max_request_bytes,
            auth_required=config.auth_token is not None,
            allowed_origins=config.allowed_origins,
        )
    )


async def get_models(request: web.Request) -> web.Response:
    services = services_for(request)
    records = await services.sessions.list(include_archived=False)
    pairs = sorted({(record.provider_name, record.model) for record in records})
    return json_response(
        ModelsResponse(
            source="sessions",
            models=tuple(
                ModelDescriptor(provider_name=provider_name, model=model)
                for provider_name, model in pairs
            ),
        )
    )


async def get_commands(request: web.Request) -> web.Response:
    del request
    registry = create_default_command_registry()
    commands = []
    for name in _WEB_COMMAND_NAMES:
        command = registry.get(name)
        if command is None:
            continue
        commands.append(
            CommandDescriptor(
                name=command.name,
                usage=command.usage,
                description=command.description,
            )
        )
    return json_response(CommandsResponse(source="runtime", commands=tuple(commands)))


async def patch_session_model(request: web.Request) -> web.Response:
    body = await require_json_body(
        request,
        required_fields=("provider_name", "model", "expected_updated_at"),
    )
    services = services_for(request)
    session_id = request.match_info["session_id"]
    provider_name = require_non_empty_text(body, "provider_name")
    model = require_non_empty_text(body, "model")
    expected_updated_at = require_non_empty_text(body, "expected_updated_at")

    async def write_model_change() -> None:
        async def write(transaction: object) -> None:
            active_transaction = cast("SqliteTransaction", transaction)
            current = await services.sessions.update_metadata(
                session_id,
                provider_name=provider_name,
                model=model,
                expected_updated_at=expected_updated_at,
                transaction=active_transaction,
            )
            change = ModelChangeEntry(parent_id=current.active_leaf_entry_id, model=model)
            leaf = LeafEntry(parent_id=change.id, entry_id=change.id)
            await services.session_storage(session_id).append_many_in_transaction(
                active_transaction,
                (change, leaf),
            )

        from tau_web.sqlite.writer import SqliteTransaction

        await services.database.write(write)

    try:
        await write_model_change()
    except Exception as exc:
        raise_for_repository_error(exc)

    updated = await _require_session(services, session_id)
    return json_response(await session_resource(services, updated))


async def patch_session_thinking(request: web.Request) -> web.Response:
    body = await require_json_body(
        request,
        required_fields=("thinking_level", "expected_updated_at"),
    )
    services = services_for(request)
    session_id = request.match_info["session_id"]
    thinking_level = _thinking_level_field(body, "thinking_level")
    expected_updated_at = require_non_empty_text(body, "expected_updated_at")

    async def write_thinking_change() -> None:
        async def write(transaction: object) -> None:
            active_transaction = cast("SqliteTransaction", transaction)
            current = await services.sessions.update_metadata(
                session_id,
                thinking_level=thinking_level,
                expected_updated_at=expected_updated_at,
                transaction=active_transaction,
            )
            change = ThinkingLevelChangeEntry(
                parent_id=current.active_leaf_entry_id,
                thinking_level=thinking_level,
            )
            leaf = LeafEntry(parent_id=change.id, entry_id=change.id)
            await services.session_storage(session_id).append_many_in_transaction(
                active_transaction,
                (change, leaf),
            )

        from tau_web.sqlite.writer import SqliteTransaction

        await services.database.write(write)

    try:
        await write_thinking_change()
    except Exception as exc:
        raise_for_repository_error(exc)

    updated = await _require_session(services, session_id)
    return json_response(await session_resource(services, updated))


async def get_session_plan(request: web.Request) -> web.Response:
    services = services_for(request)
    session_id = request.match_info["session_id"]
    await _require_session(services, session_id)
    snapshot = await SqlitePlanStore(services.plans).get(session_id)
    return json_response(_plan_resource(snapshot or PlanSnapshot(session_id=session_id)))


async def put_session_plan(request: web.Request) -> web.Response:
    body = await require_json_body(
        request,
        required_fields=("expected_revision",),
        optional_fields=("content", "items", "markdown"),
    )
    services = services_for(request)
    session_id = request.match_info["session_id"]
    await _require_writable_session(services, session_id)
    expected_revision = _expected_revision_field(body, "expected_revision")

    try:
        items = _plan_items_from_request(body)
        snapshot = await SqlitePlanStore(services.plans).save(
            PlanSnapshot(
                session_id=session_id,
                items=items,
                updated_by=_PLAN_UPDATED_BY,
            ),
            expected_revision=expected_revision,
        )
    except PlanConflictError:
        current = await SqlitePlanStore(services.plans).get(session_id)
        resource = _plan_resource(current or PlanSnapshot(session_id=session_id))
        return json_response(
            {
                "error": {
                    "code": "plan_revision_conflict",
                    "message": "The session plan changed since it was loaded.",
                },
                "current": resource,
            },
            status=web.HTTPConflict.status_code,
        )
    except ValueError as exc:
        raise web.HTTPBadRequest(reason=str(exc)) from exc
    except Exception as exc:
        raise_for_repository_error(exc)
        raise AssertionError("unreachable") from exc

    await services.broker.publish(
        build_invalidation_envelope(
            event_type="tau.plan.updated",
            session_id=session_id,
            payload={"revision": snapshot.revision},
        )
    )
    return json_response(_plan_resource(snapshot))


async def get_session_usage(request: web.Request) -> web.Response:
    services = services_for(request)
    session_id = request.match_info["session_id"]
    await _require_session(services, session_id)
    run_id = _optional_non_empty_query(request, "run_id")
    if run_id is not None:
        run = require_found(await services.runs.get(run_id), resource="run", identifier=run_id)
        if run.session_id != session_id:
            raise web.HTTPNotFound(reason=f"Unknown run: {run_id}")

    records = await services.usage.list(session_id=session_id, run_id=run_id)
    totals = UsageTotals(
        input=sum(record.input_tokens for record in records),
        output=sum(record.output_tokens for record in records),
        cache_read=sum(record.cached_input_tokens for record in records),
        cache_write=0,
        cost=sum(record.cost_microunits or 0 for record in records),
    )
    return json_response(UsageResponse(records=tuple(records), totals=totals))


async def search(request: web.Request) -> web.Response:
    services = services_for(request)
    query = _required_non_empty_query(request, "q")
    session_id = _optional_non_empty_query(request, "session_id")
    limit = _positive_int_query(request, "limit", default=_DEFAULT_SEARCH_LIMIT)
    if session_id is not None:
        await _require_session(services, session_id)

    try:
        results = await services.fts.search(query, session_id=session_id, limit=limit)
    except ValueError as exc:
        raise web.HTTPBadRequest(reason=str(exc)) from exc
    except sqlite3.OperationalError as exc:
        raise web.HTTPBadRequest(reason="Invalid FTS query.") from exc

    return json_response({"results": results})


async def _require_session(services: TauWebServices, session_id: str) -> SessionRecord:
    return require_found(
        await services.sessions.get(session_id),
        resource="session",
        identifier=session_id,
    )


async def _require_writable_session(services: TauWebServices, session_id: str) -> SessionRecord:
    session = await _require_session(services, session_id)
    if session.archived_at is not None:
        raise web.HTTPConflict(reason="Archived sessions must be restored before updating")
    return session


def _thinking_level_field(body: dict[str, JSONValue], field: str) -> str | None:
    value = body[field]
    if value is None:
        return None
    if not isinstance(value, str):
        raise web.HTTPBadRequest(reason=f"Field '{field}' must be a string or null.")
    normalized = normalize_thinking_level(value)
    return normalized


def _expected_revision_field(body: dict[str, JSONValue], field: str) -> int | None:
    value = body[field]
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise web.HTTPBadRequest(reason=f"Field '{field}' must be an integer or null.")
    if value < 0:
        raise web.HTTPBadRequest(reason=f"Field '{field}' must be non-negative.")
    return value


def _required_non_empty_query(request: web.Request, field: str) -> str:
    value = request.query.get(field)
    if value is None or not value.strip():
        raise web.HTTPBadRequest(reason=f"Query parameter '{field}' must be a non-empty string.")
    return value.strip()


def _optional_non_empty_query(request: web.Request, field: str) -> str | None:
    value = request.query.get(field)
    if value is None:
        return None
    if not value.strip():
        raise web.HTTPBadRequest(reason=f"Query parameter '{field}' must be a non-empty string.")
    return value.strip()


def _positive_int_query(request: web.Request, field: str, *, default: int) -> int:
    raw = request.query.get(field)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise web.HTTPBadRequest(reason=f"Query parameter '{field}' must be an integer.") from exc
    if value <= 0:
        raise web.HTTPBadRequest(reason=f"Query parameter '{field}' must be positive.")
    return value


def _plan_items_from_request(body: JSONObject) -> tuple[PlanItem, ...]:
    markdown = body.get("markdown")
    if markdown is not None:
        if not isinstance(markdown, str):
            raise ValueError("Field 'markdown' must be a string.")
        return parse_plan_markdown(markdown)

    raw_items: JSONValue | None = body.get("items")
    content = body.get("content")
    if raw_items is None and isinstance(content, dict):
        raw_items = content.get("items", [])
    if raw_items is None:
        raise ValueError("Request must include 'markdown', 'items', or content.items.")
    if not isinstance(raw_items, list):
        raise ValueError("Plan items must be an array.")

    items: list[PlanItem] = []
    for index, value in enumerate(raw_items):
        if not isinstance(value, dict):
            raise ValueError(f"Plan item {index + 1} must be an object.")
        step = value.get("step")
        status = value.get("status", "pending")
        if not isinstance(step, str) or not isinstance(status, str):
            raise ValueError(f"Plan item {index + 1} requires string step and status.")
        items.append(PlanItem(step=step, status=cast(PlanStatus, status)))
    return tuple(items)


def _plan_resource(snapshot: PlanSnapshot) -> PlanResource:
    items_payload = [
        cast(JSONObject, {"step": item.step, "status": item.status})
        for item in snapshot.items
    ]
    return PlanResource(
        session_id=snapshot.session_id,
        content=cast(JSONObject, {"items": items_payload}),
        items=snapshot.items,
        markdown=render_plan_markdown(snapshot.items),
        revision=snapshot.revision,
        updated_at=snapshot.updated_at,
        updated_by=snapshot.updated_by,
    )


def setup_routes(app: web.Application) -> None:
    app.router.add_get("/api/settings", get_settings)
    app.router.add_get("/api/models", get_models)
    app.router.add_get("/api/commands", get_commands)
    app.router.add_patch("/api/sessions/{session_id}/model", patch_session_model)
    app.router.add_patch("/api/sessions/{session_id}/thinking", patch_session_thinking)
    app.router.add_get("/api/sessions/{session_id}/plan", get_session_plan)
    app.router.add_put("/api/sessions/{session_id}/plan", put_session_plan)
    app.router.add_get("/api/sessions/{session_id}/usage", get_session_usage)
    app.router.add_get("/api/search", search)
