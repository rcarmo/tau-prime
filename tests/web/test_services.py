from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from tau_web.config import WebConfig
from tau_web.services import TauWebServices
from tau_web.sqlite.connection import SqliteDatabase
from tau_web.sqlite.writer import SqliteTransaction


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


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


@pytest.mark.anyio
async def test_services_open_initializes_database_and_components(
    web_config: WebConfig,
) -> None:
    services = await TauWebServices.open(web_config)
    try:
        assert web_config.database_path is not None
        assert services.config is web_config
        assert services.database.opened
        assert services.database.path == web_config.database_path
        assert services.sessions.database is services.database
        assert services.runs.database is services.database
        assert services.queues.database is services.database
        assert services.deliveries.database is services.database
        assert services.audit.database is services.database
        assert services.pool.__class__.__name__ == "AsyncAgentPool"
        assert services.runtime.__class__.__name__ == "DurableAgentRuntime"
        assert services.router.__class__.__name__ == "ChatRouter"
        assert services.closed is False
        assert services.database.recovered_run_count == 0
    finally:
        await services.close()


@pytest.mark.anyio
async def test_services_open_exposes_recovered_run_count(web_config: WebConfig) -> None:
    assert web_config.database_path is not None
    await _seed_running_run(web_config.database_path)

    services = await TauWebServices.open(web_config)
    try:
        recovered = await services.runs.get("run")

        assert services.database.recovered_run_count == 1
        assert recovered is not None
        assert recovered.status == "interrupted"
        assert recovered.ended_at is not None
        assert recovered.error is not None
    finally:
        await services.close()


@pytest.mark.anyio
async def test_services_close_is_idempotent_and_concurrency_safe(
    web_config: WebConfig,
) -> None:
    services = await TauWebServices.open(web_config)

    await services.close()
    await services.close()

    assert services.closed is True
    assert services.database.opened is False

    reopened = await TauWebServices.open(web_config)
    await asyncio.gather(*(reopened.close() for _ in range(8)))

    assert reopened.closed is True
    assert reopened.database.opened is False


@pytest.mark.anyio
async def test_services_close_retries_after_partial_failure(
    monkeypatch: pytest.MonkeyPatch,
    web_config: WebConfig,
) -> None:
    services = await TauWebServices.open(web_config)
    original_shutdown = type(services.runtime).shutdown
    shutdown_calls = 0

    async def flaky_shutdown(runtime: object, *, cancel_timeout: float = 1.0) -> None:
        nonlocal shutdown_calls
        shutdown_calls += 1
        if shutdown_calls == 1:
            raise RuntimeError("runtime cleanup failed")
        await original_shutdown(runtime, cancel_timeout=cancel_timeout)

    monkeypatch.setattr(type(services.runtime), "shutdown", flaky_shutdown)

    with pytest.raises(RuntimeError, match="runtime cleanup failed"):
        await services.close()

    assert shutdown_calls == 1
    assert services.closed is False
    assert services.database.opened is False

    await services.close()

    assert shutdown_calls == 2
    assert services.closed is True
    assert services.database.opened is False


@pytest.mark.anyio
async def test_services_close_releases_database_lock_for_reopen(
    web_config: WebConfig,
) -> None:
    first = await TauWebServices.open(web_config)
    await first.close()

    second = await TauWebServices.open(web_config)
    try:
        assert second.database.opened is True
    finally:
        await second.close()
