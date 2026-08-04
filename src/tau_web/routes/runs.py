"""Durable run and queue REST routes."""

from __future__ import annotations

from typing import Final, NoReturn

from aiohttp import web

from tau_coding import AgentPoolError
from tau_web.routes.common import (
    json_response,
    optional_non_empty_text,
    parse_bool,
    raise_for_repository_error,
    record_json,
    record_list_response,
    require_found,
    require_json_body,
    require_non_empty_text,
    services_for,
)
from tau_web.services import TauWebServices
from tau_web.sqlite.repositories import QueueKind, RunStatus
from tau_web.sqlite.sessions import SessionRecord

_RUN_STATUS_MAP: Final[dict[str, RunStatus]] = {
    "pending": "pending",
    "running": "running",
    "completed": "completed",
    "cancelled": "cancelled",
    "failed": "failed",
    "interrupted": "interrupted",
}
_QUEUE_KIND_MAP: Final[dict[str, QueueKind]] = {
    "steer": "steer",
    "follow_up": "follow_up",
}


def setup_routes(app: web.Application) -> None:
    app.router.add_get("/api/sessions/{session_id}/runs", list_runs)
    app.router.add_post("/api/sessions/{session_id}/runs", submit_run)
    app.router.add_get("/api/runs/{run_id}", get_run)
    app.router.add_post("/api/runs/{run_id}/cancel", cancel_run)
    app.router.add_post("/api/runs/{run_id}/abort", abort_run)
    app.router.add_post("/api/runs/{run_id}/retry", retry_run)
    app.router.add_get("/api/sessions/{session_id}/queue", list_queue)
    app.router.add_post("/api/sessions/{session_id}/queue", enqueue_message)
    app.router.add_post("/api/runs/{run_id}/messages", queue_run_message)
    app.router.add_post("/api/runs/{run_id}/queue/{kind}/dispatch", dispatch_next)


async def list_runs(request: web.Request) -> web.Response:
    services = services_for(request)
    session_id = request.match_info["session_id"]
    await _require_session(services, session_id)
    statuses = _run_statuses(request)
    return record_list_response(
        "runs",
        await services.runs.list(session_id=session_id, statuses=statuses),
    )


async def submit_run(request: web.Request) -> web.Response:
    services = services_for(request)
    session_id = request.match_info["session_id"]
    await _require_session(services, session_id)
    body = await require_json_body(
        request,
        optional_fields=("content", "continue", "run_id"),
    )
    run_id = optional_non_empty_text(body, "run_id")
    has_content = "content" in body
    continue_value = body.get("continue", False)
    if not isinstance(continue_value, bool):
        raise web.HTTPBadRequest(reason="Field 'continue' must be a boolean.")
    if has_content == continue_value:
        raise web.HTTPBadRequest(
            reason="Provide exactly one of non-blank 'content' or 'continue: true'."
        )
    try:
        if continue_value:
            handle = await services.runtime.submit_continue(session_id, run_id=run_id)
        else:
            content = require_non_empty_text(body, "content")
            handle = await services.runtime.submit_prompt(session_id, content, run_id=run_id)
        record = require_found(
            await services.runs.get(handle.run_id), resource="run", identifier=handle.run_id
        )
    except Exception as exc:
        _raise_for_runtime_error(exc)
    return json_response(record_json(record), status=202)


async def get_run(request: web.Request) -> web.Response:
    run_id = request.match_info["run_id"]
    record = require_found(
        await services_for(request).runs.get(run_id), resource="run", identifier=run_id
    )
    return json_response(record_json(record))


async def cancel_run(request: web.Request) -> web.Response:
    return await _stop_run(request, abort=False)


async def abort_run(request: web.Request) -> web.Response:
    return await _stop_run(request, abort=True)


async def _stop_run(request: web.Request, *, abort: bool) -> web.Response:
    services = services_for(request)
    run_id = request.match_info["run_id"]
    require_found(await services.runs.get(run_id), resource="run", identifier=run_id)
    accepted = await (services.runtime.abort(run_id) if abort else services.runtime.cancel(run_id))
    record = require_found(await services.runs.get(run_id), resource="run", identifier=run_id)
    return json_response(
        {"accepted": accepted, "run": record_json(record)},
        status=202 if accepted else 200,
    )


async def retry_run(request: web.Request) -> web.Response:
    services = services_for(request)
    run_id = request.match_info["run_id"]
    try:
        handle = await services.runtime.retry(run_id)
        record = require_found(
            await services.runs.get(handle.run_id), resource="run", identifier=handle.run_id
        )
    except Exception as exc:
        _raise_for_runtime_error(exc)
    return json_response({"retry_of": run_id, "run": record_json(record)}, status=202)


async def list_queue(request: web.Request) -> web.Response:
    services = services_for(request)
    session_id = request.match_info["session_id"]
    await _require_session(services, session_id)
    raw_kind = request.query.get("kind")
    kind = _queue_kind(raw_kind) if raw_kind is not None else None
    include_consumed = parse_bool(request.query.get("include_consumed"), field="include_consumed")
    records = await services.queues.list(
        session_id=session_id,
        queue_kind=kind,
        include_consumed=include_consumed,
    )
    return record_list_response("queue", records)


async def enqueue_message(request: web.Request) -> web.Response:
    services = services_for(request)
    session_id = request.match_info["session_id"]
    await _require_session(services, session_id)
    body = await require_json_body(
        request,
        required_fields=("content",),
        optional_fields=("kind", "source_session_id"),
    )
    content = require_non_empty_text(body, "content")
    raw_kind = body.get("kind", "follow_up")
    if not isinstance(raw_kind, str):
        raise web.HTTPBadRequest(reason="Field 'kind' must be a string.")
    kind = _queue_kind(raw_kind)
    source = optional_non_empty_text(body, "source_session_id")
    if source is not None:
        await _require_session(services, source)
    record = await services.runtime.enqueue(
        session_id,
        content,
        queue_kind=kind,
        source_session_id=source,
    )
    return json_response(record_json(record), status=201)


async def queue_run_message(request: web.Request) -> web.Response:
    services = services_for(request)
    run_id = request.match_info["run_id"]
    require_found(await services.runs.get(run_id), resource="run", identifier=run_id)
    body = await require_json_body(
        request,
        required_fields=("content", "kind"),
        optional_fields=("source_session_id",),
    )
    content = require_non_empty_text(body, "content")
    kind = _queue_kind(require_non_empty_text(body, "kind"))
    source = optional_non_empty_text(body, "source_session_id")
    if source is not None:
        await _require_session(services, source)
    try:
        if kind == "steer":
            record = await services.runtime.steer(run_id, content, source_session_id=source)
        else:
            record = await services.runtime.follow_up(run_id, content, source_session_id=source)
    except Exception as exc:
        _raise_for_runtime_error(exc)
    return json_response(record_json(record), status=200 if record.consumed_at else 202)


async def dispatch_next(request: web.Request) -> web.Response:
    services = services_for(request)
    run_id = request.match_info["run_id"]
    require_found(await services.runs.get(run_id), resource="run", identifier=run_id)
    kind = _queue_kind(request.match_info["kind"])
    try:
        record = await services.runtime.dispatch_next(run_id, kind)
    except Exception as exc:
        _raise_for_runtime_error(exc)
    if record is None:
        return web.Response(status=204)
    return json_response(record_json(record))


async def _require_session(services: TauWebServices, session_id: str) -> SessionRecord:
    return require_found(
        await services.sessions.get(session_id), resource="session", identifier=session_id
    )


def _raise_for_runtime_error(exc: Exception) -> NoReturn:
    if isinstance(exc, (AgentPoolError, ValueError)):
        raise web.HTTPConflict(reason=str(exc)) from exc
    raise_for_repository_error(exc)


def _queue_kind(value: str) -> QueueKind:
    kind = _QUEUE_KIND_MAP.get(value.strip())
    if kind is None:
        raise web.HTTPBadRequest(reason="Queue kind must be 'steer' or 'follow_up'.")
    return kind


def _run_statuses(request: web.Request) -> list[RunStatus] | None:
    statuses: list[RunStatus] = []
    invalid: set[str] = set()
    for raw in request.query.getall("status", []):
        for item in raw.split(","):
            normalized = item.strip()
            if not normalized:
                continue
            status = _RUN_STATUS_MAP.get(normalized)
            if status is None:
                invalid.add(normalized)
            else:
                statuses.append(status)
    if invalid:
        raise web.HTTPBadRequest(reason=f"Unknown run status: {', '.join(sorted(invalid))}")
    return statuses or None
