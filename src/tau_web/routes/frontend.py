"""Frontend shell routes for Tau Web."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from typing import Final

from aiohttp import web

_FRONTEND_PUBLIC_PATHS: Final[frozenset[str]] = frozenset(
    {
        "/",
        "/index.html",
        "/manifest.webmanifest",
        "/sw.js",
        "/static/app.css",
        "/static/app.js",
        "/static/live-ui.js",
    }
)


@dataclass(frozen=True, slots=True)
class FrontendAsset:
    resource_name: str
    content_type: str
    charset: str | None
    cache_control: str
    service_worker_allowed: str | None = None


_ROOT_ASSETS: Final[dict[str, FrontendAsset]] = {
    "/": FrontendAsset(
        resource_name="index.html",
        content_type="text/html",
        charset="utf-8",
        cache_control="no-cache",
    ),
    "/index.html": FrontendAsset(
        resource_name="index.html",
        content_type="text/html",
        charset="utf-8",
        cache_control="no-cache",
    ),
    "/manifest.webmanifest": FrontendAsset(
        resource_name="manifest.webmanifest",
        content_type="application/manifest+json",
        charset="utf-8",
        cache_control="no-cache",
    ),
    "/sw.js": FrontendAsset(
        resource_name="sw.js",
        content_type="application/javascript",
        charset="utf-8",
        cache_control="no-cache",
        service_worker_allowed="/",
    ),
}

_STATIC_ASSETS: Final[dict[str, FrontendAsset]] = {
    "app.css": FrontendAsset(
        resource_name="app.css",
        content_type="text/css",
        charset="utf-8",
        cache_control="public, max-age=3600, must-revalidate",
    ),
    "app.js": FrontendAsset(
        resource_name="app.js",
        content_type="application/javascript",
        charset="utf-8",
        cache_control="public, max-age=3600, must-revalidate",
    ),
    "live-ui.js": FrontendAsset(
        resource_name="live-ui.js",
        content_type="application/javascript",
        charset="utf-8",
        cache_control="public, max-age=3600, must-revalidate",
    ),
}


def is_frontend_path(path: str) -> bool:
    return path in _FRONTEND_PUBLIC_PATHS


async def serve_root(request: web.Request) -> web.Response:
    return _asset_response(_ROOT_ASSETS[request.path])


async def serve_static(request: web.Request) -> web.Response:
    filename = request.match_info["filename"]
    asset = _STATIC_ASSETS.get(filename)
    if asset is None:
        raise web.HTTPNotFound(reason="Unknown frontend asset.")
    return _asset_response(asset)


async def serve_named_asset(request: web.Request) -> web.Response:
    asset = _ROOT_ASSETS.get(request.path)
    if asset is None:
        raise web.HTTPNotFound(reason="Unknown frontend asset.")
    return _asset_response(asset)


async def serve_index(request: web.Request) -> web.Response:
    del request
    return _asset_response(_ROOT_ASSETS["/index.html"])


def _asset_response(asset: FrontendAsset) -> web.Response:
    resource = files("tau_web").joinpath("static").joinpath(asset.resource_name)
    data = resource.read_bytes()
    headers = {"Cache-Control": asset.cache_control}
    if asset.service_worker_allowed is not None:
        headers["Service-Worker-Allowed"] = asset.service_worker_allowed
    return web.Response(
        body=data,
        content_type=asset.content_type,
        charset=asset.charset,
        headers=headers,
    )


def setup_routes(app: web.Application) -> None:
    app.router.add_get("/", serve_root)
    app.router.add_get("/index.html", serve_index)
    app.router.add_get("/manifest.webmanifest", serve_named_asset)
    app.router.add_get("/sw.js", serve_named_asset)
    app.router.add_get("/static/{filename}", serve_static)
