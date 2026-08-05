"""Built-in diagnostic extension implemented against Tau's public contracts."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Sequence

from tau_extensions import (
    AnnotationProviderSpec,
    CommandSpec,
    DisposalHandle,
    EditorAnnotation,
    ExtensionDefinition,
    ExtensionRegistrar,
    ExtensionServices,
    FileRenderContext,
    FileRendererSpec,
    JSONObject,
    JSONValue,
    RouteRequest,
    RouteResponse,
    RouteSpec,
    ToolSpec,
    WidgetReference,
    WidgetSpec,
)
from tau_extensions.web import (
    ActionContext,
    ActionDefinition,
    ActionExecutor,
    ActionRegistry,
    ActionResult,
    Button,
    Field,
    FieldOption,
    Invalidation,
    Metric,
    Progress,
    PropertyPatch,
    Stack,
    StandardView,
    Table,
    TableColumn,
    Text,
)

DIAGNOSTIC_EXTENSION_ID = "tau.diagnostic"
VIEW_ID = "diagnostic-view"
ACTION_ID = "refresh-status"
COMMAND_NAME = "diagnostic.command"
TOOL_NAME = "diagnostic.tool"
ROUTE_PATH = "/status"
ASSET_PATH = "diagnostic/state.json"
WIDGET_SCRIPT_PATH = "diagnostic/widget.js"
FILE_RENDERER_ID = "diagnostic-file"
ANNOTATION_PROVIDER_ID = "diagnostic-annotations"
WIDGET_ID = "diagnostic-widget"
EVENT_NAME = "diagnostic.ping"
GLOBAL_STATE_KEY = "state"
WORKSPACE_SCOPE_ID = "diagnostic-workspace"
WORKSPACE_STATE_KEY = "workspace-state"
SESSION_SCOPE_ID = "diagnostic-session"
SESSION_STATE_KEY = "session-state"
_ROUTE_CONTRIBUTION_KEY = "route-status"
_ASSET_CONTRIBUTION_KEY = "asset-state"
_EVENT_CONTRIBUTION_KEY = "event-ping"
_BACKGROUND_TASK_NAME = "diagnostic-worker"


class DiagnosticExtension:
    """Harmless built-in extension that exercises Tau's portable extension APIs."""

    def __init__(self, services: ExtensionServices) -> None:
        self.services = services
        self.view = _build_view()
        self.action_registry = ActionRegistry()
        self.action_executor = ActionExecutor(self.action_registry)
        self.action_definition = ActionDefinition(id=ACTION_ID, handler=self._execute_action)
        self.command_spec = CommandSpec(COMMAND_NAME, "Run built-in diagnostics", self._run_command)
        self.tool_spec = ToolSpec(
            TOOL_NAME,
            "Return the diagnostic extension snapshot.",
            {
                "type": "object",
                "properties": {
                    "echo": {"type": "string"},
                },
                "additionalProperties": False,
            },
            self._run_tool,
        )
        self.route_spec = RouteSpec("GET", ROUTE_PATH, self._route_response)
        self.file_renderer_spec = FileRendererSpec(
            FILE_RENDERER_ID,
            self._render_file,
            filename_patterns=("*.tau-diagnostic.json", "*.tau-diagnostic.txt"),
        )
        self.annotation_provider_spec = AnnotationProviderSpec(
            ANNOTATION_PROVIDER_ID,
            self._annotate_file,
            filename_patterns=("*.tau-diagnostic.json", "*.tau-diagnostic.txt"),
        )
        self.widget_spec = WidgetSpec(
            WIDGET_ID,
            "Diagnostic widget",
            WIDGET_SCRIPT_PATH,
            actions={"snapshot": self._widget_snapshot},
        )
        self.asset_content = _json_bytes(
            {
                "asset_path": ASSET_PATH,
                "extension_id": self.services.extension_id,
                "view_id": self.view.id,
            }
        )
        self.widget_script = _widget_script_bytes()
        self.definition = ExtensionDefinition(setup=self._setup)
        self.host_events: list[str] = []
        self.service_events: list[JSONObject] = []
        self.started = False
        self.disposed = False
        self.state_revision: int | None = None
        self.workspace_revision: int | None = None
        self.session_revision: int | None = None
        self._state: JSONObject = self._snapshot()
        self._started_handles: list[DisposalHandle] = []
        self._background_release: asyncio.Event | None = None
        self._background_started: asyncio.Event | None = None
        self._background_task: asyncio.Task[None] | None = None

    def snapshot(self) -> JSONObject:
        """Return the latest in-memory diagnostic snapshot."""
        return dict(self._state)

    async def start(self) -> None:
        """Start the diagnostic extension and exercise all portable services."""
        if self.disposed:
            raise RuntimeError("DiagnosticExtension is disposed")
        if self.started:
            return

        handles: list[DisposalHandle] = []
        try:
            handles.append(
                self.action_registry.register(self.services.extension_id, self.action_definition)
            )
            handles.append(
                self.services.assets.register(
                    ASSET_PATH,
                    self.asset_content,
                    mime_type="application/json",
                )
            )
            handles.append(
                self.services.assets.register(
                    WIDGET_SCRIPT_PATH,
                    self.widget_script,
                    mime_type="application/javascript",
                )
            )
            handles.append(self.services.file_renderers.register(self.file_renderer_spec))
            handles.append(
                self.services.annotation_providers.register(self.annotation_provider_spec)
            )
            handles.append(self.services.widgets.register(self.widget_spec))
            handles.append(self.services.commands.register(self.command_spec))
            handles.append(self.services.tools.register(self.tool_spec))
            handles.append(self.services.routes.register(self.route_spec))
            handles.append(self.services.events.subscribe(EVENT_NAME, self._record_service_event))

            self._background_release = asyncio.Event()
            self._background_started = asyncio.Event()
            self._background_task = self.services.tasks.spawn(
                self._background_worker(
                    started=self._background_started,
                    release=self._background_release,
                ),
                _BACKGROUND_TASK_NAME,
            )
            await self._background_started.wait()

            await self._initialize_storage()
            self.started = True
            await self.services.events.publish(
                EVENT_NAME,
                {
                    "extension_id": self.services.extension_id,
                    "kind": "started",
                    "view_id": self.view.id,
                },
            )
            await self._persist_final_state()
        except Exception:
            for handle in reversed(handles):
                handle.dispose()
            if self._background_release is not None:
                self._background_release.set()
            if self._background_task is not None:
                try:
                    await self._background_task
                except asyncio.CancelledError:
                    raise
                except Exception:
                    pass
            self._background_release = None
            self._background_started = None
            self._background_task = None
            self.started = False
            self._state = self._snapshot()
            raise

        self._started_handles = handles
        self._state = self._snapshot()

    async def stop(self) -> None:
        """Stop the diagnostic extension and release owned registrations."""
        if not self.started:
            return

        if self._background_release is not None:
            self._background_release.set()
        task = self._background_task
        self._background_task = None
        self._background_release = None
        self._background_started = None
        if task is not None:
            await task
            await asyncio.sleep(0)

        for handle in reversed(self._started_handles):
            handle.dispose()
        self._started_handles.clear()
        self.action_registry.dispose_extension(self.services.extension_id)
        self.started = False
        self._state = self._snapshot()

    async def dispose(self) -> None:
        """Dispose the extension and its owned service bundle."""
        if self.disposed:
            return
        await self.stop()
        await self.services.dispose()
        self.disposed = True

    def _setup(self, registrar: ExtensionRegistrar) -> Sequence[DisposalHandle]:
        return (
            registrar.contribute("views", VIEW_ID, self.view),
            registrar.contribute("actions", ACTION_ID, self.action_definition),
            registrar.contribute("file_renderers", FILE_RENDERER_ID, self.file_renderer_spec),
            registrar.contribute(
                "editor_annotations",
                ANNOTATION_PROVIDER_ID,
                self.annotation_provider_spec,
            ),
            registrar.contribute("widgets", WIDGET_ID, self.widget_spec),
            registrar.contribute("commands", COMMAND_NAME, self.command_spec),
            registrar.contribute("tools", TOOL_NAME, self.tool_spec),
            registrar.contribute("routes", _ROUTE_CONTRIBUTION_KEY, self.route_spec),
            registrar.contribute(
                "assets",
                _ASSET_CONTRIBUTION_KEY,
                {"mime_type": "application/json", "path": ASSET_PATH},
            ),
            registrar.contribute(
                "events",
                _EVENT_CONTRIBUTION_KEY,
                {"name": EVENT_NAME},
            ),
            registrar.on("activate", lambda: self.host_events.append("activate")),
            registrar.on("deactivate", lambda: self.host_events.append("deactivate")),
        )

    async def _initialize_storage(self) -> None:
        global_storage = self.services.storage.global_()
        workspace_storage = self.services.storage.workspace(WORKSPACE_SCOPE_ID)
        session_storage = self.services.storage.session(SESSION_SCOPE_ID)

        current = await global_storage.get(GLOBAL_STATE_KEY)
        expected_revision = 0 if current is None else current.revision
        created = await global_storage.save(
            GLOBAL_STATE_KEY,
            {
                "extension_id": self.services.extension_id,
                "phase": "initial",
                "view_id": self.view.id,
            },
            expected_revision=expected_revision,
        )
        self.state_revision = created.revision

        workspace_current = await workspace_storage.get(WORKSPACE_STATE_KEY)
        workspace_expected = 0 if workspace_current is None else workspace_current.revision
        workspace_record = await workspace_storage.save(
            WORKSPACE_STATE_KEY,
            {"scope": "workspace", "started": True},
            expected_revision=workspace_expected,
        )
        self.workspace_revision = workspace_record.revision

        session_current = await session_storage.get(SESSION_STATE_KEY)
        session_expected = 0 if session_current is None else session_current.revision
        session_record = await session_storage.save(
            SESSION_STATE_KEY,
            {"scope": "session", "started": True},
            expected_revision=session_expected,
        )
        self.session_revision = session_record.revision

    async def _persist_final_state(self) -> None:
        if self.state_revision is None:
            raise RuntimeError("storage was not initialized")
        next_revision = self.state_revision + 1
        snapshot = self._snapshot(storage_revision=next_revision)
        updated = await self.services.storage.global_().save(
            GLOBAL_STATE_KEY,
            snapshot,
            expected_revision=self.state_revision,
        )
        self.state_revision = updated.revision
        self._state = snapshot

    async def _background_worker(self, *, started: asyncio.Event, release: asyncio.Event) -> None:
        started.set()
        await release.wait()

    def _record_service_event(self, payload: JSONValue) -> None:
        if isinstance(payload, dict):
            self.service_events.append(payload.copy())
        else:
            self.service_events.append({"payload": payload})
        self._state = self._snapshot()

    async def _execute_action(self, context: ActionContext) -> ActionResult:
        context.raise_if_cancelled()
        return ActionResult(
            data={
                "event_count": len(self.service_events),
                "extension_id": self.services.extension_id,
                "payload": dict(context.request.payload),
                "started": self.started,
            },
            invalidations=(Invalidation(target="view", key=self.view.id),),
            patches=(
                PropertyPatch(
                    view_id=self.view.id,
                    path="/components/0/text",
                    value="diagnostic-ready",
                    sequence=1,
                ),
            ),
        )

    def _render_file(self, context: FileRenderContext) -> StandardView | WidgetReference:
        if context.path.endswith(".json"):
            return WidgetReference(WIDGET_ID)
        return self.view

    def _annotate_file(self, context: FileRenderContext) -> tuple[EditorAnnotation, ...]:
        return (
            EditorAnnotation(
                1,
                f"Diagnostic fixture: {context.path}",
                severity="info",
                source="tau.diagnostic",
            ),
        )

    def _widget_snapshot(self, payload: JSONObject) -> JSONObject:
        return {"payload": dict(payload), "snapshot": self.snapshot()}

    def _run_command(self) -> JSONObject:
        return self.snapshot()

    def _run_tool(self, arguments: JSONObject) -> JSONObject:
        return {
            "arguments": dict(arguments),
            "snapshot": self.snapshot(),
        }

    def _route_response(self, request: RouteRequest) -> RouteResponse:
        return RouteResponse(
            200,
            body={
                "event_count": len(self.service_events),
                "extension_id": self.services.extension_id,
                "method": request.method,
                "path": request.path,
                "started": self.started,
                "storage_revision": self.state_revision,
            },
        )

    def _snapshot(self, *, storage_revision: int | None = None) -> JSONObject:
        return {
            "asset_path": ASSET_PATH,
            "event_count": len(self.service_events),
            "extension_id": self.services.extension_id,
            "route_path": ROUTE_PATH,
            "session_revision": self.session_revision,
            "started": self.started,
            "storage_revision": self.state_revision
            if storage_revision is None
            else storage_revision,
            "view_id": self.view.id,
            "workspace_revision": self.workspace_revision,
        }


def _build_view() -> StandardView:
    return StandardView(
        id=VIEW_ID,
        title="Built-in Diagnostic",
        placement="dashboard",
        components=(
            Text(text="diagnostic-ready", style="muted", live=True),
            Metric(label="Events", value=0),
            Progress(label="Startup", value=1, max=1),
            Button(
                label="Refresh",
                action_id=ACTION_ID,
                accessible_label="Refresh diagnostic state",
                payload={"source": "diagnostic"},
                variant="primary",
            ),
            Field(
                name="environment",
                label="Environment",
                input_type="select",
                required=True,
                value="local",
                options=(
                    FieldOption(label="Local", value="local"),
                    FieldOption(label="CI", value="ci"),
                ),
            ),
            Table(
                label="Scopes",
                columns=(
                    TableColumn(label="Scope", key="scope"),
                    TableColumn(label="State", key="state"),
                ),
                rows=(
                    {"scope": "global", "state": "ready"},
                    {"scope": "workspace", "state": "ready"},
                ),
            ),
            Stack(
                direction="column",
                accessible_label="Diagnostic summary",
                children=(Text(text="Nested summary", style="code", live=False),),
            ),
        ),
    )


def _widget_script_bytes() -> bytes:
    return b"""(() => {
  'use strict';
  const root = document.getElementById('tau-widget-root');
  const status = document.createElement('pre');
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = 'Load diagnostic snapshot';
  button.addEventListener('click', async () => {
    try {
      const result = await window.tauWidget.action({name: 'snapshot', payload: {source: 'widget'}});
      status.textContent = JSON.stringify(result, null, 2);
    } catch (error) {
      status.textContent = error instanceof Error ? error.message : 'Widget action failed.';
    }
  });
  root.replaceChildren(button, status);
})();
"""


def _json_bytes(value: JSONValue) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def create_extension(services: ExtensionServices) -> DiagnosticExtension:
    """Create the built-in diagnostic extension."""
    if services.extension_id != DIAGNOSTIC_EXTENSION_ID:
        raise ValueError(
            f"expected extension_id {DIAGNOSTIC_EXTENSION_ID!r}, got {services.extension_id!r}"
        )
    return DiagnosticExtension(services)


__all__ = [
    "ACTION_ID",
    "ASSET_PATH",
    "COMMAND_NAME",
    "DIAGNOSTIC_EXTENSION_ID",
    "FILE_RENDERER_ID",
    "ANNOTATION_PROVIDER_ID",
    "DiagnosticExtension",
    "EVENT_NAME",
    "GLOBAL_STATE_KEY",
    "ROUTE_PATH",
    "SESSION_SCOPE_ID",
    "SESSION_STATE_KEY",
    "TOOL_NAME",
    "VIEW_ID",
    "WIDGET_ID",
    "WIDGET_SCRIPT_PATH",
    "WORKSPACE_SCOPE_ID",
    "WORKSPACE_STATE_KEY",
    "create_extension",
]
