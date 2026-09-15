from __future__ import annotations

import asyncio
import re
from dataclasses import replace

import pytest
from aiohttp import ClientConnectionError, web
from aiohttp.test_utils import TestClient, TestServer

from tau_web.app import SERVICES_KEY, create_app
from tau_web.config import WebConfig


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def _start_client(app: web.Application) -> TestClient:
    client = TestClient(TestServer(app))
    await client.start_server()
    return client


def _install_test_post_route(app: web.Application) -> None:
    async def mutate(request: web.Request) -> web.Response:
        payload = await request.read()
        return web.json_response({"ok": True, "size": len(payload)})

    app.router.add_post("/__test__/mutate", mutate)


REQUEST_ID_RE = re.compile(r"[0-9a-f]{32}")


@pytest.mark.anyio
async def test_auth_rejects_missing_bearer_token(web_config: WebConfig) -> None:
    app = create_app(replace(web_config, auth_token="secret-token"))
    _install_test_post_route(app)
    client = await _start_client(app)

    try:
        async with client.post("/__test__/mutate") as response:
            assert response.status == 401
            body = await response.json()
            assert body["error"]["code"] == "unauthorized"
            assert body["error"]["message"] == "Missing or invalid bearer token."
            assert body["error"]["request_id"] == response.headers["X-Request-ID"]
            assert response.headers["WWW-Authenticate"] == "Bearer"
    finally:
        await client.close()


@pytest.mark.anyio
async def test_auth_rejects_bad_bearer_token(web_config: WebConfig) -> None:
    app = create_app(replace(web_config, auth_token="secret-token"))
    _install_test_post_route(app)
    client = await _start_client(app)

    try:
        async with client.post(
            "/__test__/mutate",
            headers={"Authorization": "Bearer wrong-token"},
        ) as response:
            assert response.status == 401
            body = await response.json()
            assert body["error"]["code"] == "unauthorized"
            assert body["error"]["request_id"] == response.headers["X-Request-ID"]
    finally:
        await client.close()


@pytest.mark.anyio
async def test_auth_accepts_good_bearer_token(web_config: WebConfig) -> None:
    app = create_app(replace(web_config, auth_token="secret-token"))
    _install_test_post_route(app)
    client = await _start_client(app)

    try:
        async with client.post(
            "/__test__/mutate",
            data=b"ok",
            headers={"Authorization": "Bearer secret-token"},
        ) as response:
            assert response.status == 200
            assert await response.json() == {"ok": True, "size": 2}
    finally:
        await client.close()


@pytest.mark.anyio
async def test_health_is_exempt_from_auth(web_config: WebConfig) -> None:
    app = create_app(replace(web_config, auth_token="secret-token"))
    client = await _start_client(app)

    try:
        async with client.get("/api/health") as response:
            assert response.status == 200
            assert (await response.json())["status"] == "ok"
    finally:
        await client.close()


@pytest.mark.anyio
async def test_safe_get_ignores_origin_and_csrf(web_config: WebConfig) -> None:
    app = create_app(web_config)
    client = await _start_client(app)

    try:
        async with client.get(
            "/api/health",
            headers={"Origin": "https://app.example.com"},
        ) as response:
            assert response.status == 200
            assert (await response.json())["status"] == "ok"
    finally:
        await client.close()


@pytest.mark.anyio
async def test_frontend_csp_allows_blob_script_src_and_keeps_object_src_none(
    web_config: WebConfig,
) -> None:
    app = create_app(web_config)
    client = await _start_client(app)

    try:
        async with client.get("/") as response:
            assert response.status == 200
            csp = response.headers["Content-Security-Policy"]
    finally:
        await client.close()

    directives = {
        directive.split(" ", 1)[0]: directive
        for directive in csp.split("; ")
    }
    assert directives["script-src"] == "script-src 'self' blob:"
    assert directives["object-src"] == "object-src 'none'"


@pytest.mark.anyio
async def test_same_origin_post_with_csrf_header_is_allowed(web_config: WebConfig) -> None:
    app = create_app(web_config)
    _install_test_post_route(app)
    client = await _start_client(app)

    try:
        origin = str(client.make_url("/")).rstrip("/")
        async with client.post(
            "/__test__/mutate",
            data=b"ok",
            headers={"Origin": origin, "X-Tau-CSRF": "1"},
        ) as response:
            assert response.status == 200
            assert await response.json() == {"ok": True, "size": 2}
    finally:
        await client.close()


@pytest.mark.anyio
async def test_allowed_cross_origin_post_with_csrf_header_is_allowed(
    web_config: WebConfig,
) -> None:
    app = create_app(replace(web_config, allowed_origins=("https://app.example.com",)))
    _install_test_post_route(app)
    client = await _start_client(app)

    try:
        async with client.post(
            "/__test__/mutate",
            data=b"ok",
            headers={"Origin": "https://app.example.com", "X-Tau-CSRF": "1"},
        ) as response:
            assert response.status == 200
            assert await response.json() == {"ok": True, "size": 2}
    finally:
        await client.close()


@pytest.mark.anyio
async def test_post_with_origin_requires_csrf_header(web_config: WebConfig) -> None:
    app = create_app(web_config)
    _install_test_post_route(app)
    client = await _start_client(app)

    try:
        origin = str(client.make_url("/")).rstrip("/")
        async with client.post(
            "/__test__/mutate",
            headers={"Origin": origin},
        ) as response:
            assert response.status == 403
            body = await response.json()
            assert body["error"]["code"] == "forbidden"
            assert body["error"]["message"] == "Missing or invalid CSRF header."
    finally:
        await client.close()


@pytest.mark.anyio
async def test_post_rejects_unlisted_cross_origin(web_config: WebConfig) -> None:
    app = create_app(web_config)
    _install_test_post_route(app)
    client = await _start_client(app)

    try:
        async with client.post(
            "/__test__/mutate",
            headers={"Origin": "https://app.example.com", "X-Tau-CSRF": "1"},
        ) as response:
            assert response.status == 403
            body = await response.json()
            assert body["error"]["code"] == "forbidden"
            assert body["error"]["message"] == "Origin is not allowed."
    finally:
        await client.close()


@pytest.mark.anyio
async def test_post_without_origin_remains_valid_api_client(web_config: WebConfig) -> None:
    app = create_app(web_config)
    _install_test_post_route(app)
    client = await _start_client(app)

    try:
        async with client.post("/__test__/mutate", data=b"ok") as response:
            assert response.status == 200
            assert await response.json() == {"ok": True, "size": 2}
    finally:
        await client.close()


@pytest.mark.anyio
async def test_not_found_errors_are_structured_and_preserve_request_id(
    web_config: WebConfig,
) -> None:
    app = create_app(web_config)
    client = await _start_client(app)

    try:
        async with client.get("/__missing__", headers={"X-Request-ID": "trace-123"}) as response:
            assert response.status == 404
            body = await response.json()
            assert body == {
                "error": {
                    "code": "not_found",
                    "message": "Not Found",
                    "request_id": "trace-123",
                }
            }
            assert response.headers["X-Request-ID"] == "trace-123"
    finally:
        await client.close()


@pytest.mark.anyio
async def test_method_not_allowed_errors_are_structured(web_config: WebConfig) -> None:
    app = create_app(web_config)
    _install_test_post_route(app)
    client = await _start_client(app)

    try:
        async with client.get("/__test__/mutate") as response:
            assert response.status == 405
            body = await response.json()
            assert body["error"]["code"] == "method_not_allowed"
            assert body["error"]["message"] == "Method Not Allowed"
            assert body["error"]["request_id"] == response.headers["X-Request-ID"]
            assert response.headers["Allow"] == "POST"
    finally:
        await client.close()


@pytest.mark.anyio
async def test_request_entity_too_large_errors_are_structured(web_config: WebConfig) -> None:
    app = create_app(replace(web_config, max_request_bytes=8))
    _install_test_post_route(app)
    client = await _start_client(app)

    try:
        async with client.post("/__test__/mutate", data=b"0123456789") as response:
            assert response.status == 413
            body = await response.json()
            assert body["error"]["code"] == "request_entity_too_large"
            assert body["error"]["message"]
            assert body["error"]["request_id"] == response.headers["X-Request-ID"]
    finally:
        await client.close()


@pytest.mark.anyio
async def test_unhandled_errors_are_structured(web_config: WebConfig) -> None:
    app = create_app(web_config)

    async def explode(_: web.Request) -> web.Response:
        raise RuntimeError("boom")

    app.router.add_get("/__test__/explode", explode)
    client = await _start_client(app)

    try:
        async with client.get("/__test__/explode") as response:
            assert response.status == 500
            body = await response.json()
            assert body["error"] == {
                "code": "internal_server_error",
                "message": "Internal Server Error",
                "request_id": response.headers["X-Request-ID"],
            }
    finally:
        await client.close()


@pytest.mark.anyio
async def test_request_ids_are_unique_when_not_supplied(web_config: WebConfig) -> None:
    app = create_app(web_config)
    client = await _start_client(app)

    try:
        async with client.get("/api/health") as first:
            first_request_id = first.headers["X-Request-ID"]
            assert REQUEST_ID_RE.fullmatch(first_request_id) is not None
        async with client.get("/api/health") as second:
            second_request_id = second.headers["X-Request-ID"]
            assert REQUEST_ID_RE.fullmatch(second_request_id) is not None
        assert first_request_id != second_request_id
    finally:
        await client.close()


@pytest.mark.anyio
async def test_cancelled_request_still_allows_cleanup_on_shutdown(web_config: WebConfig) -> None:
    app = create_app(web_config)
    cleaned = asyncio.Event()

    async def cancel_self(_: web.Request) -> web.Response:
        task = asyncio.current_task()
        assert task is not None
        try:
            asyncio.get_running_loop().call_soon(task.cancel)
            await asyncio.sleep(10)
        finally:
            cleaned.set()
        raise AssertionError("unreachable")

    app.router.add_get("/__test__/cancel", cancel_self)
    client = await _start_client(app)

    try:
        with pytest.raises((asyncio.CancelledError, ClientConnectionError)):
            await client.get("/__test__/cancel")
        await asyncio.wait_for(cleaned.wait(), timeout=1)
    finally:
        await client.close()

    assert SERVICES_KEY not in app
