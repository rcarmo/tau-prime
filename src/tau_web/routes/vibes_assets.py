"""Pinned public asset manifest for the replacement frontend (not yet routed)."""
from __future__ import annotations

import json
from importlib.resources import files
from pathlib import PurePosixPath

from aiohttp import web

_TYPES = {
    '.js': ('application/javascript', 'utf-8'),
    '.mjs': ('application/javascript', 'utf-8'),
    '.css': ('text/css', 'utf-8'),
    '.png': ('image/png', None),
    '.svg': ('image/svg+xml', None),
    '.ttf': ('font/ttf', None),
    '.woff2': ('font/woff2', None),
    '.json': ('application/json', 'utf-8'),
}


def asset_names() -> frozenset[str]:
    manifest = files('tau_web').joinpath('vibes', 'public-assets.json')
    return frozenset(json.loads(manifest.read_text(encoding='utf-8')))


def index_response() -> web.Response:
    resource = files('tau_web').joinpath('vibes', 'static', 'index.html')
    return web.Response(body=resource.read_bytes(), content_type='text/html', charset='utf-8',
                        headers={'Cache-Control': 'no-cache', 'X-Content-Type-Options': 'nosniff'})


def asset_response(name: str) -> web.Response:
    if name not in asset_names() or any(part in {'.', '..'} for part in name.split('/')):
        raise web.HTTPNotFound(reason='Unknown frontend asset.')
    suffix = PurePosixPath(name).suffix
    if suffix not in _TYPES:
        raise web.HTTPNotFound(reason='Unknown frontend asset type.')
    content_type, charset = _TYPES[suffix]
    resource = files('tau_web').joinpath('vibes', 'static', *name.split('/'))
    return web.Response(body=resource.read_bytes(), content_type=content_type, charset=charset,
                        headers={'Cache-Control': 'no-cache', 'X-Content-Type-Options': 'nosniff'})
