"""Production frontend routes: imported Vibes UI with Tau backend adapters."""
from __future__ import annotations

from aiohttp import web
from tau_web.routes.vibes_assets import asset_names, asset_response, index_response


def is_frontend_path(path: str) -> bool:
    if path in {'/', '/index.html', '/manifest.json', '/manifest.webmanifest', '/sw.js'}:
        return True
    return path.startswith('/static/') and path.removeprefix('/static/') in asset_names()


async def serve_root(request: web.Request) -> web.Response:
    return index_response()


async def serve_static(request: web.Request) -> web.Response:
    return asset_response(request.match_info['filename'])


async def serve_named_asset(request: web.Request) -> web.Response:
    if request.path == '/sw.js':
        response = asset_response('retire-sw.js')
        response.headers['Service-Worker-Allowed'] = '/'
        return response
    response = asset_response('manifest.json')
    response.content_type = 'application/manifest+json'
    return response


async def serve_index(request: web.Request) -> web.Response:
    return index_response()


def setup_routes(app: web.Application) -> None:
    app.router.add_get('/', serve_root)
    app.router.add_get('/index.html', serve_index)
    app.router.add_get('/manifest.json', serve_named_asset)
    app.router.add_get('/manifest.webmanifest', serve_named_asset)
    app.router.add_get('/sw.js', serve_named_asset)
    app.router.add_get('/static/{filename:.*}', serve_static)
