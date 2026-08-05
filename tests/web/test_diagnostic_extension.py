from __future__ import annotations

from dataclasses import replace
from typing import cast

import pytest
from aiohttp.test_utils import TestClient, TestServer

from tau_extensions import ExtensionServices
from tau_extensions.builtin.diagnostic import (
    ASSET_PATH,
    DIAGNOSTIC_EXTENSION_ID,
    EVENT_NAME,
    GLOBAL_STATE_KEY,
    ROUTE_PATH,
    VIEW_ID,
    create_extension,
)
from tau_web.app import SERVICES_KEY, create_app
from tau_web.config import WebConfig
from tau_web.extensions import ExtensionDirectory, SqliteExtensionStorageBackend
from tau_web.services import TauWebServices
from tau_web.sqlite.connection import SqliteReader
from tau_web.sqlite.repositories import ExtensionStateRepository

_PERMISSIONS = [
    "storage",
    "background_tasks",
    "assets",
    "commands",
    "tools",
    "routes",
    "events",
    "views",
    "actions",
]


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def _start_client(config: WebConfig) -> TestClient:
    client = TestClient(TestServer(create_app(config)))
    await client.start_server()
    return client


def _services(client: TestClient) -> TauWebServices:
    return cast(TauWebServices, client.app[SERVICES_KEY])


async def _read_global_state_row(
    services: TauWebServices,
) -> tuple[str, int, int, str, int, int, str] | None:
    async def read(reader: SqliteReader) -> tuple[str, int, int, str, int, int, str] | None:
        row = await reader.fetch_one(
            """
            SELECT
                value_json,
                revision,
                json_valid(value_json) AS is_valid,
                json_extract(value_json, '$.extension_id') AS extracted_extension_id,
                json_extract(value_json, '$.started') AS extracted_started,
                json_extract(value_json, '$.storage_revision') AS extracted_storage_revision,
                json_extract(value_json, '$.view_id') AS extracted_view_id
            FROM extension_state
            WHERE extension_id = ?
              AND scope = ?
              AND scope_id = ?
              AND key = ?
              AND json_valid(value_json) = 1
            """,
            (DIAGNOSTIC_EXTENSION_ID, "global", "global", GLOBAL_STATE_KEY),
        )
        if row is None:
            return None
        return (
            str(row["value_json"]),
            int(row["revision"]),
            int(row["is_valid"]),
            str(row["extracted_extension_id"]),
            int(row["extracted_started"]),
            int(row["extracted_storage_revision"]),
            str(row["extracted_view_id"]),
        )

    return await services.database.read(read)


@pytest.mark.anyio
async def test_builtin_diagnostic_extension_uses_sqlite_storage_and_web_adapters(
    web_config: WebConfig,
) -> None:
    client = await _start_client(replace(web_config, auth_token="secret-token"))
    diagnostic = None
    try:
        services = _services(client)
        assert isinstance(services.extensions, ExtensionDirectory)
        assert isinstance(services.extension_state, ExtensionStateRepository)
        assert isinstance(services.extension_storage, SqliteExtensionStorageBackend)
        assert services.extension_storage.repository is services.extension_state

        extension_services = ExtensionServices(
            DIAGNOSTIC_EXTENSION_ID,
            _PERMISSIONS,
            services.extension_storage,
        )
        diagnostic = create_extension(extension_services)

        await diagnostic.start()
        services.extensions.register(extension_services)

        assert services.extensions.extension_ids == (DIAGNOSTIC_EXTENSION_ID,)
        assert services.extensions.get(DIAGNOSTIC_EXTENSION_ID) is extension_services
        assert await _read_global_state_row(services) == (
            '{"asset_path":"diagnostic/state.json","event_count":1,"extension_id":"tau.diagnostic","route_path":"/status","session_revision":1,"started":true,"storage_revision":2,"view_id":"diagnostic-view","workspace_revision":1}',
            2,
            1,
            DIAGNOSTIC_EXTENSION_ID,
            1,
            2,
            VIEW_ID,
        )

        asset_response = await client.get(
            f"/api/extensions/assets/{DIAGNOSTIC_EXTENSION_ID}/{ASSET_PATH}",
            headers={"Authorization": "Bearer secret-token"},
        )
        assert asset_response.status == 200
        assert await asset_response.json() == {
            "asset_path": ASSET_PATH,
            "extension_id": DIAGNOSTIC_EXTENSION_ID,
            "view_id": VIEW_ID,
        }
        assert asset_response.headers["Content-Type"] == "application/json"

        await diagnostic.services.events.publish(EVENT_NAME, {"kind": "web", "sequence": 2})

        route_response = await client.get(
            f"/api/extensions/routes/{DIAGNOSTIC_EXTENSION_ID}{ROUTE_PATH}",
            headers={"Authorization": "Bearer secret-token"},
        )
        assert route_response.status == 200
        assert await route_response.json() == {
            "event_count": 2,
            "extension_id": DIAGNOSTIC_EXTENSION_ID,
            "method": "GET",
            "path": ROUTE_PATH,
            "started": True,
            "storage_revision": 2,
        }

        await diagnostic.dispose()

        missing_asset = await client.get(
            f"/api/extensions/assets/{DIAGNOSTIC_EXTENSION_ID}/{ASSET_PATH}",
            headers={"Authorization": "Bearer secret-token"},
        )
        assert missing_asset.status == 404

        missing_route = await client.get(
            f"/api/extensions/routes/{DIAGNOSTIC_EXTENSION_ID}{ROUTE_PATH}",
            headers={"Authorization": "Bearer secret-token"},
        )
        assert missing_route.status == 404

        removed = await services.extensions.unregister(DIAGNOSTIC_EXTENSION_ID)
        assert removed is extension_services
        assert services.extensions.extension_ids == ()
    finally:
        if diagnostic is not None and not diagnostic.disposed:
            await diagnostic.dispose()
        await client.close()
