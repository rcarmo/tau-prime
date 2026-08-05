# Extension examples

Compact, **partial** snippets verified against Tau's current extension contracts and tests. See [architecture](./architecture.md), [API](./api.md), and [extensions](./extensions.md) for the full model.

## Built-in reference: `tau.diagnostic`

Start with:
- `src/tau_extensions/builtin/diagnostic/tau-extension.json`
- `src/tau_extensions/builtin/diagnostic/extension.py`

It demonstrates declarative views/actions, file renderers, editor annotations, local assets, a sandboxed widget, routes, commands, tools, events, and storage.

## Declarative `StandardView` + action

**Partial snippet**. Requires `views` and `actions`.

```python
import asyncio
from tau_extensions.web import ActionDefinition, ActionExecutor, ActionRegistry, ActionRequest, ActionResult, Button, StandardView, Text, view_to_json

view = StandardView(
    id="status-view",
    title="Status",
    placement="sidebar",
    components=(
        Text(text="Ready", style="muted", live=True),
        Button(label="Refresh", action_id="refresh-status", accessible_label="Refresh status", payload={"force": True}, variant="primary"),
    ),
)

async def refresh(context) -> ActionResult:
    context.raise_if_cancelled()
    return ActionResult(data={"ok": True})

async def main() -> None:
    registry = ActionRegistry()
    registry.register("com.example.demo", ActionDefinition(id="refresh-status", handler=refresh, requires_approval=True, idempotent=True))
    result = await ActionExecutor(registry, approval_callback=lambda request, definition: True).execute(
        ActionRequest(request_id="req-1", extension_id="com.example.demo", action_id="refresh-status", view_id="status-view", payload={"force": True}, idempotency_key="refresh-1")
    )
    assert view_to_json(view)["placement"] == "sidebar"
    assert result.data == {"ok": True}

asyncio.run(main())
```

## `FileRendererSpec` + `AnnotationProviderSpec`

**Partial snippet**. Requires `views`.

```python
from tau_extensions import AnnotationProviderSpec, EditorAnnotation, FileRenderContext, FileRendererSpec
from tau_extensions.web import StandardView, Text

context = FileRenderContext("notes/demo.md", "text/markdown", "# Demo")
view = StandardView(id="markdown-preview", title="Markdown preview", placement="sidebar", components=(Text("Demo"),))

renderer = FileRendererSpec("markdown", lambda value: view if value.content else None, filename_patterns=("*.md",), priority=10)
provider = AnnotationProviderSpec("headings", lambda value: (EditorAnnotation(1, f"{value.path} heading", source="demo"),), media_types=("text/*",))

assert renderer.matches(context)
assert provider.matches(context)
```

Register them with `services.file_renderers.register(renderer)` and `services.annotation_providers.register(provider)`.

## Sandboxed `WidgetSpec`

**Partial snippet**. Requires `assets` and `sandboxed_widgets`. This is the medium-trust path.

Python registration:

```python
from tau_extensions import WidgetSpec

services.assets.register("widget.js", b"document.getElementById('tau-widget-root').textContent = 'ready';", mime_type="application/javascript")
widget = WidgetSpec("preview", "Preview", "widget.js", actions={"snapshot": lambda payload: {"payload": payload}})
services.widgets.register(widget)
```

Local widget JS:

```js
// Runs inside Tau's sandboxed widget document, not in the main page.
const result = await window.tauWidget.action({ name: "snapshot", payload: { source: "widget" } });
console.log(result);
```

Notes:
- widget document: `/api/extensions/widgets/{extension_id}/{widget_id}`
- narrow bridge: `tauWidget.action(...)`, `submit(...)`, `requestRefresh(...)`, `close(...)`
- widget action POST: `/api/extensions/widgets/{extension_id}/{widget_id}/actions/{action}`

## Admin trusted frontend module

**Partial snippet**. Requires `assets` and `trusted_frontend`. This is the high-trust path for built-in or admin-installed extensions only; workspace JavaScript is rejected.

Python registration:

```python
import base64, hashlib
from tau_extensions import TRUSTED_FRONTEND_SDK_VERSION, TrustedFrontendModuleSpec

script = b"export async function activate(api) { await api.request('/api/health'); }"
integrity = "sha256-" + base64.b64encode(hashlib.sha256(script).digest()).decode("ascii")
assert TRUSTED_FRONTEND_SDK_VERSION == "1.0"

services.assets.register("trusted/main.js", script, mime_type="application/javascript")
services.trusted_frontend.register(TrustedFrontendModuleSpec("shell", "trusted/main.js", integrity, sdk_version=TRUSTED_FRONTEND_SDK_VERSION))
```

Local trusted JS asset:

```js
export async function activate(api) {
  api.mountSlot("sidebar", (container, { signal }) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `Trusted ${api.extensionId}/${api.moduleId}`;
    signal.addEventListener("abort", () => button.remove(), { once: true });
    container.appendChild(button);
    return () => button.remove();
  });

  await api.request("/api/health"); // same-origin /api/* only
  return async () => {
    // SDK 1.0 calls this disposer after aborting mounted slots,
    // running mount disposers, and removing owned containers.
  };
}
```

Notes:
- `script_path` must point to a registered local JS asset and its bytes must match the declared `sha256-<base64>` digest
- SDK 1.0 modules export `activate(api)` (or a default function) and may return a disposer
- mountable slots: `dashboard`, `timeline_before`, `timeline_after`, `sidebar`, `compose_above`, `compose_below`
- browser loader limits: at most 64 descriptors and 1 MiB per JS asset
