"""Baseline system meters route."""

from __future__ import annotations

from aiohttp import web

from tau_web.routes.common import services_for


def setup_routes(app: web.Application) -> None:
    app.router.add_get("/meters", get_meters)


async def get_meters(request: web.Request) -> web.Response:
    snapshot = services_for(request).meters.snapshot
    return web.json_response(
        snapshot.to_payload(),
        headers={"Cache-Control": "no-store"},
    )
