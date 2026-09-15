from __future__ import annotations

import asyncio
import base64
import hashlib
from dataclasses import replace
from typing import cast

import pytest
from aiohttp.test_utils import TestClient, TestServer

from tau_extensions import (
    AnnotationProviderSpec,
    EditorAnnotation,
    ExtensionServices,
    ExtensionSource,
    FileRendererSpec,
    RevisionConflictError,
    RouteRequest,
    RouteResponse,
    RouteSpec,
    TrustedFrontendModuleSpec,
    WidgetSpec,
)
from tau_extensions.web import StandardView, Text
from tau_web.app import SERVICES_KEY, create_app
from tau_web.config import WebConfig
from tau_web.routes import extensions as extension_routes_module
from tau_web.services import TauWebServices
from tau_web.sqlite.connection import SqliteReader


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def _start_client(config: WebConfig) -> TestClient:
    client = TestClient(TestServer(create_app(config)))
    await client.start_server()
    return client


def _services(client: TestClient) -> TauWebServices:
    return cast(TauWebServices, client.app[SERVICES_KEY])


async def _register_extension(
    client: TestClient,
    extension_id: str,
    permissions: list[str],
    *,
    source: ExtensionSource = ExtensionSource.BUILT_IN,
) -> ExtensionServices:
    extension = ExtensionServices(extension_id, permissions, _services(client).extension_storage)
    _services(client).extensions.register(extension, source=source)
    return extension


async def _read_state_json(
    services: TauWebServices, extension_id: str, key: str
) -> tuple[str, int] | None:
    async def inspect(reader: SqliteReader) -> tuple[str, int] | None:
        row = await reader.fetch_one(
            """
            SELECT value_json, revision FROM extension_state
            WHERE extension_id = ? AND scope = ? AND scope_id = ? AND key = ?
            """,
            (extension_id, "global", "global", key),
        )
        if row is None:
            return None
        return str(row["value_json"]), int(row["revision"])

    return await services.database.read(inspect)


def _sri_sha256(content: bytes) -> str:
    return f"sha256-{base64.b64encode(hashlib.sha256(content).digest()).decode('ascii')}"


@pytest.mark.anyio
async def test_sqlite_extension_storage_backend_roundtrips_revisions_and_json_persistence(
    web_config: WebConfig,
) -> None:
    services = await TauWebServices.open(web_config)
    try:
        extension = ExtensionServices(
            "com.example.sqlite",
            ["storage"],
            services.extension_storage,
        )

        created = await extension.storage.global_().save(
            "state",
            {"b": 2, "a": 1},
            expected_revision=0,
        )
        updated = await extension.storage.global_().save(
            "state",
            {"nested": {"value": True}},
            expected_revision=created.revision,
        )

        assert services.extension_storage.repository is services.extension_state
        assert created.revision == 1
        assert updated.revision == 2
        assert await extension.storage.global_().get("state") == updated
        assert await extension.storage.global_().list() == {"state": updated}
        assert await _read_state_json(services, "com.example.sqlite", "state") == (
            '{"nested":{"value":true}}',
            2,
        )

        with pytest.raises(RevisionConflictError, match="expected 1"):
            await extension.storage.global_().save("state", {"stale": True}, expected_revision=1)

        deleted = await extension.storage.global_().delete(
            "state", expected_revision=updated.revision
        )

        assert deleted == updated
        assert await extension.storage.global_().get("state") is None
        assert (
            await extension.storage.global_().delete("state", expected_revision=updated.revision)
            is None
        )
    finally:
        await services.close()


@pytest.mark.anyio
async def test_extension_asset_routes_require_auth_and_serve_exact_mime(
    web_config: WebConfig,
) -> None:
    client = await _start_client(replace(web_config, auth_token="secret-token"))
    try:
        extension = await _register_extension(client, "com.example.assets", ["assets"])
        extension.assets.register(
            "bundle/app.js",
            b"console.log('tau')",
            mime_type="application/javascript",
        )

        unauthorized = await client.get("/api/extensions/assets/com.example.assets/bundle/app.js")
        assert unauthorized.status == 401

        asset = await client.get(
            "/api/extensions/assets/com.example.assets/bundle/app.js",
            headers={"Authorization": "Bearer secret-token"},
        )
        assert asset.status == 200
        assert await asset.read() == b"console.log('tau')"
        assert asset.headers["Content-Type"] == "application/javascript"
        assert asset.headers["Cache-Control"] == "public, max-age=31536000, immutable"
        assert asset.headers["X-Content-Type-Options"] == "nosniff"

        missing = await client.get(
            "/api/extensions/assets/com.example.assets/missing.js",
            headers={"Authorization": "Bearer secret-token"},
        )
        assert missing.status == 404

        traversal = await client.get(
            "/api/extensions/assets/com.example.assets/%2E%2E/secret.txt",
            headers={"Authorization": "Bearer secret-token"},
        )
        assert traversal.status == 404
    finally:
        await client.close()


@pytest.mark.anyio
async def test_frontend_modules_route_requires_auth_and_lists_deterministically(
    monkeypatch: pytest.MonkeyPatch,
    web_config: WebConfig,
) -> None:
    client = await _start_client(replace(web_config, auth_token="secret-token"))
    headers = {"Authorization": "Bearer secret-token"}
    try:
        alpha = await _register_extension(
            client,
            "com.example.alpha",
            ["assets", "trusted_frontend"],
            source=ExtensionSource.BUILT_IN,
        )
        beta = await _register_extension(
            client,
            "com.example.beta",
            ["assets", "trusted_frontend"],
            source=ExtensionSource.ADMIN,
        )
        workspace = await _register_extension(
            client,
            "com.example.workspace",
            ["assets", "trusted_frontend"],
            source=ExtensionSource.WORKSPACE,
        )

        alpha_primary = b"console.log('alpha-primary');"
        alpha_secondary = b"console.log('alpha-secondary');"
        beta_main = b"console.log('beta-main');"
        workspace_main = b"console.log('workspace-main');"

        alpha.assets.register(
            "trusted/zeta.js", alpha_secondary, mime_type="application/javascript"
        )
        alpha.assets.register("trusted/alpha.js", alpha_primary, mime_type="application/javascript")
        beta.assets.register("trusted/main.js", beta_main, mime_type="application/javascript")
        workspace.assets.register(
            "trusted/workspace.js",
            workspace_main,
            mime_type="application/javascript",
        )

        alpha.trusted_frontend.register(
            TrustedFrontendModuleSpec(
                "zeta",
                "trusted/zeta.js",
                _sri_sha256(alpha_secondary),
            )
        )
        alpha.trusted_frontend.register(
            TrustedFrontendModuleSpec(
                "alpha",
                "trusted/alpha.js",
                _sri_sha256(alpha_primary),
            )
        )
        beta.trusted_frontend.register(
            TrustedFrontendModuleSpec("main", "trusted/main.js", _sri_sha256(beta_main))
        )
        workspace.trusted_frontend.register(
            TrustedFrontendModuleSpec(
                "workspace",
                "trusted/workspace.js",
                _sri_sha256(workspace_main),
            )
        )

        unauthorized = await client.get("/api/extensions/frontend-modules")
        assert unauthorized.status == 401

        response = await client.get("/api/extensions/frontend-modules", headers=headers)
        assert response.status == 200
        assert response.headers["Cache-Control"] == "no-store"

        payload = await response.json()
        expected_modules = [
            {
                "extension_id": "com.example.alpha",
                "module_id": "alpha",
                "sdk_version": "1.0",
                "integrity": _sri_sha256(alpha_primary),
                "asset_url": "/api/extensions/assets/com.example.alpha/trusted/alpha.js",
            },
            {
                "extension_id": "com.example.alpha",
                "module_id": "zeta",
                "sdk_version": "1.0",
                "integrity": _sri_sha256(alpha_secondary),
                "asset_url": "/api/extensions/assets/com.example.alpha/trusted/zeta.js",
            },
            {
                "extension_id": "com.example.beta",
                "module_id": "main",
                "sdk_version": "1.0",
                "integrity": _sri_sha256(beta_main),
                "asset_url": "/api/extensions/assets/com.example.beta/trusted/main.js",
            },
        ]
        assert payload == {"modules": expected_modules}
        assert all(
            set(descriptor)
            == {
                "extension_id",
                "module_id",
                "sdk_version",
                "integrity",
                "asset_url",
            }
            for descriptor in payload["modules"]
        )
        assert all(
            descriptor["extension_id"] != "com.example.workspace"
            for descriptor in payload["modules"]
        )

        monkeypatch.setattr(extension_routes_module, "_MAX_FRONTEND_MODULES", 2)
        bounded = await client.get("/api/extensions/frontend-modules", headers=headers)
        assert bounded.status == 200
        assert await bounded.json() == {"modules": expected_modules[:2]}

        monkeypatch.setattr(extension_routes_module, "_MAX_FRONTEND_MODULES", 0)
        empty = await client.get("/api/extensions/frontend-modules", headers=headers)
        assert empty.status == 200
        assert await empty.json() == {"modules": []}
    finally:
        await client.close()


def test_frontend_modules_route_precedes_parameter_routes(web_config: WebConfig) -> None:
    app = create_app(web_config)
    canonicals = [resource.canonical for resource in app.router.resources()]

    frontend_modules_index = canonicals.index("/api/extensions/frontend-modules")
    assert frontend_modules_index < canonicals.index("/api/extensions/assets/{extension_id}/{path}")
    assert frontend_modules_index < canonicals.index("/api/extensions/routes/{extension_id}")
    assert frontend_modules_index < canonicals.index("/api/extensions/routes/{extension_id}/{path}")


@pytest.mark.anyio
async def test_extension_routes_require_auth_and_forward_selected_request_data(
    web_config: WebConfig,
) -> None:
    client = await _start_client(replace(web_config, auth_token="secret-token"))
    try:
        extension = await _register_extension(client, "com.example.routes", ["routes"])

        def echo(request: RouteRequest) -> RouteResponse:
            return RouteResponse(
                200,
                body={
                    "method": request.method,
                    "path": request.path,
                    "query": dict(request.query),
                    "headers": dict(request.headers),
                    "body": request.body,
                },
            )

        extension.routes.register(RouteSpec("POST", "/echo", echo))

        unauthorized = await client.post(
            "/api/extensions/routes/com.example.routes/echo",
            json={"ok": True},
        )
        assert unauthorized.status == 401

        response = await client.post(
            "/api/extensions/routes/com.example.routes/echo?mode=fast",
            json={"ok": True},
            headers={
                "Authorization": "Bearer secret-token",
                "Accept": "application/json",
                "Cookie": "secret=1",
                "X-Request-ID": "trace-123",
                "X-Unsafe": "hidden",
            },
        )
        assert response.status == 200
        payload = await response.json()

        assert payload["method"] == "POST"
        assert payload["path"] == "/echo"
        assert payload["query"] == {"mode": "fast"}
        assert payload["body"] == {"ok": True}
        assert payload["headers"]["accept"] == "application/json"
        assert payload["headers"]["content-type"] == "application/json"
        assert payload["headers"]["x-request-id"] == "trace-123"
        assert "authorization" not in payload["headers"]
        assert "cookie" not in payload["headers"]
        assert "x-unsafe" not in payload["headers"]

        missing = await client.get(
            "/api/extensions/routes/com.example.routes/missing",
            headers={"Authorization": "Bearer secret-token"},
        )
        assert missing.status == 404
    finally:
        await client.close()


@pytest.mark.anyio
async def test_extension_route_errors_timeouts_and_body_bounds(
    monkeypatch: pytest.MonkeyPatch,
    web_config: WebConfig,
) -> None:
    client = await _start_client(web_config)
    try:
        extension = await _register_extension(client, "com.example.failures", ["routes"])

        def boom(request: RouteRequest) -> RouteResponse:
            del request
            raise RuntimeError("boom")

        async def timeout(request: RouteRequest) -> RouteResponse:
            del request
            await asyncio.sleep(0.05)
            return RouteResponse(200, body={"ok": True})

        def wrong_type(request: RouteRequest) -> object:
            del request
            return {"ok": True}

        def forbidden_header(request: RouteRequest) -> RouteResponse:
            del request
            return RouteResponse(200, body="ok", headers={"Set-Cookie": "session=1"})

        def too_large_response(request: RouteRequest) -> RouteResponse:
            del request
            return RouteResponse(
                200,
                body="x" * (extension_routes_module._MAX_EXTENSION_ROUTE_BODY_BYTES + 1),
            )

        def echo(request: RouteRequest) -> RouteResponse:
            return RouteResponse(200, body={"body": request.body})

        extension.routes.register(RouteSpec("GET", "/boom", boom))
        extension.routes.register(RouteSpec("GET", "/timeout", timeout))
        extension.routes.register(RouteSpec("GET", "/wrong", wrong_type))
        extension.routes.register(RouteSpec("GET", "/forbidden-header", forbidden_header))
        extension.routes.register(RouteSpec("GET", "/too-large-response", too_large_response))
        extension.routes.register(RouteSpec("POST", "/echo", echo))

        monkeypatch.setattr(extension_routes_module, "_MAX_EXTENSION_ROUTE_TIMEOUT_SECONDS", 0.01)

        boom_response = await client.get("/api/extensions/routes/com.example.failures/boom")
        assert boom_response.status == 500
        assert (await boom_response.json())["error"]["code"] == "extension_route_error"

        timeout_response = await client.get("/api/extensions/routes/com.example.failures/timeout")
        assert timeout_response.status == 504
        assert (await timeout_response.json())["error"]["code"] == "extension_route_timeout"

        wrong_response = await client.get("/api/extensions/routes/com.example.failures/wrong")
        assert wrong_response.status == 502
        assert (await wrong_response.json())["error"]["code"] == "invalid_extension_response"

        forbidden_header_response = await client.get(
            "/api/extensions/routes/com.example.failures/forbidden-header"
        )
        assert forbidden_header_response.status == 502
        assert (await forbidden_header_response.json())["error"]["code"] == (
            "invalid_extension_response"
        )

        too_large_response_result = await client.get(
            "/api/extensions/routes/com.example.failures/too-large-response"
        )
        assert too_large_response_result.status == 502
        too_large_error = await too_large_response_result.json()
        assert too_large_error["error"]["code"] == "invalid_extension_response"
        assert "1048576 bytes" in too_large_error["error"]["message"]

        non_json = await client.post(
            "/api/extensions/routes/com.example.failures/echo",
            data=b"hello",
            headers={"Content-Type": "text/plain"},
        )
        assert non_json.status == 415
        assert (await non_json.json())["error"]["message"] == (
            "Extension routes accept only JSON request bodies."
        )

        oversized = await client.post(
            "/api/extensions/routes/com.example.failures/echo",
            json={"payload": "x" * extension_routes_module._MAX_EXTENSION_ROUTE_BODY_BYTES},
        )
        assert oversized.status == 413
        assert (await oversized.json())["error"]["code"] == "request_entity_too_large"
    finally:
        await client.close()


@pytest.mark.anyio
async def test_file_routes_include_declarative_renderer_and_annotations(
    web_config: WebConfig,
) -> None:
    source = web_config.cwd / "extended.md"
    source.write_text("# Extended\n", encoding="utf-8")
    client = await _start_client(web_config)
    try:
        extension = await _register_extension(client, "com.example.preview", ["views"])
        view = StandardView(
            id="file-preview",
            title="File preview",
            placement="sidebar",
            components=(Text("Rendered safely"),),
        )
        extension.file_renderers.register(
            FileRendererSpec(
                "markdown",
                lambda context: view,
                filename_patterns=("*.md",),
            )
        )
        extension.annotation_providers.register(
            AnnotationProviderSpec(
                "heading",
                lambda context: (
                    EditorAnnotation(1, "Heading", severity="info", source="preview"),
                ),
                media_types=("text/markdown",),
            )
        )

        response = await client.get("/api/files", params={"path": "extended.md"})
        assert response.status == 200
        payload = await response.json()
        assert payload["renderer"] == {
            "type": "view",
            "extension_id": "com.example.preview",
            "renderer_id": "markdown",
            "view": {
                "kind": "card",
                "id": "file-preview",
                "title": "File preview",
                "placement": "sidebar",
                "components": [
                    {
                        "kind": "text",
                        "text": "Rendered safely",
                        "style": "normal",
                        "live": False,
                    }
                ],
            },
        }
        assert payload["annotations"] == [
            {
                "line": 1,
                "message": "Heading",
                "severity": "info",
                "source": "preview",
                "extension_id": "com.example.preview",
                "provider_id": "heading",
            }
        ]
    finally:
        await client.close()


@pytest.mark.anyio
async def test_widget_document_and_action_are_authenticated_bounded_and_sandbox_ready(
    monkeypatch: pytest.MonkeyPatch,
    web_config: WebConfig,
) -> None:
    client = await _start_client(replace(web_config, auth_token="secret-token"))
    headers = {"Authorization": "Bearer secret-token"}
    try:
        extension = await _register_extension(
            client,
            "com.example.widgets",
            ["assets", "sandboxed_widgets"],
        )
        extension.assets.register(
            "preview.js",
            b"document.getElementById('tau-widget-root').textContent = 'ready';",
            mime_type="application/javascript",
        )
        extension.assets.register(
            "preview.css",
            b"body { color: white; }",
            mime_type="text/css",
        )
        extension.widgets.register(
            WidgetSpec(
                "preview",
                "Preview <safe>",
                "preview.js",
                style_path="preview.css",
                actions={"echo": lambda payload: {"echo": payload}},
            )
        )

        unauthorized = await client.get("/api/extensions/widgets/com.example.widgets/preview")
        assert unauthorized.status == 401

        document = await client.get(
            "/api/extensions/widgets/com.example.widgets/preview",
            headers=headers,
        )
        assert document.status == 200
        text = await document.text()
        assert "Preview &lt;safe&gt;" in text
        assert "/static/widget-bridge.js" in text
        assert "tau-widget-root" in text
        assert "ready" in text
        assert document.headers["Cache-Control"] == "no-store"
        assert "default-src 'none'" in document.headers["Content-Security-Policy"]
        assert "connect-src 'none'" in document.headers["Content-Security-Policy"]
        assert "X-Frame-Options" not in document.headers

        action = await client.post(
            "/api/extensions/widgets/com.example.widgets/preview/actions/echo",
            json={"payload": {"value": 3}},
            headers={**headers, "X-Tau-CSRF": "1"},
        )
        assert action.status == 200
        assert await action.json() == {"echo": {"value": 3}}

        malformed = await client.post(
            "/api/extensions/widgets/com.example.widgets/preview/actions/echo",
            json={"payload": [], "extra": True},
            headers={**headers, "X-Tau-CSRF": "1"},
        )
        assert malformed.status == 400

        missing = await client.post(
            "/api/extensions/widgets/com.example.widgets/preview/actions/missing",
            json={"payload": {}},
            headers={**headers, "X-Tau-CSRF": "1"},
        )
        assert missing.status == 404

        monkeypatch.setattr(extension_routes_module, "_MAX_WIDGET_ACTION_RESULT_BYTES", 4)
        too_large = await client.post(
            "/api/extensions/widgets/com.example.widgets/preview/actions/echo",
            json={"payload": {"value": 3}},
            headers={**headers, "X-Tau-CSRF": "1"},
        )
        assert too_large.status == 502
        assert (await too_large.json())["error"]["code"] == ("widget_action_result_too_large")
    finally:
        await client.close()
