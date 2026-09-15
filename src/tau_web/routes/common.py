"""Shared request validation, serialization, and error helpers for Tau Web routes."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, NoReturn, cast

from aiohttp import web

from tau_agent.types import JSONObject, JSONValue
from tau_web.app import CONFIG_KEY, SERVICES_KEY
from tau_web.config import WebConfig
from tau_web.services import TauWebServices
from tau_web.sqlite.repositories import RecordNotFoundError, RepositoryError, RevisionConflictError
from tau_web.sqlite.sessions import (
    AgentNameConflictError,
    InvalidAgentNameError,
    SessionMetadataConflictError,
)

type JSONBody = JSONObject

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})


def config_for(request: web.Request) -> WebConfig:
    return cast(WebConfig, request.app[CONFIG_KEY])


def services_for(request: web.Request) -> TauWebServices:
    return cast(TauWebServices, request.app[SERVICES_KEY])


async def require_json_body(
    request: web.Request,
    *,
    required_fields: Sequence[str] = (),
    optional_fields: Sequence[str] = (),
    allow_empty: bool = False,
) -> JSONBody:
    raw_body = await request.read()
    if not raw_body:
        if allow_empty:
            return {}
        raise web.HTTPBadRequest(reason="Request body must be a JSON object.")
    if not _is_json_content_type(request.content_type):
        raise web.HTTPUnsupportedMediaType(
            reason="Content-Type must be application/json or a +json subtype.",
        )

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise web.HTTPBadRequest(reason="Request body must be valid JSON.") from exc

    if not isinstance(payload, dict) or not all(isinstance(key, str) for key in payload):
        raise web.HTTPBadRequest(reason="Request body must be a JSON object.")

    body = cast(JSONBody, payload)
    allowed_fields = set(required_fields) | set(optional_fields)
    unknown_fields = sorted(set(body) - allowed_fields)
    if unknown_fields:
        raise web.HTTPBadRequest(
            reason=f"Unknown field(s): {', '.join(unknown_fields)}.",
        )

    missing_fields = [field for field in required_fields if field not in body]
    if missing_fields:
        raise web.HTTPBadRequest(
            reason=f"Missing required field(s): {', '.join(missing_fields)}.",
        )

    return body


def parse_bool(value: str | None, *, field: str, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().casefold()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise web.HTTPBadRequest(reason=f"Query parameter '{field}' must be a boolean.")


def require_text(body: Mapping[str, JSONValue], field: str) -> str:
    value = body.get(field)
    if not isinstance(value, str):
        raise web.HTTPBadRequest(reason=f"Field '{field}' must be a string.")
    return value


def require_non_empty_text(body: Mapping[str, JSONValue], field: str) -> str:
    value = require_text(body, field)
    if not value.strip():
        raise web.HTTPBadRequest(reason=f"Field '{field}' must not be blank.")
    return value


def optional_text(body: Mapping[str, JSONValue], field: str) -> str | None:
    if field not in body:
        return None
    value = body[field]
    if not isinstance(value, str):
        raise web.HTTPBadRequest(reason=f"Field '{field}' must be a string.")
    return value


def optional_non_empty_text(body: Mapping[str, JSONValue], field: str) -> str | None:
    value = optional_text(body, field)
    if value is None:
        return None
    if not value.strip():
        raise web.HTTPBadRequest(reason=f"Field '{field}' must not be blank.")
    return value


def optional_nullable_text(body: Mapping[str, JSONValue], field: str) -> str | None:
    if field not in body:
        return None
    value = body[field]
    if value is None:
        return None
    if not isinstance(value, str):
        raise web.HTTPBadRequest(reason=f"Field '{field}' must be a string or null.")
    return value


def optional_json_object(body: Mapping[str, JSONValue], field: str) -> JSONObject | None:
    if field not in body:
        return None
    value = body[field]
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise web.HTTPBadRequest(reason=f"Field '{field}' must be a JSON object.")
    if not _is_json_value(value):
        raise web.HTTPBadRequest(
            reason=f"Field '{field}' must contain only valid JSON values.",
        )
    return value


def optional_path(body: Mapping[str, JSONValue], field: str) -> Path | None:
    value = optional_text(body, field)
    return Path(value) if value is not None else None


def require_found[T](value: T | None, *, resource: str, identifier: str) -> T:
    if value is None:
        raise web.HTTPNotFound(reason=f"Unknown {resource}: {identifier}")
    return value


def raise_for_repository_error(exc: Exception) -> NoReturn:
    if isinstance(exc, (InvalidAgentNameError, ValueError)):
        raise web.HTTPBadRequest(reason=str(exc)) from exc
    if isinstance(exc, RecordNotFoundError):
        raise web.HTTPNotFound(reason=str(exc)) from exc
    if isinstance(
        exc,
        (
            AgentNameConflictError,
            RepositoryError,
            RevisionConflictError,
            SessionMetadataConflictError,
        ),
    ):
        raise web.HTTPConflict(reason=str(exc)) from exc
    raise exc


def json_response(data: object, *, status: int = 200) -> web.Response:
    return web.json_response(to_json_value(data), status=status)


def record_json(record: object) -> JSONObject:
    payload = to_json_value(record)
    if not isinstance(payload, dict) or not all(isinstance(key, str) for key in payload):
        raise TypeError("Serialized record payload must be a JSON object")
    return payload


def record_list_json(field: str, records: Sequence[object]) -> JSONObject:
    return {field: [record_json(record) for record in records]}


def record_response(record: object, *, status: int = 200) -> web.Response:
    return json_response(record_json(record), status=status)


def record_list_response(
    field: str,
    records: Sequence[object],
    *,
    status: int = 200,
) -> web.Response:
    return json_response(record_list_json(field, records), status=status)


def to_json_value(value: object) -> JSONValue:
    if _is_dataclass_instance(value):
        return {
            field.name: to_json_value(getattr(value, field.name))
            for field in fields(cast(Any, value))
        }
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [to_json_value(item) for item in value]
    if isinstance(value, list):
        return [to_json_value(item) for item in value]
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("JSON objects must use string keys")
        return {str(key): to_json_value(item) for key, item in value.items()}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("JSON numbers must be finite")
        return value
    if isinstance(value, str | int | bool) or value is None:
        return value
    raise TypeError(f"Unsupported JSON value: {type(value).__name__}")


def _is_json_content_type(content_type: str) -> bool:
    return content_type == "application/json" or content_type.endswith("+json")


def _is_json_value(value: object) -> bool:
    if value is None or isinstance(value, str | int | bool):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_json_value(item) for key, item in value.items())
    return False


def _is_dataclass_instance(value: object) -> bool:
    return not isinstance(value, type) and is_dataclass(value)
