from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from tau_web.app import create_app
from tau_web.config import WebConfig

CSP_HEADER = "; ".join(
    (
        "default-src 'self'",
        "base-uri 'none'",
        "connect-src 'self'",
        "font-src 'self' data:",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "img-src 'self' blob: data:",
        "manifest-src 'self'",
        "object-src 'none'",
        "script-src 'self' blob:",
        "style-src 'self'",
        "worker-src 'self'",
    )
)
FRONTEND_ASSETS = (
    ("/", "text/html"),
    ("/index.html", "text/html"),
    ("/manifest.webmanifest", "application/manifest+json"),
    ("/sw.js", "application/javascript"),
    ("/static/dist/app.css", "text/css"),
    ("/static/common/fonts/vendor/firacode-nerd-font-mono-bold.ttf", "font/ttf"),
    ("/static/common/fonts/vendor/firacode-nerd-font-mono-regular.ttf", "font/ttf"),
    ("/static/dist/app.js", "application/javascript"),
    ("/static/extension-ui.js", "application/javascript"),
    ("/static/widget-bridge.js", "application/javascript"),
    ("/static/frontend-sdk.js", "application/javascript"),
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def _start_client(app: web.Application) -> TestClient:
    client = TestClient(TestServer(app))
    await client.start_server()
    return client


@pytest.mark.anyio
@pytest.mark.parametrize(("path", "content_type"), FRONTEND_ASSETS)
async def test_frontend_assets_return_expected_status_types_and_headers(
    web_config: WebConfig,
    path: str,
    content_type: str,
) -> None:
    app = create_app(web_config)
    client = await _start_client(app)

    try:
        async with client.get(path) as response:
            assert response.status == 200
            assert response.content_type == content_type
            assert response.headers["Content-Security-Policy"] == CSP_HEADER
            assert response.headers["Referrer-Policy"] == "same-origin"
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers["X-Frame-Options"] == "DENY"
            assert response.headers["Permissions-Policy"] == (
                "camera=(), geolocation=(), microphone=(), payment=(), usb=()"
            )
            assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
            if path == "/sw.js":
                assert response.headers["Service-Worker-Allowed"] == "/"
            else:
                assert "Service-Worker-Allowed" not in response.headers
    finally:
        await client.close()


@pytest.mark.anyio
async def test_index_html_references_frontend_assets_landmarks_and_labels(
    web_config: WebConfig,
) -> None:
    app = create_app(web_config)
    client = await _start_client(app)

    try:
        async with client.get("/") as root_response:
            root_html = await root_response.text()
        async with client.get("/index.html") as index_response:
            index_html = await index_response.text()
    finally:
        await client.close()

    assert root_html == index_html
    assert '<script type="module" src="/static/js/bootstrap.js"></script>' in root_html
    assert '/static/dist/app.css' in root_html
    assert '<title>Tau</title>' in root_html
    assert '/static/preact-shell.js' not in root_html
    assert 'user-scalable=no' not in root_html


@pytest.mark.anyio
async def test_app_js_contains_tau_endpoints_sse_parser_and_safe_dom_updates(web_config):
    client = await _start_client(create_app(web_config))
    try:
        response = await client.get('/static/js/tau-client.js')
        assert response.status == 200
        script = await response.text()
        stream = await (await client.get('/static/js/tau-events.js')).text()
    finally:
        await client.close()
    assert 'X-Tau-CSRF' in script
    assert 'Authorization' in script
    assert '/api/events' in stream
    assert 'Last-Event-ID' in stream
    assert 'consumeTauEvents' in stream


@pytest.mark.anyio
async def test_extension_ui_script_exposes_safe_extension_view_renderer(
    web_config: WebConfig,
) -> None:
    app = create_app(web_config)
    client = await _start_client(app)

    try:
        async with client.get("/static/extension-ui.js") as response:
            script = await response.text()
    finally:
        await client.close()

    assert "tau:extension-view" in script
    assert "tau:extension-action" in script
    assert "window.tauExtensionUI" in script
    assert ".innerHTML" not in script
    assert "eval(" not in script
    for name in (
        "buildText",
        "buildButton",
        "buildMetric",
        "buildProgress",
        "buildField",
        "buildTable",
        "buildStack",
    ):
        assert name in script
    for limit in (
        "viewBytes: 64 * 1024",
        "payloadBytes: 8 * 1024",
        "depth: 12",
        "nodes: 256",
        "textBytes: 16 * 1024",
        "tableRows: 50",
        "tableColumns: 20",
    ):
        assert limit in script


@pytest.mark.anyio
async def test_frontend_sdk_exposes_loader_without_eval_or_inner_html(
    web_config: WebConfig,
) -> None:
    app = create_app(web_config)
    client = await _start_client(app)

    try:
        async with client.get("/static/frontend-sdk.js") as response:
            script = await response.text()
    finally:
        await client.close()

    assert "window.tauFrontendSDK" in script
    assert "configure:" in script
    assert "loadAll:" in script
    assert "disposeAll:" in script
    assert ".innerHTML" not in script
    assert "eval(" not in script
    assert "new Function" not in script


def test_frontend_sdk_node_vm_contracts() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node executable not found")

    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "tests" / "web" / "frontend-sdk.test.mjs"
    result = subprocess.run(
        [node, str(script)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "frontend-sdk node vm tests failed\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


@pytest.mark.anyio
async def test_manifest_and_service_worker_match_shell_asset_references(
    web_config: WebConfig,
) -> None:
    app = create_app(web_config)
    client = await _start_client(app)

    try:
        async with client.get("/manifest.webmanifest") as manifest_response:
            manifest = json.loads(await manifest_response.text())
        async with client.get("/sw.js") as worker_response:
            worker = await worker_response.text()
    finally:
        await client.close()

    assert manifest['name'] == 'Tau'
    assert manifest['start_url'] == '/'
    assert "name.startsWith('tau-web-shell-')" in worker
    assert 'registration.unregister()' in worker
    assert "addEventListener('fetch'" not in worker


