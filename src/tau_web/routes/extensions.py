"""Registered extension asset and route adapters for Tau Web."""

from __future__ import annotations

import asyncio
import html
import inspect
import json
import secrets
from collections.abc import Awaitable, Mapping
from typing import cast
from urllib.parse import quote
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
_MAX_FRONTEND_MODULES = 64
_MAX_WIDGET_ACTION_PAYLOAD_BYTES = 8 * 1024
_MAX_WIDGET_ACTION_RESULT_BYTES = 64 * 1024
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
    app.router.add_get("/api/extensions/frontend-modules", list_frontend_modules)
    app.router.add_get(
        "/api/extensions/widgets/{extension_id}/{widget_id}",
        get_widget_document,
    )
    app.router.add_post(
        "/api/extensions/widgets/{extension_id}/{widget_id}/actions/{action}",
        invoke_widget_action,
    )
    app.router.add_get("/api/extensions/assets/{extension_id}/{path:.*}", get_extension_asset)
    app.router.add_route("*", "/api/extensions/routes/{extension_id}", dispatch_extension_route)
    app.router.add_route(
        "*",
        "/api/extensions/routes/{extension_id}/{path:.*}",
        dispatch_extension_route,
    )


async def list_frontend_modules(request: web.Request) -> web.Response:
    modules = services_for(request).extensions.list_trusted_frontend_modules(
        limit=_MAX_FRONTEND_MODULES
    )
    return web.json_response(
        {
            "modules": [
                {
                    "extension_id": module.extension_id,
                    "module_id": module.module_id,
                    "sdk_version": module.sdk_version,
                    "integrity": module.integrity,
                    "asset_url": _frontend_module_asset_url(
                        module.extension_id,
                        module.asset_path,
                    ),
                }
                for module in modules
            ]
        },
        headers={"Cache-Control": "no-store"},
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


async def get_widget_document(request: web.Request) -> web.Response:
    extension_id = request.match_info["extension_id"]
    widget_id = request.match_info["widget_id"]
    directory = services_for(request).extensions
    widget = directory.lookup_widget(extension_id, widget_id)
    if widget is None:
        raise web.HTTPNotFound(reason="Unknown extension widget.")
    script_asset = directory.lookup_asset(extension_id, widget.script_path)
    style_asset = (
        directory.lookup_asset(extension_id, widget.style_path)
        if widget.style_path is not None
        else None
    )
    if script_asset is None or (widget.style_path is not None and style_asset is None):
        raise web.HTTPNotFound(reason="Unknown extension widget asset.")
    try:
        script = script_asset.content.decode("utf-8")
        style = style_asset.content.decode("utf-8") if style_asset is not None else ""
    except UnicodeDecodeError as exc:
        raise web.HTTPUnsupportedMediaType(reason="Widget assets must be UTF-8 text.") from exc

    nonce = secrets.token_urlsafe(24)
    csp = "; ".join(
        (
            "default-src 'none'",
            "base-uri 'none'",
            "connect-src 'none'",
            "font-src 'none'",
            "form-action 'none'",
            "frame-ancestors 'self'",
            "frame-src 'none'",
            "img-src data:",
            "media-src 'none'",
            "object-src 'none'",
            f"script-src 'nonce-{nonce}'",
            f"style-src 'nonce-{nonce}'",
        )
    )
    document = _widget_document(
        extension_id=extension_id,
        widget_id=widget.id,
        title=widget.title,
        nonce=nonce,
        csp=csp,
        style=style,
        script=script,
    )
    return web.Response(
        text=document,
        content_type="text/html",
        charset="utf-8",
        headers={
            "Cache-Control": "no-store",
            "Content-Security-Policy": csp,
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        },
    )


async def invoke_widget_action(request: web.Request) -> web.Response:
    raw_body = await request.read()
    if len(raw_body) > _MAX_WIDGET_ACTION_PAYLOAD_BYTES:
        raise web.HTTPRequestEntityTooLarge(
            max_size=_MAX_WIDGET_ACTION_PAYLOAD_BYTES,
            actual_size=len(raw_body),
        )
    if not raw_body:
        raise web.HTTPBadRequest(reason="Request body must be a JSON object.")
    if not _is_json_content_type(request.content_type):
        raise web.HTTPUnsupportedMediaType(
            reason="Content-Type must be application/json or a +json subtype."
        )
    try:
        body = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise web.HTTPBadRequest(reason="Request body must be valid JSON.") from exc
    if not isinstance(body, dict) or set(body) != {"payload"}:
        raise web.HTTPBadRequest(
            reason="Request body must contain exactly the 'payload' field."
        )
    payload = body["payload"]
    if not isinstance(payload, dict) or not all(isinstance(key, str) for key in payload):
        raise web.HTTPBadRequest(reason="Field 'payload' must be a JSON object.")
    try:
        result = await services_for(request).extensions.invoke_widget_action(
            request.match_info["extension_id"],
            request.match_info["widget_id"],
            request.match_info["action"],
            payload,
        )
    except LookupError as exc:
        raise web.HTTPNotFound(reason="Unknown extension widget action.") from exc
    except TimeoutError:
        return _error_response(
            request,
            status=504,
            code="widget_action_timeout",
            message="Widget action timed out.",
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        return _error_response(
            request,
            status=500,
            code="widget_action_error",
            message="Widget action failed.",
        )
    try:
        encoded = json.dumps(
            result,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError):
        return _error_response(
            request,
            status=502,
            code="invalid_widget_action_result",
            message="Widget action result must be finite JSON.",
        )
    if len(encoded) > _MAX_WIDGET_ACTION_RESULT_BYTES:
        return _error_response(
            request,
            status=502,
            code="widget_action_result_too_large",
            message=(
                f"Widget action result must be at most {_MAX_WIDGET_ACTION_RESULT_BYTES} bytes."
            ),
        )
    return web.Response(body=encoded, content_type="application/json")


def _widget_document(
    *,
    extension_id: str,
    widget_id: str,
    title: str,
    nonce: str,
    csp: str,
    style: str,
    script: str,
) -> str:
    escaped_script = script.replace("</script", "<\\/script")
    escaped_style = style.replace("</style", "<\\/style")
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<meta http-equiv="Content-Security-Policy" content="{html.escape(csp, quote=True)}">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{html.escape(title)}</title>"
        f'<style nonce="{nonce}">{escaped_style}</style>'
        f'<script nonce="{nonce}" src="/static/widget-bridge.js"></script>'
        "</head>"
        f'<body data-extension-id="{html.escape(extension_id, quote=True)}" '
        f'data-widget-id="{html.escape(widget_id, quote=True)}">'
        '<main id="tau-widget-root"></main>'
        f'<script nonce="{nonce}">{escaped_script}</script>'
        "</body></html>"
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


def _frontend_module_asset_url(extension_id: str, asset_path: str) -> str:
    return (
        f"/api/extensions/assets/{quote(extension_id, safe='')}"
        f"/{quote(asset_path, safe='/')}"
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
