"""aiohttp-only middleware for Tau Web request metadata and security checks."""

from __future__ import annotations

import asyncio
import re
import secrets
from collections.abc import Awaitable, Callable, Mapping
from http import HTTPStatus
from uuid import uuid4

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import StreamResponse

from tau_web.config import WebConfig, normalize_origin

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_KEY = web.RequestKey[str]("tau.web.request_id")
CSRF_HEADER = "X-Tau-CSRF"
_HEALTH_PATH = "/api/health"
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
_REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")

Handler = Callable[[Request], Awaitable[StreamResponse]]
Middleware = Callable[[Request, Handler], Awaitable[StreamResponse]]


def build_middlewares(config: WebConfig) -> tuple[Middleware, ...]:
    """Return Tau Web middlewares in outer-to-inner order."""
    from tau_web.routes.frontend import is_frontend_path

    @web.middleware
    async def request_id_middleware(request: Request, handler: Handler) -> StreamResponse:
        request_id = _request_id_from_header(request.headers.get(REQUEST_ID_HEADER))
        request[REQUEST_ID_KEY] = request_id
        try:
            response = await handler(request)
        except asyncio.CancelledError:
            raise
        response.headers[REQUEST_ID_HEADER] = request_id
        return response

    @web.middleware
    async def frontend_security_headers_middleware(
        request: Request,
        handler: Handler,
    ) -> StreamResponse:
        response = await handler(request)
        if is_frontend_path(request.path):
            response.headers.setdefault(
                "Content-Security-Policy",
                "; ".join(
                    (
                        "default-src 'self'",
                        "base-uri 'none'",
                        "connect-src 'self'",
                        "font-src 'self'",
                        "form-action 'self'",
                        "frame-ancestors 'none'",
                        "img-src 'self' data:",
                        "manifest-src 'self'",
                        "object-src 'none'",
                        "script-src 'self'",
                        "style-src 'self'",
                        "worker-src 'self'",
                    )
                ),
            )
            response.headers.setdefault("Referrer-Policy", "same-origin")
            response.headers.setdefault("X-Content-Type-Options", "nosniff")
            response.headers.setdefault("X-Frame-Options", "DENY")
        return response

    @web.middleware
    async def structured_error_middleware(request: Request, handler: Handler) -> StreamResponse:
        try:
            return await handler(request)
        except asyncio.CancelledError:
            raise
        except web.HTTPException as exc:
            return _json_error_response(
                request,
                status=exc.status,
                code=_status_code_name(exc.status),
                message=_http_exception_message(exc),
                headers=exc.headers,
            )
        except Exception:
            return _json_error_response(
                request,
                status=500,
                code="internal_server_error",
                message="Internal Server Error",
            )

    @web.middleware
    async def bearer_auth_middleware(request: Request, handler: Handler) -> StreamResponse:
        auth_token = config.auth_token
        if auth_token is None or request.path == _HEALTH_PATH or is_frontend_path(request.path):
            return await handler(request)

        authorization = request.headers.get("Authorization")
        scheme, separator, candidate = (
            authorization.partition(" ") if authorization else ("", "", "")
        )
        if (
            separator != " "
            or scheme.lower() != "bearer"
            or not secrets.compare_digest(
                candidate,
                auth_token,
            )
        ):
            raise web.HTTPUnauthorized(
                reason="Missing or invalid bearer token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return await handler(request)

    @web.middleware
    async def origin_csrf_middleware(request: Request, handler: Handler) -> StreamResponse:
        if request.method in _SAFE_METHODS:
            return await handler(request)

        raw_origin = request.headers.get("Origin")
        if raw_origin is None:
            return await handler(request)

        try:
            origin = normalize_origin(raw_origin)
            request_origin = normalize_origin(f"{request.scheme}://{request.host}")
        except ValueError as exc:
            raise web.HTTPForbidden(reason=str(exc)) from exc

        if origin != request_origin and origin not in config.allowed_origins:
            raise web.HTTPForbidden(reason="Origin is not allowed.")
        if request.headers.get(CSRF_HEADER) != "1":
            raise web.HTTPForbidden(reason="Missing or invalid CSRF header.")
        return await handler(request)

    return (
        request_id_middleware,
        frontend_security_headers_middleware,
        structured_error_middleware,
        bearer_auth_middleware,
        origin_csrf_middleware,
    )


def _json_error_response(
    request: Request,
    *,
    status: int,
    code: str,
    message: str,
    headers: Mapping[str, str] | None = None,
) -> web.Response:
    return web.json_response(
        {
            "error": {
                "code": code,
                "message": message,
                "request_id": _request_id_for(request),
            }
        },
        status=status,
        headers=_filtered_headers(headers),
    )


def _request_id_from_header(request_id: str | None) -> str:
    if request_id is not None:
        candidate = request_id.strip()
        if _REQUEST_ID_PATTERN.fullmatch(candidate) is not None:
            return candidate
    return uuid4().hex


def _request_id_for(request: Request) -> str:
    request_id = request.get(REQUEST_ID_KEY)
    if isinstance(request_id, str) and request_id:
        return request_id
    return uuid4().hex


def _http_exception_message(exc: web.HTTPException) -> str:
    if exc.reason:
        return exc.reason
    if exc.text:
        return exc.text
    return _status_message(exc.status)


_STATUS_CODE_NAMES = {
    413: "request_entity_too_large",
}


def _status_code_name(status: int) -> str:
    if status in _STATUS_CODE_NAMES:
        return _STATUS_CODE_NAMES[status]
    try:
        return HTTPStatus(status).name.lower()
    except ValueError:
        return f"http_{status}"


def _status_message(status: int) -> str:
    try:
        return HTTPStatus(status).phrase
    except ValueError:
        return f"HTTP {status}"


def _filtered_headers(headers: Mapping[str, str] | None) -> dict[str, str]:
    if headers is None:
        return {}

    filtered: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in {"content-length", "content-type"}:
            continue
        filtered[key] = value
    return filtered
