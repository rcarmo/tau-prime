from __future__ import annotations

import json
import re

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
)
FRONTEND_ASSETS = (
    ("/", "text/html"),
    ("/index.html", "text/html"),
    ("/manifest.webmanifest", "application/manifest+json"),
    ("/sw.js", "application/javascript"),
    ("/static/app.css", "text/css"),
    ("/static/app.js", "application/javascript"),
    ("/static/live-ui.js", "application/javascript"),
    ("/static/extension-ui.js", "application/javascript"),
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
    assert '<link rel="manifest" href="/manifest.webmanifest" />' in root_html
    assert '<link rel="stylesheet" href="/static/app.css" />' in root_html
    assert '<script type="module" src="/static/app.js"></script>' in root_html
    assert '<script type="module" src="/static/live-ui.js"></script>' in root_html
    assert '<script type="module" src="/static/extension-ui.js"></script>' in root_html
    assert {
        match.group(1)
        for match in re.finditer(r'data-extension-slot="([^"]+)"', root_html)
    } == {
        "compose_above",
        "compose_below",
        "sidebar",
        "timeline_before",
        "timeline_after",
        "dashboard",
    }
    assert root_html.count('data-extension-slot="') == 6
    assert re.search(r"<header\b", root_html) is not None
    assert re.search(r'<main\b[^>]*id="timeline-main"', root_html) is not None
    assert re.search(r"<footer\b", root_html) is not None
    assert re.search(r'<aside\b[^>]*id="session-nav"', root_html) is not None
    assert re.search(r'<aside\b[^>]*id="side-panel"', root_html) is not None
    for field_id in (
        "workspace-editor",
        "search-input",
        "plan-editor",
        "auth-token",
        "provider-input",
        "model-input",
        "thinking-level-select",
        "compose-provider-select",
        "compose-model-select",
        "compose-thinking-select",
        "compose-delivery-mode",
        "compose-input",
    ):
        assert f'for="{field_id}"' in root_html
    for element_id in (
        "compose-context-readout",
        "compose-attachment-button",
        "compose-file-input",
        "compose-attachment-list",
        "compose-clear-attachments",
        "compose-completion-popup",
        "compose-completion-listbox",
        "compose-completion-status",
        "plan-revision",
        "plan-status",
        "plan-conflict",
        "plan-save-button",
        "plan-reload-button",
        "system-meters",
        "meters-summary",
        "meters-collapse-button",
        "meters-visibility-button",
        "meters-details",
        "meter-cpu-sparkline",
        "meter-ram-sparkline",
        "meter-rss-sparkline",
        "meter-swap-sparkline",
    ):
        assert f'id="{element_id}"' in root_html


@pytest.mark.anyio
async def test_app_js_contains_tau_endpoints_sse_parser_and_safe_dom_updates(
    web_config: WebConfig,
) -> None:
    app = create_app(web_config)
    client = await _start_client(app)

    try:
        async with client.get("/static/app.js") as response:
            script = await response.text()
    finally:
        await client.close()

    for endpoint in (
        "/api/sessions",
        "/api/settings",
        "/api/models",
        "/api/commands",
        "/api/files",
        "/api/media",
        "/api/search",
        "/api/events",
        "/meters",
        "/queue",
    ):
        assert endpoint in script
    assert 'accept: "text/event-stream"' in script
    assert "readEventStream" in script
    assert "parseEventChunk" in script
    assert 'case "tau.plan.updated"' in script
    assert 'frame.event === "tau.meters.updated"' in script
    assert "startMetersPolling" in script
    assert 'document.addEventListener("visibilitychange", handleMetersVisibilityChange)' in script
    assert '"tau.web.metersEnabled"' in script
    assert '"tau.web.metersCollapsed"' in script
    assert "expected_revision" in script
    assert 'navigator.serviceWorker.register("/sw.js", { scope: "/" });' in script
    assert ".innerHTML" not in script
    assert (
        re.search(
            r"(?i)\bpi\b|\bacp\b|pi[_-]?client|acp[_-]?client",
            script,
        )
        is None
    )


@pytest.mark.anyio
async def test_live_ui_wires_runtime_controls_and_stream_events(web_config: WebConfig) -> None:
    app = create_app(web_config)
    client = await _start_client(app)
    try:
        async with client.get("/static/live-ui.js") as response:
            script = await response.text()
    finally:
        await client.close()

    for endpoint in ("/thinking", "/usage", "/runs", "/queue"):
        assert endpoint in script
    assert 'mutateRun(activeRun.run_id, "cancel")' in script
    assert 'mutateRun(activeRun.run_id, "abort")' in script
    assert "window.tauLiveUI = Object.freeze" in script
    assert "submitComposerMessage" in script
    assert "handleComposeIntercept" not in script
    for event_type in (
        "thinking_delta",
        "tool_execution_start",
        "tool_execution_update",
        "tool_execution_end",
        "queue_update",
        "message_end",
    ):
        assert event_type in script
    assert ".innerHTML" not in script


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
async def test_app_css_contains_responsive_media_queries(web_config: WebConfig) -> None:
    app = create_app(web_config)
    client = await _start_client(app)

    try:
        async with client.get("/static/app.css") as response:
            stylesheet = await response.text()
    finally:
        await client.close()

    assert "@media (max-width: 960px)" in stylesheet
    assert "@media (max-width: 720px)" in stylesheet
    assert ".shell-layout" in stylesheet
    assert ".mobile-only" in stylesheet
    assert ".extension-slot" in stylesheet
    assert ".tau-extension-view" in stylesheet
    assert ".tau-extension-stack" in stylesheet
    assert ".compose-select-grid" in stylesheet
    assert ".compose-attachment-list" in stylesheet
    assert ".compose-completion-popup" in stylesheet
    assert ".attachment-chip" in stylesheet
    assert '[data-extension-slot="dashboard"]' in stylesheet
    assert '[data-extension-slot="compose_above"]' in stylesheet
    assert '[data-extension-slot="compose_below"]' in stylesheet


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

    assert manifest == {
        "name": "Tau Web Shell",
        "short_name": "Tau",
        "description": (
            "Responsive shell for persisted Tau sessions, timeline playback, and "
            "workspace browsing."
        ),
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#0b1220",
        "theme_color": "#0f172a",
        "lang": "en",
    }
    for asset_path in (
        "/",
        "/index.html",
        "/manifest.webmanifest",
        "/static/app.css",
        "/static/app.js",
        "/static/live-ui.js",
        "/static/extension-ui.js",
    ):
        assert f'"{asset_path}"' in worker


@pytest.mark.anyio
@pytest.mark.parametrize(
    "path",
    (
        "/static/not-found.js",
        "/static/../app.js",
        "/static/%2e%2e/app.js",
        "/static/%2e%2e%2fapp.js",
    ),
)
async def test_unknown_or_traversal_frontend_paths_return_404(
    web_config: WebConfig,
    path: str,
) -> None:
    app = create_app(web_config)
    client = await _start_client(app)

    try:
        async with client.get(path) as response:
            assert response.status == 404
            payload = await response.json()
    finally:
        await client.close()

    assert payload["error"]["code"] == "not_found"
