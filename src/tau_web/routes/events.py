"""Server-sent event transport for canonical Tau web events."""

from __future__ import annotations

import asyncio
import json
from contextlib import suppress

from aiohttp import web

from tau_agent.types import JSONObject, JSONValue
from tau_web.routes.common import require_found, services_for, to_json_value
from tau_web.services import TauWebServices
from tau_web.sqlite.repositories import RunStatus
from tau_web.sse import BrokerEvent

_NONTERMINAL: tuple[RunStatus, ...] = ("pending", "running")
_SNAPSHOT_SESSION_LIMIT = 100
_SNAPSHOT_COLLECTION_LIMIT = 100


def setup_routes(app: web.Application) -> None:
    app.router.add_get("/api/events", stream_events)


async def stream_events(request: web.Request) -> web.StreamResponse:
    services = services_for(request)
    session_id = request.query.get("session_id")
    if session_id is not None:
        if not session_id.strip():
            raise web.HTTPBadRequest(reason="Query parameter 'session_id' must not be blank.")
        require_found(
            await services.sessions.get(session_id),
            resource="session",
            identifier=session_id,
        )
    last_event_id = _last_event_id(request)
    subscription, replay = services.broker.subscribe(
        session_id=session_id,
        last_event_id=last_event_id,
    )
    response = web.StreamResponse(
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
    await response.prepare(request)
    snapshot_cursor: int | None = None
    try:
        if last_event_id is None or replay.snapshot_required:
            snapshot_cursor = replay.cursor
            snapshot = await _snapshot(services, session_id, snapshot_cursor)
            await _write_event(
                response, cursor=snapshot_cursor, event="tau.snapshot", data=snapshot
            )
        else:
            for replay_event in replay.events:
                await _write_broker_event(response, replay_event)

        while True:
            live_event = await subscription.next(services.config.sse_heartbeat_seconds)
            if live_event is None:
                if subscription.closed:
                    break
                await response.write(b": heartbeat\n\n")
                continue
            if snapshot_cursor is not None and live_event.cursor <= snapshot_cursor:
                continue
            await _write_broker_event(response, live_event)
    except asyncio.CancelledError:
        raise
    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        subscription.close()
        with suppress(ConnectionResetError, RuntimeError):
            await response.write_eof()
    return response


def _last_event_id(request: web.Request) -> int | None:
    raw = request.headers.get("Last-Event-ID")
    if raw is None:
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise web.HTTPBadRequest(reason="Last-Event-ID must be a non-negative integer.") from exc
    if value < 0:
        raise web.HTTPBadRequest(reason="Last-Event-ID must be a non-negative integer.")
    return value


async def _snapshot(services: TauWebServices, session_id: str | None, cursor: int) -> JSONObject:
    sessions_repo = services.sessions
    timeline_repo = services.timeline
    runs_repo = services.runs
    queues_repo = services.queues
    if session_id is None:
        sessions = await sessions_repo.list(include_archived=False)
    else:
        sessions = [
            require_found(
                await sessions_repo.get(session_id),
                resource="session",
                identifier=session_id,
            )
        ]
    sessions = sessions[:_SNAPSHOT_SESSION_LIMIT]
    timeline: list[JSONValue] = []
    runs: list[JSONValue] = []
    queue: list[JSONValue] = []
    for session in sessions:
        timeline.extend(
            to_json_value(item)
            for item in await timeline_repo.list(
                session_id=session.session_id,
                limit=_SNAPSHOT_COLLECTION_LIMIT,
            )
        )
        runs.extend(
            to_json_value(item)
            for item in await runs_repo.list(
                session_id=session.session_id,
                statuses=_NONTERMINAL,
            )
        )
        queue.extend(
            to_json_value(item) for item in await queues_repo.list(session_id=session.session_id)
        )
    return {
        "cursor": cursor,
        "sessions": [to_json_value(item) for item in sessions],
        "timeline": timeline[:_SNAPSHOT_COLLECTION_LIMIT],
        "runs": runs[:_SNAPSHOT_COLLECTION_LIMIT],
        "queue": queue[:_SNAPSHOT_COLLECTION_LIMIT],
    }


async def _write_broker_event(response: web.StreamResponse, event: BrokerEvent) -> None:
    envelope = event.envelope
    await _write_event(
        response,
        cursor=event.cursor,
        event=envelope.type,
        data={
            "event_id": str(envelope.event_id),
            "type": envelope.type,
            "session_id": envelope.session_id,
            "run_id": envelope.run_id,
            "sequence": envelope.sequence,
            "payload": envelope.payload,
            "created_at": envelope.created_at,
        },
    )


async def _write_event(
    response: web.StreamResponse,
    *,
    cursor: int,
    event: str,
    data: JSONObject,
) -> None:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    await response.write(f"id: {cursor}\nevent: {event}\ndata: {payload}\n\n".encode())
