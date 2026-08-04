from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Never, cast

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from tau_web import services as services_module
from tau_web.app import CONFIG_KEY, SERVICES_KEY, create_app
from tau_web.config import WebConfig
from tau_web.services import TauWebServices
from tau_web.sqlite.connection import SqliteDatabase
from tau_web.sqlite.writer import SqliteTransaction


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _loaded_module(prefix: str) -> bool:
    return any(name == prefix or name.startswith(f"{prefix}.") for name in sys.modules)


async def _seed_running_run(database_path: Path) -> None:
    async with SqliteDatabase(database_path) as database:

        async def seed(transaction: SqliteTransaction) -> None:
            await transaction.execute(
                """
                INSERT INTO workspaces(workspace_id, root_path, created_at, updated_at)
                VALUES ('workspace', ?, 'now', 'now')
                """,
                (str(database_path.parent),),
            )
            await transaction.execute(
                """
                INSERT INTO sessions(
                    session_id, workspace_id, agent_name, provider_name, model,
                    created_at, updated_at
                ) VALUES ('session', 'workspace', 'default', 'test', 'model', 'now', 'now')
                """
            )
            await transaction.execute(
                """
                INSERT INTO session_runs(
                    run_id, session_id, status, started_at, updated_at
                ) VALUES ('run', 'session', 'running', 'now', 'now')
                """
            )

        await database.write(seed)


def test_app_module_import_is_lazy_and_does_not_load_optional_clients() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import tau_web.app; "
                "print('aiohttp' in sys.modules, 'pi_client' in sys.modules, "
                "'acp_client' in sys.modules)"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "False False False"


def test_create_app_defers_database_startup(web_config: WebConfig) -> None:
    assert web_config.database_path is not None
    assert not web_config.database_path.exists()

    app = create_app(web_config)

    assert app[CONFIG_KEY] is web_config
    assert app._client_max_size == web_config.max_request_bytes
    assert SERVICES_KEY not in app
    assert not web_config.database_path.exists()


@pytest.mark.anyio
async def test_health_reports_started_services(web_config: WebConfig) -> None:
    assert web_config.database_path is not None
    await _seed_running_run(web_config.database_path)
    app = create_app(web_config)
    client = TestClient(TestServer(app))

    await client.start_server()
    try:
        async with client.get("/api/health") as response:
            assert response.status == 200
            assert await response.json() == {
                "status": "ok",
                "service": "tau-web",
                "database": "ready",
                "recovered_runs": 1,
            }
        assert SERVICES_KEY in app
        assert _loaded_module("pi_client") is False
        assert _loaded_module("acp_client") is False
    finally:
        await client.close()


@pytest.mark.anyio
async def test_app_runner_manages_service_lifecycle(web_config: WebConfig) -> None:
    app = create_app(web_config)
    runner = web.AppRunner(app)

    await runner.setup()
    services = cast(TauWebServices, app[SERVICES_KEY])
    assert app[CONFIG_KEY] is web_config
    assert services.database.opened is True
    assert services.closed is False

    await runner.cleanup()

    assert services.closed is True
    assert services.database.opened is False
    assert SERVICES_KEY not in app

    reopened = await TauWebServices.open(web_config)
    try:
        assert reopened.database.opened is True
    finally:
        await reopened.close()


@pytest.mark.anyio
async def test_runner_cleanup_clears_services_state_when_close_raises(
    monkeypatch: pytest.MonkeyPatch,
    web_config: WebConfig,
) -> None:
    app = create_app(web_config)
    runner = web.AppRunner(app)

    await runner.setup()
    services = cast(TauWebServices, app[SERVICES_KEY])
    original_close = TauWebServices.close
    close_calls = 0

    async def close_then_raise(service: TauWebServices) -> None:
        nonlocal close_calls
        close_calls += 1
        await original_close(service)
        raise RuntimeError("cleanup boom")

    with monkeypatch.context() as patch:
        patch.setattr(TauWebServices, "close", close_then_raise)
        with pytest.raises(RuntimeError, match="cleanup boom"):
            await runner.cleanup()

    assert close_calls == 1
    assert services.closed is True
    assert services.database.opened is False
    assert SERVICES_KEY not in app

    reopened = await TauWebServices.open(web_config)
    try:
        assert reopened.database.opened is True
    finally:
        await reopened.close()


@pytest.mark.anyio
async def test_startup_failure_does_not_leak_services_or_lock(
    monkeypatch: pytest.MonkeyPatch,
    web_config: WebConfig,
) -> None:
    def fail_router(*_: object, **__: object) -> Never:
        raise RuntimeError("boom")

    with monkeypatch.context() as patch:
        patch.setattr(services_module, "ChatRouter", fail_router)
        app = create_app(web_config)
        runner = web.AppRunner(app)

        with pytest.raises(RuntimeError, match="boom"):
            await runner.setup()

    assert SERVICES_KEY not in app

    reopened = await TauWebServices.open(web_config)
    try:
        assert reopened.database.opened is True
    finally:
        await reopened.close()
