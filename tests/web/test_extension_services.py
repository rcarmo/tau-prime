from __future__ import annotations

import asyncio
from dataclasses import replace
from typing import cast

import pytest
from aiohttp.test_utils import TestClient, TestServer

from tau_extensions import (
    ExtensionServices,
    RevisionConflictError,
    RouteRequest,
    RouteResponse,
    RouteSpec,
)
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
) -> ExtensionServices:
    extension = ExtensionServices(extension_id, permissions, _services(client).extension_storage)
    _services(client).extensions.register(extension)
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
