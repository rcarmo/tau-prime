"""Registered extension asset and route adapters for Tau Web."""

from __future__ import annotations

import asyncio
import inspect
import json
from collections.abc import Awaitable, Mapping
from typing import cast
from uuid import uuid4

from aiohttp import web

from tau_agent.types import JSONValue
from tau_extensions import RegistryError, RouteHandler, RouteRequest, RouteResponse
from tau_web.middleware import REQUEST_ID_KEY
from tau_web.routes.common import services_for

_MAX_EXTENSION_ROUTE_TIMEOUT_SECONDS = 30.0
_MAX_EXTENSION_ROUTE_BODY_BYTES = 1024 * 1024
_MAX_EXTENSION_ROUTE_QUERY_ENTRIES = 64
_MAX_EXTENSION_ROUTE_HEADER_ENTRIES = 32
_MAX_EXTENSION_ROUTE_KEY_BYTES = 256
_MAX_EXTENSION_ROUTE_VALUE_BYTES = 8 * 1024
_ASSET_CACHE_CONTROL = "public, max-age=31536000, immutable"
_FORBIDDEN_RESPONSE_HEADERS = frozenset({"connection", "content-length", "set-cookie"})
_SAFE_REQUEST_HEADERS = frozenset(
    {
        "accept",
        "accept-language",
        "content-type",
        "if-match",
        "if-none-match",
        "origin",
        "user-agent",
        "x-request-id",
    }
)


class InvalidExtensionResponseError(ValueError):
    """Raised when an extension route returns an invalid portable response."""


def setup_routes(app: web.Application) -> None:
    app.router.add_get("/api/extensions/assets/{extension_id}/{path:.*}", get_extension_asset)
    app.router.add_route("*", "/api/extensions/routes/{extension_id}", dispatch_extension_route)
    app.router.add_route(
        "*",
        "/api/extensions/routes/{extension_id}/{path:.*}",
        dispatch_extension_route,
    )


async def get_extension_asset(request: web.Request) -> web.Response:
    asset = services_for(request).extensions.lookup_asset(
        request.match_info["extension_id"],
        request.match_info["path"],
    )
    if asset is None:
        raise web.HTTPNotFound(reason="Unknown extension asset.")
    return web.Response(
        body=asset.content,
        headers={
            "Cache-Control": _ASSET_CACHE_CONTROL,
            "Content-Type": asset.mime_type,
            "X-Content-Type-Options": "nosniff",
        },
    )


async def dispatch_extension_route(request: web.Request) -> web.Response:
    route_path = _route_path_from_request(request)
    route = services_for(request).extensions.lookup_route(
        request.match_info["extension_id"],
        request.method,
        route_path,
    )
    if route is None:
        raise web.HTTPNotFound(reason="Unknown extension route.")

    route_request = await _portable_route_request(request, route_path)
    try:
        result = await asyncio.wait_for(
            _invoke_route_handler(route.handler, route_request),
            timeout=_MAX_EXTENSION_ROUTE_TIMEOUT_SECONDS,
        )
    except asyncio.CancelledError:
        raise
    except TimeoutError:
        return _error_response(
            request,
            status=504,
            code="extension_route_timeout",
            message="Extension route timed out.",
        )
    except Exception:
        return _error_response(
            request,
            status=500,
            code="extension_route_error",
            message="Extension route failed.",
        )

    try:
        return _web_response_from_portable(result)
    except InvalidExtensionResponseError as exc:
        return _error_response(
            request,
            status=502,
            code="invalid_extension_response",
            message=str(exc),
        )


async def _portable_route_request(request: web.Request, route_path: str) -> RouteRequest:
    body = await _read_json_request_body(request)
    try:
        return RouteRequest(
            method=request.method,
            path=route_path,
            query=_bounded_query_mapping(request.query),
            headers=_selected_request_headers(request.headers),
            body=body,
        )
    except RegistryError as exc:
        raise web.HTTPBadRequest(reason=str(exc)) from exc


async def _invoke_route_handler(handler: RouteHandler, request: RouteRequest) -> object:
    if inspect.iscoroutinefunction(handler):
        return await cast(Awaitable[object], handler(request))
    result: object = await asyncio.to_thread(handler, request)
    if inspect.isawaitable(result):
        return await cast(Awaitable[object], result)
    return result


async def _read_json_request_body(request: web.Request) -> JSONValue | None:
    content_length = request.content_length
    if content_length is not None and content_length > _MAX_EXTENSION_ROUTE_BODY_BYTES:
        raise web.HTTPRequestEntityTooLarge(
            max_size=_MAX_EXTENSION_ROUTE_BODY_BYTES,
            actual_size=content_length,
        )

    raw_body = await request.read()
    if not raw_body:
        return None
    if len(raw_body) > _MAX_EXTENSION_ROUTE_BODY_BYTES:
        raise web.HTTPRequestEntityTooLarge(
            max_size=_MAX_EXTENSION_ROUTE_BODY_BYTES,
            actual_size=len(raw_body),
        )
    if not _is_json_content_type(request.content_type):
        raise web.HTTPUnsupportedMediaType(
            reason="Extension routes accept only JSON request bodies.",
        )
    try:
        return cast(JSONValue, json.loads(raw_body.decode("utf-8")))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise web.HTTPBadRequest(reason="Extension route request body must be valid JSON.") from exc


def _bounded_query_mapping(query: Mapping[str, str]) -> dict[str, str]:
    items = list(query.items())
    if len(items) > _MAX_EXTENSION_ROUTE_QUERY_ENTRIES:
        raise web.HTTPBadRequest(reason="Too many extension route query parameters.")
    return {
        _bounded_text(
            key, field="query parameter name", max_bytes=_MAX_EXTENSION_ROUTE_KEY_BYTES
        ): _bounded_text(
            value,
            field=f"query parameter {key!r}",
            max_bytes=_MAX_EXTENSION_ROUTE_VALUE_BYTES,
        )
        for key, value in items
    }


def _selected_request_headers(headers: Mapping[str, str]) -> dict[str, str]:
    selected: dict[str, str] = {}
    for key, value in headers.items():
        normalized_key = key.lower()
        if normalized_key not in _SAFE_REQUEST_HEADERS:
            continue
        if normalized_key not in selected and len(selected) >= _MAX_EXTENSION_ROUTE_HEADER_ENTRIES:
            raise web.HTTPBadRequest(reason="Too many extension route request headers.")
        selected[
            _bounded_text(
                normalized_key,
                field="request header name",
                max_bytes=_MAX_EXTENSION_ROUTE_KEY_BYTES,
            )
        ] = _bounded_text(
            value,
            field=f"request header {normalized_key!r}",
            max_bytes=_MAX_EXTENSION_ROUTE_VALUE_BYTES,
        )
    return selected


def _web_response_from_portable(result: object) -> web.Response:
    if not isinstance(result, RouteResponse):
        raise InvalidExtensionResponseError("Extension routes must return a RouteResponse.")

    headers = _filtered_response_headers(result.headers)
    body, default_content_type = _serialize_response_body(result.body)
    if default_content_type is not None and "Content-Type" not in headers:
        headers["Content-Type"] = default_content_type
    return web.Response(status=result.status, body=body, headers=headers)


def _filtered_response_headers(headers: Mapping[str, str]) -> dict[str, str]:
    filtered: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in _FORBIDDEN_RESPONSE_HEADERS:
            raise InvalidExtensionResponseError(
                f"Extension routes must not set the {key!r} header."
            )
        filtered[key] = value
    return filtered


def _serialize_response_body(
    body: JSONValue | bytes | str | None,
) -> tuple[bytes | None, str | None]:
    if body is None:
        return None, None
    if isinstance(body, bytes):
        _require_response_size(body)
        return body, "application/octet-stream"
    if isinstance(body, str):
        encoded = body.encode("utf-8")
        _require_response_size(encoded)
        return encoded, "text/plain; charset=utf-8"

    try:
        encoded = json.dumps(
            body,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise InvalidExtensionResponseError("Extension route body must be finite JSON.") from exc
    _require_response_size(encoded)
    return encoded, "application/json"


def _require_response_size(body: bytes) -> None:
    if len(body) > _MAX_EXTENSION_ROUTE_BODY_BYTES:
        raise InvalidExtensionResponseError(
            f"Extension route bodies must be at most {_MAX_EXTENSION_ROUTE_BODY_BYTES} bytes."
        )


def _route_path_from_request(request: web.Request) -> str:
    suffix = request.match_info.get("path", "")
    return "/" if not suffix else f"/{suffix}"


def _bounded_text(value: str, *, field: str, max_bytes: int) -> str:
    if not isinstance(value, str):
        raise web.HTTPBadRequest(reason=f"Extension route {field} must be a string.")
    if "\r" in value or "\n" in value or "\x00" in value:
        raise web.HTTPBadRequest(reason=f"Extension route {field} must not contain CR, LF, or NUL.")
    if len(value.encode("utf-8")) > max_bytes:
        raise web.HTTPBadRequest(reason=f"Extension route {field} exceeds {max_bytes} bytes.")
    return value


def _is_json_content_type(content_type: str) -> bool:
    return content_type == "application/json" or content_type.endswith("+json")


def _error_response(
    request: web.Request,
    *,
    status: int,
    code: str,
    message: str,
) -> web.Response:
    request_id = request.get(REQUEST_ID_KEY)
    if not isinstance(request_id, str) or not request_id:
        request_id = uuid4().hex
    return web.json_response(
        {"error": {"code": code, "message": message, "request_id": request_id}},
        status=status,
    )
