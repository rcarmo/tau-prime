from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

import pytest

import tau_extensions.services as services_module
from tau_agent.types import JSONObject, JSONValue
from tau_extensions import (
    GLOBAL_SCOPE_ID,
    MAX_ASSET_BYTES,
    MAX_EXTENSION_ASSET_BYTES,
    MAX_STORAGE_VALUE_BYTES,
    CommandSpec,
    ExtensionServices,
    PermissionDeniedError,
    RegistryError,
    RevisionConflictError,
    RouteRequest,
    RouteResponse,
    RouteSpec,
    StorageScope,
    StoredValue,
    ToolSpec,
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@dataclass(frozen=True, slots=True)
class StorageCall:
    operation: Literal["get", "list", "save", "delete"]
    extension_id: str
    scope: StorageScope
    scope_id: str
    key: str | None = None
    expected_revision: int | None = None


class FakeStorageBackend:
    def __init__(self) -> None:
        self.records: dict[tuple[str, StorageScope, str, str], StoredValue] = {}
        self.calls: list[StorageCall] = []

    async def get(
        self,
        extension_id: str,
        *,
        scope: StorageScope,
        scope_id: str,
        key: str,
    ) -> StoredValue | None:
        self.calls.append(StorageCall("get", extension_id, scope, scope_id, key))
        return self.records.get((extension_id, scope, scope_id, key))

    async def list(
        self,
        extension_id: str,
        *,
        scope: StorageScope,
        scope_id: str,
    ) -> Mapping[str, StoredValue]:
        self.calls.append(StorageCall("list", extension_id, scope, scope_id))
        return {
            key: value
            for (
                stored_extension_id,
                stored_scope,
                stored_scope_id,
                key,
            ), value in self.records.items()
            if stored_extension_id == extension_id
            and stored_scope == scope
            and stored_scope_id == scope_id
        }

    async def save(
        self,
        extension_id: str,
        *,
        scope: StorageScope,
        scope_id: str,
        key: str,
        value: JSONValue,
        expected_revision: int | None,
    ) -> StoredValue:
        self.calls.append(
            StorageCall("save", extension_id, scope, scope_id, key, expected_revision)
        )
        identity = (extension_id, scope, scope_id, key)
        existing = self.records.get(identity)
        if expected_revision == 0:
            if existing is not None:
                raise RevisionConflictError(
                    self._format_identity(identity),
                    expected=expected_revision,
                    actual=existing.revision,
                )
        elif expected_revision is not None:
            actual = existing.revision if existing is not None else None
            if actual != expected_revision:
                raise RevisionConflictError(
                    self._format_identity(identity),
                    expected=expected_revision,
                    actual=actual,
                )
        revision = 1 if existing is None else existing.revision + 1
        stored = StoredValue(value=value, revision=revision)
        self.records[identity] = stored
        return stored

    async def delete(
        self,
        extension_id: str,
        *,
        scope: StorageScope,
        scope_id: str,
        key: str,
        expected_revision: int,
    ) -> StoredValue | None:
        self.calls.append(
            StorageCall("delete", extension_id, scope, scope_id, key, expected_revision)
        )
        identity = (extension_id, scope, scope_id, key)
        existing = self.records.get(identity)
        if existing is None:
            return None
        if existing.revision != expected_revision:
            raise RevisionConflictError(
                self._format_identity(identity),
                expected=expected_revision,
                actual=existing.revision,
            )
        self.records.pop(identity)
        return existing

    def _format_identity(self, identity: tuple[str, StorageScope, str, str]) -> str:
        extension_id, scope, scope_id, key = identity
        return f"{extension_id}:{scope}:{scope_id}:{key}"


PermissionExercise = Callable[[ExtensionServices], Awaitable[None]]


async def _use_storage(services: ExtensionServices) -> None:
    await services.storage.global_().get("state")


async def _use_tasks(services: ExtensionServices) -> None:
    services.tasks.spawn(asyncio.sleep(0), "worker")


async def _use_assets(services: ExtensionServices) -> None:
    services.assets.register("asset.txt", b"x", mime_type="text/plain")


async def _use_commands(services: ExtensionServices) -> None:
    services.commands.register(CommandSpec("demo", "Demo", lambda: None))


async def _use_tools(services: ExtensionServices) -> None:
    services.tools.register(
        ToolSpec(
            "demo_tool",
            "Demo tool",
            {"type": "object"},
            lambda arguments: arguments,
        )
    )


async def _use_routes(services: ExtensionServices) -> None:
    services.routes.register(RouteSpec("GET", "/demo", lambda request: request))


async def _use_events(services: ExtensionServices) -> None:
    services.events.subscribe("tick", lambda: None)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("permission", "exercise"),
    [
        ("storage", _use_storage),
        ("background_tasks", _use_tasks),
        ("assets", _use_assets),
        ("commands", _use_commands),
        ("tools", _use_tools),
        ("routes", _use_routes),
        ("events", _use_events),
    ],
)
async def test_extension_services_enforce_permissions(
    permission: str,
    exercise: PermissionExercise,
) -> None:
    services = ExtensionServices("com.example.demo", [], FakeStorageBackend())

    with pytest.raises(PermissionDeniedError, match=permission):
        await exercise(services)


@pytest.mark.anyio
async def test_storage_scopes_validate_identities_revisions_and_json_size(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = FakeStorageBackend()
    services = ExtensionServices("com.example.demo", ["storage"], backend)

    payload: JSONObject = {"count": 1}
    created = await services.storage.global_().save("state", payload, expected_revision=0)
    payload["count"] = 2
    fetched = await services.storage.global_().get("state")

    assert created.value == {"count": 1}
    assert created.revision == 1
    assert fetched == created
    assert fetched is not created

    updated = await services.storage.global_().save(
        "state",
        {"count": 3},
        expected_revision=created.revision,
    )
    workspace_record = await services.storage.workspace("workspace-1").save(
        "draft",
        {"status": "open"},
        expected_revision=0,
    )
    session_record = await services.storage.session("session-1").save(
        "draft",
        {"status": "active"},
        expected_revision=0,
    )
    listed = await services.storage.global_().list()

    assert updated.revision == 2
    assert workspace_record.revision == 1
    assert session_record.revision == 1
    assert listed == {"state": updated}

    with pytest.raises(RevisionConflictError, match="expected 1"):
        await services.storage.global_().save("state", {"count": 4}, expected_revision=1)
    with pytest.raises(RevisionConflictError, match="actual 2"):
        await services.storage.global_().delete("state", expected_revision=1)

    deleted = await services.storage.global_().delete("state", expected_revision=updated.revision)

    assert deleted == updated
    assert await services.storage.global_().get("state") is None
    assert backend.calls == [
        StorageCall("save", "com.example.demo", "global", GLOBAL_SCOPE_ID, "state", 0),
        StorageCall("get", "com.example.demo", "global", GLOBAL_SCOPE_ID, "state"),
        StorageCall("save", "com.example.demo", "global", GLOBAL_SCOPE_ID, "state", 1),
        StorageCall(
            "save",
            "com.example.demo",
            "workspace",
            "workspace-1",
            "draft",
            0,
        ),
        StorageCall("save", "com.example.demo", "session", "session-1", "draft", 0),
        StorageCall("list", "com.example.demo", "global", GLOBAL_SCOPE_ID),
        StorageCall("save", "com.example.demo", "global", GLOBAL_SCOPE_ID, "state", 1),
        StorageCall("delete", "com.example.demo", "global", GLOBAL_SCOPE_ID, "state", 1),
        StorageCall("delete", "com.example.demo", "global", GLOBAL_SCOPE_ID, "state", 2),
        StorageCall("get", "com.example.demo", "global", GLOBAL_SCOPE_ID, "state"),
    ]

    await services.storage.global_().save("state", {"count": 5}, expected_revision=0)

    monkeypatch.setattr(services_module, "MAX_STORAGE_VALUE_BYTES", 12)
    with pytest.raises(RegistryError, match="value must be at most 12 bytes"):
        await services.storage.global_().save("large", {"value": "1234567890"}, expected_revision=0)
    with pytest.raises(RegistryError, match="value must be at most 12 bytes"):
        StoredValue(value={"value": "1234567890"}, revision=1)


@pytest.mark.anyio
async def test_owned_tasks_track_success_failures_cancellation_and_dispose() -> None:
    services = ExtensionServices(
        "com.example.demo",
        ["background_tasks"],
        FakeStorageBackend(),
    )
    release_success = asyncio.Event()
    success_started = asyncio.Event()

    async def succeed() -> str:
        success_started.set()
        await release_success.wait()
        return "done"

    success_task = services.tasks.spawn(succeed(), "success")
    await success_started.wait()
    assert services.tasks.task_count == 1

    release_success.set()
    assert await success_task == "done"
    await asyncio.sleep(0)
    assert services.tasks.task_count == 0
    assert services.diagnostics == ()

    async def fail() -> None:
        raise RuntimeError("task boom")

    failed_task = services.tasks.spawn(fail(), "failure")
    with pytest.raises(RuntimeError, match="task boom"):
        await failed_task
    await asyncio.sleep(0)

    assert services.tasks.task_count == 0
    assert len(services.diagnostics) == 1
    assert services.diagnostics[0].phase == "task:failure"
    assert services.diagnostics[0].message == "RuntimeError: task boom"

    cancel_started = asyncio.Event()
    block_cancel = asyncio.Event()

    async def cancel_me() -> None:
        cancel_started.set()
        await block_cancel.wait()

    cancel_task = services.tasks.spawn(cancel_me(), "cancel")
    await cancel_started.wait()
    await services.tasks.cancel_all()

    assert cancel_task.cancelled() is True
    assert services.tasks.task_count == 0
    assert len(services.diagnostics) == 1

    dispose_started = asyncio.Event()
    block_dispose = asyncio.Event()

    async def dispose_me() -> None:
        dispose_started.set()
        await block_dispose.wait()

    dispose_task = services.tasks.spawn(dispose_me(), "dispose")
    await dispose_started.wait()
    await services.tasks.dispose()

    assert dispose_task.cancelled() is True
    assert services.tasks.task_count == 0
    assert len(services.diagnostics) == 1


def test_asset_registry_validates_paths_mime_size_quota_and_disposal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(services_module, "MAX_ASSET_BYTES", 4)
    monkeypatch.setattr(services_module, "MAX_EXTENSION_ASSET_BYTES", 6)
    services = ExtensionServices("com.example.demo", ["assets"], FakeStorageBackend())

    first_handle = services.assets.register(
        "images/icon.svg",
        b"abcd",
        mime_type="IMAGE/SVG+XML",
    )
    first = services.assets.lookup("images/icon.svg")
    second_handle = services.assets.register("docs/readme.txt", b"xy", mime_type="text/plain")

    assert first is not None
    assert first.path == "images/icon.svg"
    assert first.mime_type == "image/svg+xml"
    assert first.size == 4
    assert services.assets.total_bytes == 6
    assert services.assets.items() == (
        services.assets.lookup("docs/readme.txt"),
        first,
    )

    with pytest.raises(RegistryError, match="duplicate asset path"):
        services.assets.register("images/icon.svg", b"z", mime_type="text/plain")
    with pytest.raises(RegistryError, match="path must be a safe relative path"):
        services.assets.register("/absolute.txt", b"x", mime_type="text/plain")
    with pytest.raises(RegistryError, match="path must be a safe relative path"):
        services.assets.register("../escape.txt", b"x", mime_type="text/plain")
    with pytest.raises(RegistryError, match="path must be a safe relative path"):
        services.assets.register("bad path.txt", b"x", mime_type="text/plain")
    with pytest.raises(RegistryError, match="mime_type"):
        services.assets.register("bad.bin", b"x", mime_type="binary/octet-stream")
    with pytest.raises(RegistryError, match="asset content must be at most 4 bytes"):
        services.assets.register("large.bin", b"12345", mime_type="application/octet-stream")
    with pytest.raises(RegistryError, match="extension assets must total at most 6 bytes"):
        services.assets.register("overflow.txt", b"z", mime_type="text/plain")

    second_handle.dispose()
    assert services.assets.lookup("docs/readme.txt") is None
    assert services.assets.total_bytes == 4

    first_handle.dispose()
    assert services.assets.items() == ()
    assert services.assets.total_bytes == 0


def test_command_tool_and_route_registries_validate_specs_duplicates_and_disposal() -> None:
    services = ExtensionServices(
        "com.example.demo",
        ["commands", "tools", "routes"],
        FakeStorageBackend(),
    )

    with pytest.raises(RegistryError, match="name"):
        CommandSpec("bad name", "Demo", lambda: None)
    with pytest.raises(RegistryError, match="title must not be blank"):
        CommandSpec("demo", "   ", lambda: None)
    with pytest.raises(RegistryError, match="description must not be blank"):
        ToolSpec("demo_tool", "", {"type": "object"}, lambda arguments: arguments)
    with pytest.raises(RegistryError, match="input_schema must be a JSON object"):
        ToolSpec(
            "demo_tool",
            "Demo tool",
            cast(JSONObject, 3),
            lambda arguments: arguments,
        )
    with pytest.raises(RegistryError, match="method must be a supported HTTP verb"):
        RouteSpec("TRACE", "/demo", lambda: None)
    with pytest.raises(RegistryError, match="path must start with '/'"):
        RouteSpec("GET", "demo", lambda: None)

    command_handle = services.commands.register(CommandSpec("demo", "Demo", lambda: None))
    tool_handle = services.tools.register(
        ToolSpec(
            "demo_tool",
            "Demo tool",
            {"type": "object"},
            lambda arguments: arguments,
        )
    )
    route_handle = services.routes.register(RouteSpec("get", "/demo", lambda request: request))

    assert services.commands.get("demo") is not None
    assert services.tools.get("demo_tool") is not None
    assert services.routes.get("GET", "/demo") is not None
    assert services.routes.items()[0].method == "GET"

    with pytest.raises(RegistryError, match="duplicate command name"):
        services.commands.register(CommandSpec("demo", "Again", lambda: None))
    with pytest.raises(RegistryError, match="duplicate tool name"):
        services.tools.register(
            ToolSpec(
                "demo_tool",
                "Again",
                {"type": "object"},
                lambda arguments: arguments,
            )
        )
    with pytest.raises(RegistryError, match="duplicate route GET /demo"):
        services.routes.register(RouteSpec("GET", "/demo", lambda: None))

    command_handle.dispose()
    tool_handle.dispose()
    route_handle.dispose()

    assert services.commands.items() == ()
    assert services.tools.items() == ()
    assert services.routes.items() == ()


@pytest.mark.anyio
async def test_event_bus_runs_sync_and_async_listeners_deterministically() -> None:
    services = ExtensionServices("com.example.demo", ["events"], FakeStorageBackend())
    seen: list[str] = []

    def sync_listener(value: int) -> None:
        seen.append(f"sync:{value}")

    def broken_listener(value: int) -> None:
        seen.append(f"broken:{value}")
        raise RuntimeError("listener boom")

    async def async_listener(value: int) -> None:
        await asyncio.sleep(0)
        seen.append(f"async:{value}")

    first_handle = services.events.subscribe("tick", sync_listener)
    broken_handle = services.events.subscribe("tick", broken_listener)
    async_handle = services.events.subscribe("tick", async_listener)

    assert services.events.count() == 3
    assert services.events.count("tick") == 3

    await services.events.publish("tick", 7)

    assert seen == ["sync:7", "broken:7", "async:7"]
    assert len(services.diagnostics) == 1
    assert services.diagnostics[0].phase == "event:tick"
    assert services.diagnostics[0].message == "RuntimeError: listener boom"

    broken_handle.dispose()
    first_handle.dispose()
    assert services.events.count("tick") == 1

    await services.events.publish("tick", 8)
    async_handle.dispose()

    assert seen == ["sync:7", "broken:7", "async:7", "async:8"]
    assert services.events.count() == 0


@pytest.mark.anyio
async def test_extension_services_dispose_cleans_owned_resources() -> None:
    services = ExtensionServices(
        "com.example.demo",
        ["background_tasks", "assets", "commands", "tools", "routes", "events"],
        FakeStorageBackend(),
    )
    task_started = asyncio.Event()
    task_release = asyncio.Event()

    async def background() -> None:
        task_started.set()
        await task_release.wait()

    task = services.tasks.spawn(background(), "worker")
    await task_started.wait()
    services.assets.register("asset.txt", b"x", mime_type="text/plain")
    services.commands.register(CommandSpec("demo", "Demo", lambda: None))
    services.tools.register(
        ToolSpec(
            "demo_tool",
            "Demo tool",
            {"type": "object"},
            lambda arguments: arguments,
        )
    )
    services.routes.register(RouteSpec("GET", "/demo", lambda: None))
    services.events.subscribe("tick", lambda: None)

    await services.dispose()
    await services.dispose()

    assert services.disposed is True
    assert task.cancelled() is True
    assert services.tasks.task_count == 0
    assert services.assets.total_bytes == 0
    assert services.assets.items() == ()
    assert services.commands.items() == ()
    assert services.tools.items() == ()
    assert services.routes.items() == ()
    assert services.events.count() == 0


def test_route_request_and_response_validate_json_headers_and_status() -> None:
    request = RouteRequest(
        "post",
        "/demo/path",
        query={"page": "1"},
        headers={"Accept": "application/json", "X-Trace": "abc"},
        body={"value": [1, True, None]},
    )
    response = RouteResponse(
        201,
        body={"ok": True},
        headers={"Content-Type": "application/json", "X-Trace": "abc"},
    )

    assert request.method == "POST"
    assert request.path == "/demo/path"
    assert request.query == {"page": "1"}
    assert request.headers == {"Accept": "application/json", "X-Trace": "abc"}
    assert request.body == {"value": [1, True, None]}
    assert response.status == 201
    assert response.body == {"ok": True}
    assert response.headers["Content-Type"] == "application/json"

    with pytest.raises(RegistryError, match="status must be between 200 and 599"):
        RouteResponse(199)
    with pytest.raises(RegistryError, match=r"headers\['X-Bad'\] must not contain CR, LF, or NUL"):
        RouteResponse(200, headers={"X-Bad": "ok\r\nboom"})
    with pytest.raises(RegistryError, match="headers keys must not contain CR, LF, or NUL"):
        RouteRequest("GET", "/demo", headers={"Bad\r\nName": "x"})


def test_service_modules_do_not_import_tau_web_or_sqlite() -> None:
    source_path = Path(services_module.__file__).resolve()
    source = source_path.read_text(encoding="utf-8")

    assert "tau_web" not in source
    assert "sqlite" not in source
    assert MAX_STORAGE_VALUE_BYTES > 0
    assert MAX_ASSET_BYTES > 0
    assert MAX_EXTENSION_ASSET_BYTES >= MAX_ASSET_BYTES
