from __future__ import annotations

import importlib
import json
import sys
from collections.abc import Callable, Mapping
from typing import cast

import pytest

from tau_extensions import (
    GLOBAL_SCOPE_ID,
    Candidate,
    ExtensionDefinition,
    ExtensionHost,
    ExtensionServices,
    ExtensionSource,
    JSONValue,
    RouteRequest,
    StoredValue,
    TrustPolicy,
    discover_extensions,
    resolve_extensions,
)
from tau_extensions.builtin import extension_roots
from tau_extensions.web import (
    ActionRequest,
    ActionResult,
    Invalidation,
    PropertyPatch,
    view_to_json,
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class FakeStorageBackend:
    def __init__(self) -> None:
        self.records: dict[tuple[str, str, str, str], StoredValue] = {}
        self.calls: list[tuple[str, str, str, str, str]] = []

    async def get(
        self,
        extension_id: str,
        *,
        scope: str,
        scope_id: str,
        key: str,
    ) -> StoredValue | None:
        self.calls.append(("get", extension_id, scope, scope_id, key))
        return self.records.get((extension_id, scope, scope_id, key))

    async def list(
        self,
        extension_id: str,
        *,
        scope: str,
        scope_id: str,
    ) -> Mapping[str, StoredValue]:
        self.calls.append(("list", extension_id, scope, scope_id, ""))
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
        scope: str,
        scope_id: str,
        key: str,
        value: JSONValue,
        expected_revision: int | None,
    ) -> StoredValue:
        self.calls.append(("save", extension_id, scope, scope_id, key))
        identity = (extension_id, scope, scope_id, key)
        existing = self.records.get(identity)
        if expected_revision == 0 and existing is not None:
            raise ValueError("expected create-only save")
        if expected_revision not in (None, 0):
            actual = existing.revision if existing is not None else None
            if actual != expected_revision:
                raise ValueError(
                    "revision conflict for "
                    f"{identity!r}: expected {expected_revision!r}, actual {actual!r}"
                )
        revision = 1 if existing is None else existing.revision + 1
        stored = StoredValue(value=value, revision=revision)
        self.records[identity] = stored
        return stored

    async def delete(
        self,
        extension_id: str,
        *,
        scope: str,
        scope_id: str,
        key: str,
        expected_revision: int,
    ) -> StoredValue | None:
        self.calls.append(("delete", extension_id, scope, scope_id, key))
        identity = (extension_id, scope, scope_id, key)
        existing = self.records.get(identity)
        if existing is None:
            return None
        if existing.revision != expected_revision:
            raise ValueError(
                "revision conflict for "
                f"{identity!r}: expected {expected_revision!r}, actual {existing.revision!r}"
            )
        self.records.pop(identity)
        return existing


def _builtin_diagnostic_candidate() -> Candidate:
    result = discover_extensions({ExtensionSource.BUILT_IN: extension_roots()})
    assert result.diagnostics == ()
    return next(
        candidate for candidate in result.candidates if candidate.manifest.id == "tau.diagnostic"
    )


def _load_entrypoint(candidate: Candidate) -> Callable[[ExtensionServices], object]:
    module_name, attribute_name = candidate.manifest.entrypoint.split(":", 1)
    attribute = getattr(importlib.import_module(module_name), attribute_name)
    assert callable(attribute)
    return cast(Callable[[ExtensionServices], object], attribute)


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


def test_builtin_diagnostic_discovery_is_import_free_and_matches_manifest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delitem(sys.modules, "tau_extensions.builtin.diagnostic", raising=False)
    monkeypatch.delitem(sys.modules, "tau_extensions.builtin.diagnostic.extension", raising=False)

    candidate = _builtin_diagnostic_candidate()

    assert candidate.path == (extension_roots()[0] / "diagnostic").resolve()
    assert candidate.manifest.entrypoint == "tau_extensions.builtin.diagnostic:create_extension"
    assert candidate.manifest.permissions == frozenset(_PERMISSIONS)
    assert candidate.manifest.contributions == {
        "views": [{"id": "diagnostic-view"}],
        "actions": [{"id": "refresh-status"}],
        "commands": [{"name": "diagnostic.command"}],
        "tools": [{"name": "diagnostic.tool"}],
        "routes": [{"method": "GET", "path": "/status"}],
        "assets": [{"path": "diagnostic/state.json"}],
        "events": [{"name": "diagnostic.ping"}],
    }
    assert "tau_extensions.builtin.diagnostic" not in sys.modules
    assert "tau_extensions.builtin.diagnostic.extension" not in sys.modules


def test_builtin_diagnostic_resolution_entrypoint_load_and_host_contributions() -> None:
    candidate = _builtin_diagnostic_candidate()
    plan = resolve_extensions([candidate], enabled_ids=(), approvals=(), policy=TrustPolicy())

    assert [resolved.manifest.id for resolved in plan.ordered_candidates] == ["tau.diagnostic"]
    assert {decision.candidate.manifest.id: decision.code for decision in plan.decisions} == {
        "tau.diagnostic": "builtin_default_enabled"
    }
    assert plan.diagnostics == ()

    from tau_extensions.builtin.diagnostic import (
        ACTION_ID,
        ASSET_PATH,
        COMMAND_NAME,
        DIAGNOSTIC_EXTENSION_ID,
        EVENT_NAME,
        ROUTE_PATH,
        TOOL_NAME,
        VIEW_ID,
        DiagnosticExtension,
    )

    instances: dict[str, DiagnosticExtension] = {}

    def loader(resolved_candidate: Candidate) -> ExtensionDefinition:
        factory = _load_entrypoint(resolved_candidate)
        services = ExtensionServices(
            resolved_candidate.manifest.id,
            sorted(resolved_candidate.manifest.permissions),
            FakeStorageBackend(),
        )
        instance = cast(DiagnosticExtension, factory(services))
        instances[resolved_candidate.manifest.id] = instance
        return instance.definition

    host = ExtensionHost(plan, loader)
    host.activate_all()

    extension = instances[DIAGNOSTIC_EXTENSION_ID]

    assert host.statuses[DIAGNOSTIC_EXTENSION_ID] == "active"
    assert host.active_extension_ids == (DIAGNOSTIC_EXTENSION_ID,)
    assert extension.host_events == ["activate"]
    assert host.contribution_registry.values("views") == (extension.view,)
    assert host.contribution_registry.values("actions") == (extension.action_definition,)
    assert host.contribution_registry.values("commands") == (extension.command_spec,)
    assert host.contribution_registry.values("tools") == (extension.tool_spec,)
    assert host.contribution_registry.values("routes") == (extension.route_spec,)
    assert host.contribution_registry.values("assets") == (
        {"mime_type": "application/json", "path": ASSET_PATH},
    )
    assert host.contribution_registry.values("events") == ({"name": EVENT_NAME},)
    assert host.contribution_registry.contributions("views")[0].key == VIEW_ID
    assert host.contribution_registry.contributions("actions")[0].key == ACTION_ID
    assert host.contribution_registry.contributions("commands")[0].key == COMMAND_NAME
    assert host.contribution_registry.contributions("tools")[0].key == TOOL_NAME
    assert host.contribution_registry.contributions("routes")[0].key == "route-status"
    assert host.contribution_registry.contributions("assets")[0].key == "asset-state"
    assert host.contribution_registry.contributions("events")[0].key == "event-ping"
    assert host.contribution_registry.contributions("routes")[0].value.path == ROUTE_PATH

    host.deactivate_all()

    assert extension.host_events == ["activate", "deactivate"]
    assert host.active_extension_ids == ()
    assert host.contribution_registry.values("views") == ()
    assert host.contribution_registry.values("actions") == ()
    assert host.contribution_registry.values("commands") == ()
    assert host.contribution_registry.values("tools") == ()
    assert host.contribution_registry.values("routes") == ()
    assert host.contribution_registry.values("assets") == ()
    assert host.contribution_registry.values("events") == ()


@pytest.mark.anyio
async def test_builtin_diagnostic_start_exercises_storage_tasks_and_runtime_services() -> None:
    from tau_extensions.builtin.diagnostic import (
        ASSET_PATH,
        COMMAND_NAME,
        DIAGNOSTIC_EXTENSION_ID,
        EVENT_NAME,
        GLOBAL_STATE_KEY,
        ROUTE_PATH,
        SESSION_SCOPE_ID,
        SESSION_STATE_KEY,
        TOOL_NAME,
        VIEW_ID,
        WORKSPACE_SCOPE_ID,
        WORKSPACE_STATE_KEY,
        create_extension,
    )

    backend = FakeStorageBackend()
    services = ExtensionServices(DIAGNOSTIC_EXTENSION_ID, _PERMISSIONS, backend)
    extension = create_extension(services)

    await extension.start()
    try:
        asset = services.assets.lookup(ASSET_PATH)
        command = services.commands.get(COMMAND_NAME)
        tool = services.tools.get(TOOL_NAME)
        route = services.routes.get("GET", ROUTE_PATH)

        assert extension.started is True
        assert extension.state_revision == 2
        assert extension.workspace_revision == 1
        assert extension.session_revision == 1
        assert services.tasks.task_count == 1
        assert services.events.count(EVENT_NAME) == 1
        assert asset is not None
        assert json.loads(asset.content.decode("utf-8")) == {
            "asset_path": ASSET_PATH,
            "extension_id": DIAGNOSTIC_EXTENSION_ID,
            "view_id": VIEW_ID,
        }
        assert command is not None
        assert command.handler() == extension.snapshot()
        assert tool is not None
        assert tool.handler({"echo": "hello"}) == {
            "arguments": {"echo": "hello"},
            "snapshot": extension.snapshot(),
        }
        assert route is not None
        request = RouteRequest("GET", ROUTE_PATH)
        assert route.handler(request) == extension.route_spec.handler(request)
        assert extension.service_events == [
            {
                "extension_id": DIAGNOSTIC_EXTENSION_ID,
                "kind": "started",
                "view_id": VIEW_ID,
            }
        ]

        await services.events.publish(EVENT_NAME, {"kind": "manual", "sequence": 2})

        assert extension.service_events[-1] == {"kind": "manual", "sequence": 2}
        assert services.routes.get("GET", ROUTE_PATH) is not None
        assert await services.storage.global_().get(GLOBAL_STATE_KEY) == StoredValue(
            value={
                "asset_path": ASSET_PATH,
                "event_count": 1,
                "extension_id": DIAGNOSTIC_EXTENSION_ID,
                "route_path": ROUTE_PATH,
                "session_revision": 1,
                "started": True,
                "storage_revision": 2,
                "view_id": VIEW_ID,
                "workspace_revision": 1,
            },
            revision=2,
        )
        assert await services.storage.workspace(WORKSPACE_SCOPE_ID).get(WORKSPACE_STATE_KEY) == (
            StoredValue(value={"scope": "workspace", "started": True}, revision=1)
        )
        assert await services.storage.session(SESSION_SCOPE_ID).get(SESSION_STATE_KEY) == (
            StoredValue(value={"scope": "session", "started": True}, revision=1)
        )
        assert backend.records[
            (DIAGNOSTIC_EXTENSION_ID, "global", GLOBAL_SCOPE_ID, GLOBAL_STATE_KEY)
        ] == StoredValue(
            value={
                "asset_path": ASSET_PATH,
                "event_count": 1,
                "extension_id": DIAGNOSTIC_EXTENSION_ID,
                "route_path": ROUTE_PATH,
                "session_revision": 1,
                "started": True,
                "storage_revision": 2,
                "view_id": VIEW_ID,
                "workspace_revision": 1,
            },
            revision=2,
        )
        assert backend.calls[:6] == [
            ("get", DIAGNOSTIC_EXTENSION_ID, "global", GLOBAL_SCOPE_ID, GLOBAL_STATE_KEY),
            ("save", DIAGNOSTIC_EXTENSION_ID, "global", GLOBAL_SCOPE_ID, GLOBAL_STATE_KEY),
            (
                "get",
                DIAGNOSTIC_EXTENSION_ID,
                "workspace",
                WORKSPACE_SCOPE_ID,
                WORKSPACE_STATE_KEY,
            ),
            (
                "save",
                DIAGNOSTIC_EXTENSION_ID,
                "workspace",
                WORKSPACE_SCOPE_ID,
                WORKSPACE_STATE_KEY,
            ),
            (
                "get",
                DIAGNOSTIC_EXTENSION_ID,
                "session",
                SESSION_SCOPE_ID,
                SESSION_STATE_KEY,
            ),
            (
                "save",
                DIAGNOSTIC_EXTENSION_ID,
                "session",
                SESSION_SCOPE_ID,
                SESSION_STATE_KEY,
            ),
        ]
    finally:
        await extension.dispose()

    assert extension.disposed is True
    assert services.disposed is True


@pytest.mark.anyio
async def test_builtin_diagnostic_view_action_patches_invalidations_and_stop_disposes() -> None:
    from tau_extensions.builtin.diagnostic import (
        ACTION_ID,
        COMMAND_NAME,
        DIAGNOSTIC_EXTENSION_ID,
        EVENT_NAME,
        ROUTE_PATH,
        TOOL_NAME,
        VIEW_ID,
        create_extension,
    )

    services = ExtensionServices(DIAGNOSTIC_EXTENSION_ID, _PERMISSIONS, FakeStorageBackend())
    extension = create_extension(services)

    await extension.start()
    try:
        view_json = view_to_json(extension.view)
        components = cast(list[object], view_json["components"])

        assert view_json["id"] == VIEW_ID
        assert components[0] == {
            "kind": "text",
            "text": "diagnostic-ready",
            "style": "muted",
            "live": True,
        }

        result = await extension.action_executor.execute(
            ActionRequest(
                request_id="req-1",
                extension_id=DIAGNOSTIC_EXTENSION_ID,
                action_id=ACTION_ID,
                view_id=VIEW_ID,
                payload={"source": "test"},
            )
        )

        assert result == ActionResult(
            data={
                "event_count": 1,
                "extension_id": DIAGNOSTIC_EXTENSION_ID,
                "payload": {"source": "test"},
                "started": True,
            },
            invalidations=(Invalidation(target="view", key=VIEW_ID),),
            patches=(
                PropertyPatch(
                    view_id=VIEW_ID,
                    path="/components/0/text",
                    value="diagnostic-ready",
                    sequence=1,
                ),
            ),
        )

        await extension.stop()

        assert extension.started is False
        assert services.tasks.task_count == 0
        assert services.assets.items() == ()
        assert services.commands.items() == ()
        assert services.tools.items() == ()
        assert services.routes.items() == ()
        assert services.events.count() == 0
        assert extension.action_registry.get(DIAGNOSTIC_EXTENSION_ID, ACTION_ID) is None
        assert services.commands.get(COMMAND_NAME) is None
        assert services.tools.get(TOOL_NAME) is None
        assert services.routes.get("GET", ROUTE_PATH) is None
        assert services.events.count(EVENT_NAME) == 0
    finally:
        await extension.dispose()

    assert extension.disposed is True
    assert services.disposed is True
