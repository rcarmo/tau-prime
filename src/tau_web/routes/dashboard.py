"""Bundled multi-session dashboard route."""

from __future__ import annotations

from aiohttp import web

from tau_web.routes.common import json_response, services_for

_DEFAULT_PAGE_SIZE = 8
_MAX_PAGE_SIZE = 50


async def get_dashboard(request: web.Request) -> web.Response:
    """Return one bounded page of aggregated dashboard state."""
    page = _positive_query(request, "page", default=1)
    page_size = _positive_query(request, "page_size", default=_DEFAULT_PAGE_SIZE)
    if page_size > _MAX_PAGE_SIZE:
        raise web.HTTPBadRequest(
            reason=f"Query parameter 'page_size' must not exceed {_MAX_PAGE_SIZE}."
        )
    snapshot = await services_for(request).dashboard.snapshot(page=page, page_size=page_size)
    response = json_response(snapshot)
    response.headers["Cache-Control"] = "no-store"
    return response


def _positive_query(request: web.Request, field: str, *, default: int) -> int:
    raw = request.query.get(field)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise web.HTTPBadRequest(
            reason=f"Query parameter '{field}' must be an integer."
        ) from exc
    if value <= 0:
        raise web.HTTPBadRequest(reason=f"Query parameter '{field}' must be positive.")
    return value


def setup_routes(app: web.Application) -> None:
    app.router.add_get("/dashboard", get_dashboard)
