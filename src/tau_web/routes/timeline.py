"""Session timeline, branch, and context REST routes for Tau Web."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from aiohttp import web

from pydantic import BaseModel, ConfigDict
from tau_agent.session import (
    CompactionEntry,
    LeafEntry,
    MessageEntry,
    ModelChangeEntry,
    SessionEntry,
    ThinkingLevelChangeEntry,
    path_to_entry,
)
from tau_agent.types import JSONObject, JSONValue
from tau_web.routes.common import (
    json_response,
    record_json,
    require_found,
    require_json_body,
    services_for,
)
from tau_web.routes.sessions import session_resource
from tau_web.services import TauWebServices
from tau_web.sqlite.session_storage import SqliteSessionStorageError
from tau_web.sqlite.sessions import SessionRecord


class EntriesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entries: list[JSONObject]


class MessagesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    leaf_entry_id: str | None
    messages: list[JSONObject]


class BranchResource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    leaf_entry_id: str
    active: bool
    depth: int
    timestamp: float


class BranchListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    branches: list[BranchResource]


class BranchSelectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session: JSONObject
    leaf_entry_id: str | None


class ContextSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entry_count: int
    message_count: int
    compaction_count: int
    active_leaf_entry_id: str | None
    model: str
    thinking_level: str | None


async def get_entries(request: web.Request) -> web.Response:
    services = services_for(request)
    session_id = request.match_info["session_id"]
    await _require_session(services, session_id)
    storage = services.session_storage(session_id)
    leaf_entry_id = _optional_leaf_entry_id_query(request)

    try:
        entries = (
            await storage.read_all()
            if leaf_entry_id is None
            else await storage.read_path(leaf_entry_id)
        )
    except SqliteSessionStorageError as exc:
        _raise_for_storage_error(exc, leaf_entry_id=leaf_entry_id)

    return json_response(
        EntriesResponse(entries=[_entry_json(entry) for entry in entries]).model_dump(mode="json")
    )


async def get_messages(request: web.Request) -> web.Response:
    services = services_for(request)
    session_id = request.match_info["session_id"]
    session = await _require_session(services, session_id)
    storage = services.session_storage(session_id)
    leaf_entry_id = _optional_leaf_entry_id_query(request)
    resolved_leaf_entry_id = (
        session.active_leaf_entry_id if leaf_entry_id is None else leaf_entry_id
    )

    if resolved_leaf_entry_id is None:
        return json_response(
            MessagesResponse(leaf_entry_id=None, messages=[]).model_dump(mode="json")
        )

    try:
        entries = await storage.read_path(resolved_leaf_entry_id)
    except SqliteSessionStorageError as exc:
        _raise_for_storage_error(exc, leaf_entry_id=resolved_leaf_entry_id)

    messages = [_entry_json(entry) for entry in entries if isinstance(entry, MessageEntry)]
    return json_response(
        MessagesResponse(
            leaf_entry_id=resolved_leaf_entry_id,
            messages=messages,
        ).model_dump(mode="json")
    )


async def get_branches(request: web.Request) -> web.Response:
    services = services_for(request)
    session_id = request.match_info["session_id"]
    session = await _require_session(services, session_id)
    storage = services.session_storage(session_id)
    entries = await storage.read_all()
    branches = [
        BranchResource(
            leaf_entry_id=entry.id,
            active=entry.id == session.active_leaf_entry_id,
            depth=_entry_depth(entries, entry.id),
            timestamp=entry.timestamp,
        )
        for entry in _branch_leaf_entries(entries)
    ]
    return json_response(BranchListResponse(branches=branches).model_dump(mode="json"))


async def select_branch(request: web.Request) -> web.Response:
    body = await require_json_body(request, required_fields=("leaf_entry_id",))
    services = services_for(request)
    session_id = request.match_info["session_id"]
    await _require_session(services, session_id)
    storage = services.session_storage(session_id)
    leaf_entry_id = _nullable_leaf_entry_id_field(body, "leaf_entry_id")
    entries = await storage.read_all()

    if leaf_entry_id is not None and not any(
        entry.id == leaf_entry_id and not isinstance(entry, LeafEntry) for entry in entries
    ):
        raise web.HTTPNotFound(reason=f"Unknown leaf entry: {leaf_entry_id}")

    try:
        await storage.append(LeafEntry(parent_id=leaf_entry_id, entry_id=leaf_entry_id))
    except SqliteSessionStorageError as exc:
        _raise_for_storage_error(exc, leaf_entry_id=leaf_entry_id)

    updated_session = require_found(
        await services.sessions.get(session_id),
        resource="session",
        identifier=session_id,
    )
    return json_response(
        BranchSelectionResponse(
            session=record_json(await session_resource(services, updated_session)),
            leaf_entry_id=leaf_entry_id,
        ).model_dump(mode="json")
    )


async def get_context(request: web.Request) -> web.Response:
    services = services_for(request)
    session_id = request.match_info["session_id"]
    session = await _require_session(services, session_id)
    storage = services.session_storage(session_id)
    active_leaf_entry_id = session.active_leaf_entry_id

    if active_leaf_entry_id is None:
        return json_response(
            ContextSummaryResponse(
                entry_count=0,
                message_count=0,
                compaction_count=0,
                active_leaf_entry_id=None,
                model=session.model,
                thinking_level=session.thinking_level,
            ).model_dump(mode="json")
        )

    try:
        entries = await storage.read_path(active_leaf_entry_id)
    except SqliteSessionStorageError as exc:
        _raise_for_storage_error(exc, leaf_entry_id=active_leaf_entry_id)

    model = session.model
    thinking_level = session.thinking_level
    message_count = 0
    compaction_count = 0

    for entry in entries:
        if isinstance(entry, MessageEntry):
            message_count += 1
        elif isinstance(entry, CompactionEntry):
            compaction_count += 1
        elif isinstance(entry, ModelChangeEntry):
            model = entry.model
        elif isinstance(entry, ThinkingLevelChangeEntry):
            thinking_level = entry.thinking_level

    return json_response(
        ContextSummaryResponse(
            entry_count=len(entries),
            message_count=message_count,
            compaction_count=compaction_count,
            active_leaf_entry_id=active_leaf_entry_id,
            model=model,
            thinking_level=thinking_level,
        ).model_dump(mode="json")
    )


async def _require_session(services: TauWebServices, session_id: str) -> SessionRecord:
    return require_found(
        await services.sessions.get(session_id),
        resource="session",
        identifier=session_id,
    )


def _optional_leaf_entry_id_query(request: web.Request) -> str | None:
    leaf_entry_id = request.query.get("leaf_entry_id")
    if leaf_entry_id is None:
        return None
    if not leaf_entry_id.strip():
        raise web.HTTPBadRequest(
            reason="Query parameter 'leaf_entry_id' must be a non-empty string."
        )
    return leaf_entry_id


def _nullable_leaf_entry_id_field(body: Mapping[str, JSONValue], field: str) -> str | None:
    value = body[field]
    if value is None:
        return None
    if not isinstance(value, str):
        raise web.HTTPBadRequest(reason=f"Field '{field}' must be a string or null.")
    if not value.strip():
        raise web.HTTPBadRequest(reason=f"Field '{field}' must not be blank.")
    return value


def _raise_for_storage_error(
    exc: SqliteSessionStorageError,
    *,
    leaf_entry_id: str | None,
) -> None:
    message = str(exc)
    if message.startswith("Unknown session:"):
        raise web.HTTPNotFound(reason=message) from exc
    if leaf_entry_id is not None and _is_missing_entry_reference_error(message):
        raise web.HTTPNotFound(reason=f"Unknown leaf entry: {leaf_entry_id}") from exc
    raise exc


def _is_missing_entry_reference_error(message: str) -> bool:
    return message.startswith(
        (
            "Missing session entry:",
            "Entry reference does not exist:",
            "Entry reference belongs to another session:",
        )
    )


def _entry_json(entry: SessionEntry) -> JSONObject:
    payload = entry.model_dump(mode="json")
    if not isinstance(payload, dict) or not all(isinstance(key, str) for key in payload):
        raise TypeError("Session entry payload must be a JSON object")
    return cast(JSONObject, payload)


def _branch_leaf_entries(entries: Sequence[SessionEntry]) -> tuple[SessionEntry, ...]:
    non_leaf_entries = [entry for entry in entries if not isinstance(entry, LeafEntry)]
    parent_ids = {entry.parent_id for entry in non_leaf_entries if entry.parent_id is not None}
    return tuple(entry for entry in non_leaf_entries if entry.id not in parent_ids)


def _entry_depth(entries: list[SessionEntry], leaf_entry_id: str) -> int:
    path = path_to_entry(entries, leaf_entry_id)
    return sum(1 for entry in path if not isinstance(entry, LeafEntry)) - 1


def setup_routes(app: web.Application) -> None:
    app.router.add_get("/api/sessions/{session_id}/entries", get_entries)
    app.router.add_get("/api/sessions/{session_id}/messages", get_messages)
    app.router.add_get("/api/sessions/{session_id}/branches", get_branches)
    app.router.add_post("/api/sessions/{session_id}/branches/select", select_branch)
    app.router.add_get("/api/sessions/{session_id}/context", get_context)
