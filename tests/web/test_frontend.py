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


def test_preact_owns_mobile_drawer_state() -> None:
    root = Path(__file__).parents[2] / "src" / "tau_web"
    hook = (root / "frontend/src/hooks/useDrawers.ts").read_text(encoding="utf-8")
    shell = (root / "frontend/src/index.tsx").read_text(encoding="utf-8")
    legacy = (root / "static/app.js").read_text(encoding="utf-8")

    assert "document.body.dataset.navOpen" in hook
    assert 'window.addEventListener("keydown", keydown)' in hook
    assert "const sidebarOpen = drawer !== null" in shell
    assert '<ClassicChatFrame workspaceOpen={sidebarOpen}' in shell
    assert '<ClassicSettingsDialog open={settingsOpen}' in shell
    assert 'className="app-layout__sidebar-wrapper"' not in shell
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


def test_preact_owns_workspace_markup() -> None:
    root = Path(__file__).parents[2] / "src" / "tau_web"
    workspace = (root / "frontend/src/components/WorkspacePanel.tsx").read_text(encoding="utf-8")
    legacy = (root / "static/app.js").read_text(encoding="utf-8")

    assert 'window.addEventListener("tau:workspace-render"' in workspace
    assert 'new CustomEvent("tau:workspace-open"' in workspace
    assert 'new CustomEvent("tau:workspace-render"' in legacy
    assert "ui.workspaceList.replaceChildren" not in legacy
    assert "renderWorkspaceAnnotations" not in legacy


def test_preact_owns_settings_summary_markup() -> None:
    root = Path(__file__).parents[2] / "src" / "tau_web"
    summary = (root / "frontend/src/components/SettingsSummary.tsx").read_text(encoding="utf-8")
    legacy = (root / "static/app.js").read_text(encoding="utf-8")

    assert 'window.addEventListener("tau:settings-render"' in summary
    assert 'new CustomEvent("tau:settings-render"' in legacy
    assert "ui.settingsSummary.replaceChildren" not in legacy


def test_preact_owns_search_result_markup() -> None:
    root = Path(__file__).parents[2] / "src" / "tau_web"
    results = (root / "frontend/src/components/SearchResults.tsx").read_text(encoding="utf-8")
    legacy = (root / "static/app.js").read_text(encoding="utf-8")

    assert 'window.addEventListener("tau:search-render"' in results
    assert 'new CustomEvent("tau:search-open-session"' in results
    assert 'new CustomEvent("tau:search-render"' in legacy
    assert "ui.searchResults.replaceChildren" not in legacy


def test_preact_owns_composer_attachment_markup() -> None:
    root = Path(__file__).parents[2] / "src" / "tau_web"
    composer = (root / "frontend/src/components/Composer.tsx").read_text(encoding="utf-8")
    legacy = (root / "static/app.js").read_text(encoding="utf-8")

    assert 'window.addEventListener("tau:attachments-render"' in composer
    assert 'new CustomEvent("tau:attachment-remove"' in composer
    assert 'new CustomEvent("tau:attachments-render"' in legacy
    assert 'window.addEventListener("tau:attachment-remove"' in legacy
    assert "composeAttachmentList.replaceChildren" not in legacy


def test_preact_owns_composer_completion_markup() -> None:
    root = Path(__file__).parents[2] / "src" / "tau_web"
    composer = (root / "frontend/src/components/Composer.tsx").read_text(encoding="utf-8")
    legacy = (root / "static/app.js").read_text(encoding="utf-8")

    assert 'window.addEventListener("tau:completion-render"' in composer
    assert 'new CustomEvent("tau:completion-select"' in composer
    assert 'new CustomEvent("tau:completion-render"' in legacy
    assert 'window.addEventListener("tau:completion-select"' in legacy
    assert "composeCompletionListbox.replaceChildren" not in legacy
    assert 'document.createElement("li")' not in legacy[legacy.index("function renderComposerCompletion"):legacy.index("function renderComposerAttachments")]


def test_preact_owns_meter_controls() -> None:
    root = Path(__file__).parents[2] / "src" / "tau_web"
    hook = (root / "frontend/src/hooks/useMeterControls.ts").read_text(encoding="utf-8")
    stats = (root / "frontend/src/components/SystemStats.tsx").read_text(encoding="utf-8")
    legacy = (root / "static/app.js").read_text(encoding="utf-8")

    assert 'new CustomEvent("tau:meter-controls"' in hook
    assert 'window.addEventListener("tau:meters-render"' in stats
    assert "data-enabled={String(state.enabled)}" in stats
    assert "aria-expanded={!state.collapsed}" in stats
    assert 'metersCollapseButton.addEventListener("click"' not in legacy
    assert 'metersVisibilityButton.addEventListener("click"' not in legacy
    assert "ui.systemMeters.dataset.enabled" not in legacy
    assert 'new CustomEvent("tau:meters-render"' in legacy
    assert "document.createElementNS" not in legacy
    assert "function applyMeterControls" in legacy


def test_preact_owns_session_filter_state() -> None:
    root = Path(__file__).parents[2] / "src" / "tau_web"
    hook = (root / "frontend/src/hooks/useSessionFilter.ts").read_text(encoding="utf-8")
    nav = (root / "frontend/src/components/SessionList.tsx").read_text(encoding="utf-8")
    legacy = (root / "static/app.js").read_text(encoding="utf-8")

    assert 'new CustomEvent("tau:session-filter"' in hook
    assert 'aria-pressed={filter === "active"}' in nav
    assert 'window.addEventListener("tau:sessions-render"' in nav
    assert 'new CustomEvent("tau:session-select"' in nav
    assert 'showActiveSessions.addEventListener("click"' not in legacy
    assert "ui.showActiveSessions.setAttribute" not in legacy
    assert 'window.addEventListener("tau:session-filter"' in legacy
    assert 'new CustomEvent("tau:sessions-render"' in legacy
    assert "ui.sessionList.replaceChildren" not in legacy
