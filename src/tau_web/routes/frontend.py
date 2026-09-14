"""Production frontend routes: imported Vibes UI with Tau backend adapters."""

from __future__ import annotations

from importlib.resources import files

from aiohttp import web

from tau_web.routes.vibes_assets import asset_names, asset_response, index_response


def is_frontend_path(path: str) -> bool:
    if path in {
        "/",
        "/index.html",
        "/manifest.json",
        "/manifest.webmanifest",
        "/sw.js",
        "/offline-sw.js",
        "/static/widget-bridge.js",
        "/static/extension-ui.js",
        "/static/frontend-sdk.js",
    }:
        return True
    return path.startswith("/static/") and path.removeprefix("/static/") in asset_names()


async def serve_root(request: web.Request) -> web.Response:
    return index_response()


async def serve_static(request: web.Request) -> web.Response:
    name = request.match_info["filename"]
    # Extension contracts remain independent of the replaced chat shell.
    if name in {"widget-bridge.js", "extension-ui.js", "frontend-sdk.js"}:
        return web.Response(
            body=files("tau_web").joinpath("static", name).read_bytes(),
            content_type="application/javascript",
            charset="utf-8",
            headers={"Cache-Control": "no-cache"},
        )
    return asset_response(name)


async def serve_named_asset(request: web.Request) -> web.Response:
    if request.path == "/sw.js":
        response = asset_response("retire-sw.js")
        response.headers["Service-Worker-Allowed"] = "/"
        return response
    response = asset_response("manifest.json")
    response.content_type = "application/manifest+json"
    return response


async def serve_index(request: web.Request) -> web.Response:
    return index_response()


async def serve_offline_worker(request: web.Request) -> web.Response:
    response = asset_response("offline-sw.js")
    response.headers["Service-Worker-Allowed"] = "/"
    return response


def setup_routes(app: web.Application) -> None:
    app.router.add_get("/", serve_root)
    app.router.add_get("/index.html", serve_index)
    app.router.add_get("/manifest.json", serve_named_asset)
    app.router.add_get("/manifest.webmanifest", serve_named_asset)
    app.router.add_get("/sw.js", serve_named_asset)
    app.router.add_get("/offline-sw.js", serve_offline_worker)
    app.router.add_get("/static/{filename:.*}", serve_static)
