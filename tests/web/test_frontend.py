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
        "font-src 'self'",
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
    ("/static/app.css", "text/css"),
    ("/static/piclaw-reference.css", "text/css"),
    ("/static/app.js", "application/javascript"),
    ("/static/live-ui.js", "application/javascript"),
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
    shell_html = (
        Path(__file__).parents[2] / "src" / "tau_web" / "frontend" / "src" / "shell.html"
    ).read_text(encoding="utf-8")
    assert '<script type="module" src="/static/preact-shell.js"></script>' in root_html
    preact_script = '<script type="module" src="/static/preact-shell.js"></script>'
    live_script = '<script type="module" src="/static/live-ui.js"></script>'
    assert root_html.index(preact_script) < root_html.index(live_script)
    root_html += shell_html
    assert '<link rel="manifest" href="/manifest.webmanifest" />' in root_html
    assert '<link rel="stylesheet" href="/static/app.css" />' in root_html
    assert '<link rel="stylesheet" href="/static/piclaw-reference.css" />' in root_html
    assert '<script type="module" src="/static/live-ui.js"></script>' in root_html
    assert '<script type="module" src="/static/extension-ui.js"></script>' in root_html
    assert '<script type="module" src="/static/frontend-sdk.js"></script>' in root_html
    assert '<script type="module" src="/static/app.js"></script>' in root_html
    extension_script = '<script type="module" src="/static/extension-ui.js"></script>'
    frontend_sdk_script = '<script type="module" src="/static/frontend-sdk.js"></script>'
    app_script = '<script type="module" src="/static/app.js"></script>'
    assert root_html.index(extension_script) < root_html.index(frontend_sdk_script)
    assert root_html.index(frontend_sdk_script) < root_html.index(app_script)
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
        "dashboard-toggle",
        "dashboard-count",
        "session-dashboard",
        "dashboard-close",
        "dashboard-grid",
        "dashboard-age",
        "dashboard-previous",
        "dashboard-page",
        "dashboard-next",
        "dashboard-manage",
    ):
        assert f'id="{element_id}"' in root_html
    assert (
        re.search(r'<textarea\b[^>]*id="compose-input"[^>]*role="combobox"', root_html)
        is not None
    )
    assert (
        re.search(
            r'<input\b[^>]*id="compose-file-input"[^>]*aria-label="Attach files"',
            root_html,
        )
        is not None
    )
    branch_list_markup = re.search(r'<div\b[^>]*id="branch-list"[^>]*>', root_html)
    assert branch_list_markup is not None
    assert 'role="list"' not in branch_list_markup.group(0)
    search_results_markup = re.search(r'<ol\b[^>]*id="search-results"[^>]*>', root_html)
    assert search_results_markup is not None
    assert 'tabindex="0"' in search_results_markup.group(0)
    assert 'aria-label="Search results"' in search_results_markup.group(0)


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
        "/api/approvals/",
        "/approvals",
        "/meters",
        "/dashboard",
        "/queue",
    ):
        assert endpoint in script
    assert 'accept: "text/event-stream"' in script
    assert "readEventStream" in script
    assert "parseEventChunk" in script
    assert 'case "tau.plan.updated"' in script
    assert 'case "tau.approval.requested"' in script
    assert 'case "tau.approval.resolved"' in script
    assert 'frame.event === "tau.meters.updated"' in script
    assert 'frame.event === "tau.dashboard.updated"' in script
    assert "loadApprovals" in script
    assert "renderApprovalPrompt" in script
    assert "settleApproval" in script
    assert "startMetersPolling" in script
    assert "startDashboardTimers" in script
    assert "stopDashboardTimers" in script
    assert 'document.addEventListener("visibilitychange", handleMetersVisibilityChange)' in script
    assert '"tau.web.metersEnabled"' in script
    assert '"tau.web.metersCollapsed"' in script
    assert 'new URL(window.location.href).searchParams.get("session_id")' in script
    assert 'window.history.replaceState(null, "", nextUrl);' in script
    assert 'window.open(buildSessionUrl(session.session_id), "_blank", "noopener")' in script
    assert (
        "void selectSession(session.session_id, "
        "{ reconnect: true, focusTimeline: true });"
    ) in script
    assert 'event.code === "Backquote"' in script
    assert 'setDashboardOpen(false);' in script
    assert 'window.setInterval(updateDashboardAgeLabels, 1000);' in script
    assert "15000" in script
    assert "3000" in script
    assert "expected_revision" in script
    assert 'navigator.serviceWorker.register("/sw.js", { scope: "/" });' in script
    capacity_pattern = (
        r"function dashboardCapacity\(\) \{[\s\S]*"
        r"window\.innerWidth < 760[\s\S]*return 4;[\s\S]*"
        r"window\.innerWidth < 1080[\s\S]*return 6;[\s\S]*return 8;"
    )
    assert re.search(capacity_pattern, script) is not None
    assert ".innerHTML" not in script
    assert (
        re.search(
            r"(?i)\bpi\b|\bacp\b|pi[_-]?client|acp[_-]?client",
            script,
        )
        is None
    )


def test_app_js_trusted_frontend_source_contracts() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = (repo_root / "src" / "tau_web" / "static" / "app.js").read_text(encoding="utf-8")

    init_start = script.index("async function init() {")
    init_end = script.index("function bindUi()", init_start)
    init_block = script[init_start:init_end]
    refresh_call = 'await refreshShell({ reconnect: true, announceMessage: "Tau shell ready." });'
    trusted_init_call = "void initializeTrustedFrontendModules();"
    assert refresh_call in init_block
    assert trusted_init_call in init_block
    assert init_block.index(refresh_call) < init_block.index(trusted_init_call)

    trusted_start = script.index("async function submitTrustedFrontendMessage(payload) {")
    trusted_end = script.index("async function apiFetch(path, options = {}) {", trusted_start)
    trusted_block = script[trusted_start:trusted_end]
    assert 'const response = await apiFetch("/api/extensions/frontend-modules");' in trusted_block
    configure_start = trusted_block.index("sdk.configure({")
    fetch_asset_index = trusted_block.index("fetchAsset: authenticatedFetch", configure_start)
    request_index = trusted_block.index("request: apiFetch", configure_start)
    submit_index = trusted_block.index("submit: submitTrustedFrontendMessage", configure_start)
    navigate_index = trusted_block.index("navigate: navigateTrustedFrontend", configure_start)
    assert configure_start < fetch_asset_index < request_index < submit_index < navigate_index
    assert "json: { content: text }" in trusted_block
    assert ".innerHTML" not in trusted_block
    assert "eval(" not in trusted_block
    assert "new Function" not in trusted_block

    navigate_start = trusted_block.index("async function navigateTrustedFrontend(target) {")
    navigate_end = trusted_block.index(
        "async function initializeTrustedFrontendModules()",
        navigate_start,
    )
    navigate_block = trusted_block[navigate_start:navigate_end]
    assert "stringOrEmpty(entry.session_id).trim()" in navigate_block
    assert "stringOrEmpty(entry.chat_jid).trim()" in navigate_block
    assert "stringOrEmpty(entry.name).trim()" in navigate_block
    assert "stringOrEmpty(entry.alias).trim()" in navigate_block
    assert "selectSession(sessionId, { reconnect: true, focusTimeline: true })" in navigate_block
    assert "window.location" not in navigate_block
    assert "buildSessionUrl" not in navigate_block

    handlers_start = script.index("function installEventHandlers() {")
    handlers_end = script.index("async function refreshShell", handlers_start)
    handlers_block = script[handlers_start:handlers_end]
    unload_start = handlers_block.index('window.addEventListener("beforeunload", () => {')
    unload_end = handlers_block.index('window.addEventListener("resize", () => {', unload_start)
    unload_block = handlers_block[unload_start:unload_end]
    assert "if (trustedFrontendConfigured) {" in unload_block
    assert "void window.tauFrontendSDK?.disposeAll?.();" in unload_block


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
    assert "@media (max-width: 1079px)" in stylesheet
    assert "@media (max-width: 759px)" in stylesheet
    assert ".shell-layout" in stylesheet
    assert ".mobile-only" in stylesheet
    assert ".extension-slot" in stylesheet
    assert ".tau-extension-view" in stylesheet
    assert ".tau-extension-stack" in stylesheet
    assert ".compose-select-grid" in stylesheet
    assert ".compose-attachment-list" in stylesheet
    assert ".compose-completion-popup" in stylesheet
    assert ".attachment-chip" in stylesheet
    assert ".session-dashboard" in stylesheet
    assert ".dashboard-shell" in stylesheet
    assert ".dashboard-grid" in stylesheet
    assert "grid-template-columns: repeat(4, minmax(0, 1fr));" in stylesheet
    assert "grid-template-columns: repeat(3, minmax(0, 1fr));" in stylesheet
    assert "grid-template-columns: repeat(2, minmax(0, 1fr));" in stylesheet
    assert ".topbar-dashboard-control" in stylesheet
    assert "grid-template-rows: auto auto minmax(0, 1fr) auto;" in stylesheet
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
    assert 'const CACHE_NAME = "tau-web-shell-v10";' in worker
    for asset_path in (
        "/",
        "/index.html",
        "/manifest.webmanifest",
        "/static/app.css",
        "/static/piclaw-reference.css",
        "/static/app.js",
        "/static/live-ui.js",
        "/static/extension-ui.js",
        "/static/widget-bridge.js",
        "/static/frontend-sdk.js",
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


def test_preact_owns_mobile_drawer_state() -> None:
    root = Path(__file__).parents[2] / "src" / "tau_web"
    hook = (root / "frontend/src/hooks/useDrawers.ts").read_text(encoding="utf-8")
    shell = (root / "frontend/src/index.tsx").read_text(encoding="utf-8")
    legacy = (root / "static/app.js").read_text(encoding="utf-8")

    assert "document.body.dataset.navOpen" in hook
    assert 'window.addEventListener("keydown", keydown)' in hook
    assert "const sidebarOpen = drawer !== null" in shell
    assert 'style={{ width: sidebarOpen ? "300px" : "0" }}' in shell
    assert 'className="app-layout__sidebar-wrapper"' in shell
    assert 'addEventListener("click", () => toggleDrawer' not in legacy
    assert 'new CustomEvent("tau:close-drawers")' in legacy


def test_preact_owns_sidebar_tab_state() -> None:
    root = Path(__file__).parents[2] / "src" / "tau_web"
    hook = (root / "frontend/src/hooks/useSidebarTabs.ts").read_text(encoding="utf-8")
    panel = (root / "frontend/src/components/SidePanel.tsx").read_text(encoding="utf-8")
    legacy = (root / "static/app.js").read_text(encoding="utf-8")

    assert 'window.addEventListener("tau:switch-tab", requested)' in hook
    assert 'hidden={activeTab !== "workspace"}' in panel
    assert 'addEventListener("click", () => switchTab' not in legacy
    assert 'new CustomEvent("tau:switch-tab"' in legacy
    assert 'new CustomEvent("tau:open-drawer"' in legacy
    assert "setDrawerState" not in legacy


def test_preact_owns_dashboard_visibility() -> None:
    root = Path(__file__).parents[2] / "src" / "tau_web"
    hook = (root / "frontend/src/hooks/useDashboardVisibility.ts").read_text(encoding="utf-8")
    dashboard = (root / "frontend/src/components/Dashboard.tsx").read_text(encoding="utf-8")
    legacy = (root / "static/app.js").read_text(encoding="utf-8")

    assert 'new CustomEvent("tau:dashboard-visibility"' in hook
    assert 'window.addEventListener("tau:set-dashboard", requested)' in hook
    assert "hidden={!open}" in dashboard
    assert 'dashboardToggle.addEventListener("click"' not in legacy
    assert 'dashboardClose.addEventListener("click"' not in legacy
    assert 'new CustomEvent("tau:set-dashboard"' in legacy
    assert "ui.sessionDashboard.hidden" not in legacy


def test_preact_owns_meter_controls() -> None:
    root = Path(__file__).parents[2] / "src" / "tau_web"
    hook = (root / "frontend/src/hooks/useMeterControls.ts").read_text(encoding="utf-8")
    status = (root / "frontend/src/components/StatusBar.tsx").read_text(encoding="utf-8")
    legacy = (root / "static/app.js").read_text(encoding="utf-8")

    assert 'new CustomEvent("tau:meter-controls"' in hook
    assert "data-enabled={String(metersEnabled)}" in status
    assert "aria-expanded={!metersCollapsed}" in status
    assert 'metersCollapseButton.addEventListener("click"' not in legacy
    assert 'metersVisibilityButton.addEventListener("click"' not in legacy
    assert "ui.systemMeters.dataset.enabled" not in legacy
    assert "function applyMeterControls" in legacy


def test_preact_owns_session_filter_state() -> None:
    root = Path(__file__).parents[2] / "src" / "tau_web"
    hook = (root / "frontend/src/hooks/useSessionFilter.ts").read_text(encoding="utf-8")
    nav = (root / "frontend/src/components/SessionNav.tsx").read_text(encoding="utf-8")
    legacy = (root / "static/app.js").read_text(encoding="utf-8")

    assert 'new CustomEvent("tau:session-filter"' in hook
    assert 'aria-pressed={filter === "active"}' in nav
    assert 'showActiveSessions.addEventListener("click"' not in legacy
    assert "ui.showActiveSessions.setAttribute" not in legacy
    assert 'window.addEventListener("tau:session-filter"' in legacy
