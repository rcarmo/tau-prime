import pytest
from aiohttp import web

from tau_web.routes.vibes_assets import asset_names, asset_response


def test_public_manifest_contains_runtime_not_tooling():
    names = asset_names()
    assert {"dist/app.js", "dist/app.css", "js/bootstrap.js"} <= names
    assert not any(name.endswith(".map") or "node_modules" in name for name in names)
    assert "build.js" not in names
    for name in names:
        response = asset_response(name)
        assert response.status == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        if name.endswith(".mjs"):
            assert response.content_type == "application/javascript"


@pytest.mark.parametrize(
    "name", ["../LICENSE", "/etc/passwd", "dist/app.js.map", "build.js", "js/../js/app.js"]
)
def test_unlisted_and_traversal_assets_rejected(name):
    with pytest.raises(web.HTTPNotFound):
        asset_response(name)


def test_public_manifest_matches_runtime_tree():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "src/tau_web/vibes/static"
    suffixes = {".js", ".mjs", ".css", ".png", ".svg", ".ttf", ".woff2", ".json"}
    expected = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.suffix in suffixes
    }
    assert asset_names() == expected


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_replacement_entrypoint_assets_over_http():
    import re

    from aiohttp.test_utils import TestClient, TestServer

    from tau_web.routes.vibes_assets import index_response

    app = web.Application()

    async def root(request):
        return index_response()

    async def static(request):
        return asset_response(request.match_info["name"])

    async def manifest(request):
        return asset_response("manifest.json")

    app.router.add_get("/", root)
    app.router.add_get("/manifest.json", manifest)
    app.router.add_get("/static/{name:.*}", static)
    async with TestClient(TestServer(app)) as client:
        response = await client.get("/")
        assert response.status == 200
        html = await response.text()
        assert "<title>Tau</title>" in html
        for url in set(re.findall(r'(?:src|href)="([^"]+)"', html)):
            asset = await client.get(url)
            assert asset.status == 200, url
            assert asset.headers["X-Content-Type-Options"] == "nosniff"
        for url in ("/static/dist/app.js", "/static/dist/app.css"):
            assert (await client.get(url)).status == 200
        assert (await client.get("/static/dist/app.js.map")).status == 404
        assert (await client.get("/static/build.js")).status == 404
