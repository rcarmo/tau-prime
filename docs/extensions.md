# Extensions

Tau currently has **two extension seams**:

1. **Portable manifest-based contracts** in `tau_extensions`
2. **Legacy Python `setup(tau)` loading** in `tau_coding.extensions`

They are related, but they are **not** the same runtime.

See also [architecture](./architecture.md), [API](./api.md), and [extension examples](./examples.md).

## Current status

- `tau_extensions` ships the portable manifest format, discovery, trust/resolution logic, lifecycle host, typed web UI/actions, scoped storage, background tasks, commands, tools, routes, events, assets, file renderers, annotations, sandboxed widgets, and trusted frontend contracts.
- Tau Web exposes HTTP adapters and browser support for the portable services, including extension routes/assets, widgets, and trusted frontend modules.
- The portable package deliberately does **not** hard-code discovery roots or auto-import code. The default web server starts with an empty extension directory; an embedding host chooses roots, resolves approvals and policy, loads code, and registers service bundles.
- `tau_coding.extensions` remains the **compatibility path** used by the Python `*.py` TUI/coding extension seam.

## Portable API (`tau_extensions`)

Current stable version:

```python
from tau_extensions import API_VERSION
assert API_VERSION == "1.0"
```

Portable extensions are described by `tau-extension.json` manifests. The current schema is:

- `schema_version`: must be `1`
- `id`: lowercase reverse-domain name or slug
- `name`: non-blank display name
- `version`: strict semantic version
- `api_version`: exact or caret `major.minor` range compatible with `API_VERSION`
- `entrypoint`: `module.path:attribute`
- `permissions`: subset of `storage`, `background_tasks`, `assets`, `commands`, `tools`, `routes`, `events`, `views`, `actions`, `sandboxed_widgets`, `trusted_frontend`
- `dependencies`: optional list of `{id, version?}`
- `contributions`: host-defined JSON object

Bounds enforced in source: manifest `256 KiB`, contributions JSON `128 KiB`.

Example manifest:

```json
{
  "schema_version": 1,
  "id": "com.example.demo",
  "name": "Demo Extension",
  "version": "1.2.3",
  "api_version": "^1.0",
  "entrypoint": "demo.extension:setup",
  "permissions": ["commands", "views", "actions"],
  "dependencies": [{"id": "com.example.shared", "version": "^1.1"}],
  "contributions": {
    "commands": [{"name": "demo.hello", "title": "Hello"}],
    "settings": {"enabled": true}
  }
}
```

`contributions` is intentionally just validated JSON today. `tau_extensions` does not impose a global contribution schema there.

### Discovery is host-configured

```python
from pathlib import Path
from tau_extensions import ExtensionSource, discover_extensions

result = discover_extensions({
    ExtensionSource.BUILT_IN: [Path("/opt/tau/extensions")],
    ExtensionSource.ADMIN: [Path("/etc/tau/extensions")],
    ExtensionSource.WORKSPACE: [Path.cwd() / ".tau" / "extensions"],
})
```

Current discovery behaviour:

- `discover_extensions()` scans only the roots passed in by the host.
- It looks only at **immediate child directories** under each root.
- Each candidate directory must contain `tau-extension.json`.
- It does **not** recurse arbitrarily.
- It does **not** import or execute `entrypoint` code.
- Symlink roots, symlink child directories, and symlink manifests are rejected.
- Duplicate ids are resolved deterministically by source priority and path ordering, with diagnostics for skipped candidates.

Each discovered `Candidate` gets a `fingerprint` that is the **SHA-256 of the exact manifest bytes**. Whitespace-only manifest edits therefore change the fingerprint.

### Trust, approval, permissions, and dependencies

```python
from tau_extensions import Approval, TrustPolicy, resolve_extensions

candidate = result.candidates[0]
plan = resolve_extensions(
    [candidate],
    enabled_ids={candidate.manifest.id},
    approvals={Approval(candidate.manifest.id, candidate.fingerprint)},
    policy=TrustPolicy(),
)
```

Current resolution rules:

- **Built-in** extensions are enabled by default.
- **Admin** extensions must be explicitly enabled and present in `TrustPolicy(admin_allowlist=...)`.
- **Workspace** extensions must be explicitly enabled and must have an `Approval` matching the current fingerprint exactly.
- Permission requests are checked against per-source allowlists.
- Default workspace permissions are deliberately limited to `views`, `actions`, `events`, `commands`.
- Dependencies are checked for missing ids, disabled dependencies, version mismatches, and dependency cycles.
- Enabled candidates are returned in deterministic topological order.

The package does not currently persist approvals for you. Hosts must decide where approval state lives and when changed fingerprints require re-approval.

### `ExtensionHost` lifecycle

`ExtensionHost` owns activation, event dispatch, disposal, and development-time reload.

```python
from tau_extensions import ExtensionDefinition, ExtensionHost

host = ExtensionHost(
    plan,
    loader=lambda candidate: ExtensionDefinition(
        setup=lambda registrar: registrar.contribute("views", "status", {"id": candidate.manifest.id})
    ),
    development_mode=True,
)
host.activate_all()
host.emit("tick", {"count": 1})
host.deactivate_all()
```

Current behaviour:

- The host supplies `loader(candidate) -> ExtensionDefinition`.
- `ExtensionDefinition` may provide `setup(registrar)`, `activate()`, and `deactivate()`.
- `setup()` may return a `Disposable`, a callable disposer, or a sequence of either.
- `ExtensionRegistrar.contribute()` registers deterministic contributions through `ContributionRegistry`.
- `ExtensionRegistrar.on()` registers event listeners owned by that extension.
- Activation runs in plan order; deactivation disposes in reverse activation order.
- Setup-owned handles, event listeners, and contributions are cleaned up automatically.
- Failures are isolated into `RuntimeDiagnostic` entries.
- `reload()` works only with `development_mode=True`, and only for the same extension id.

There is **no built-in code importer** in `tau_extensions`. Discovery validates `entrypoint`, but a host decides how and when to import code from a candidate directory.

## Declarative web UI (`tau_extensions.web`)

Stable imports that exist today:

```python
from tau_extensions.web import (
    ActionDefinition, ActionExecutor, ActionRegistry, ActionRequest, ActionResult,
    Button, Field, Metric, Progress, Stack, StandardView, Table, Text, view_to_json,
)
```

`StandardView` is a typed, declarative, portable view model.

Current placements (slots):

- `compose_above`
- `compose_below`
- `sidebar`
- `timeline_before`
- `timeline_after`
- `dashboard`

Current view kinds: `card`, `detail`, `form`.

Current component kinds: `Text`, `Button`, `Metric`, `Progress`, `Field`, `Table`, `Stack`.

Example:

```python
from tau_extensions.web import Button, StandardView, Text, view_to_json

view = StandardView(
    id="status-view",
    title="Status",
    placement="sidebar",
    components=(
        Text(text="Ready", style="muted", live=True),
        Button(label="Refresh", action_id="refresh-status", accessible_label="Refresh status", payload={"force": True}, variant="primary"),
    ),
)
assert view_to_json(view)["placement"] == "sidebar"
```

Current limits enforced in source:

- canonical view JSON: `64 KiB`
- action payload JSON on buttons/fields: `8 KiB`
- maximum depth: `12`
- maximum node count: `256`
- maximum text size: `16 KiB`
- maximum table size: `50` rows, `20` columns

The Python contract validates and canonicalises views; `view_to_json()` produces a deterministic JSON-safe payload.

### Browser renderer

Tau Web serves `/static/extension-ui.js`, which mirrors the same view contract in the browser.

Current browser behaviour:

- listens for `CustomEvent("tau:extension-view", {detail: view_json})`
- validates and renders the view into one of the six slots above
- dispatches `CustomEvent("tau:extension-action", ...)` when a `Button` is pressed
- includes `view_id`, `action_id`, and merged JSON payload in the action event detail

The renderer and server-side service path are shipped. Manifest discovery and activation remain host policy: the stock server does not scan directories or import portable extension code automatically.

### Trusted frontend modules

Tau also exposes a **trusted frontend module** contract for exceptional host-integrated cases. See [architecture](./architecture.md) for trust tiers, [API](./api.md) for `/api/extensions/...` routes, and [extension examples](./examples.md) for compact verified snippets.

Current policy and validation constraints:

- Only **built-in** and **administrator-installed** extensions are eligible for exposure.
- Workspace-sourced extensions are hard-denied for `trusted_frontend`, even if a policy allowlist tries to include it.
- Each module must declare:
  - `sdk_version` matching the current trusted frontend SDK version.
  - `integrity` in standard SRI form: `sha256-<base64>`.
- `script_path` must be a safe relative path and must resolve to a **locally registered extension asset**.
- The Python registry requires that asset to be JavaScript (`application/javascript` or `text/javascript`) and that its bytes match the declared SRI digest.
- Browser descriptors are validated strictly: they must contain exactly `asset_url`, `extension_id`, `integrity`, `module_id`, and `sdk_version`.
- In the browser loader, `asset_url` must resolve to the same origin and its pathname must start with `/api/extensions/assets/`.
- The browser loader fetches at most **64** module descriptors and at most **1 MiB** per JS asset.
- Loaded assets must remain JavaScript when served (`application/javascript`, `text/javascript`, `application/ecmascript`, or `text/ecmascript`).
- No workspace JavaScript is loaded through this path.

Current browser module shape and lifecycle from `frontend-sdk.js`:

- The module must export `activate(api)` or a default function.
- `activate(api)` may return a disposer function; `disposeAll()` later awaits that disposer.
- `api` is a frozen object exposing:
  - `version`
  - `extensionId`
  - `moduleId`
  - `request(path, options)`
  - `submit`
  - `navigate`
  - `mountSlot(slot, mount)`
- `request(...)` is limited to same-origin `/api/*` targets.
- `mountSlot(...)` is limited to `dashboard`, `timeline_before`, `timeline_after`, `sidebar`, `compose_above`, and `compose_below`.
- `mountSlot(...)` appends one owned container into that slot, passes `(container, {signal})` to the mount callback, and records an optional mount disposer returned by the callback.
- On disposal, the SDK aborts mount signals, awaits mount disposers, removes owned containers, and only then awaits the module disposer.
- Trusted modules run with the page's same-origin privileges; they are **not sandboxed widgets**.

Use this tier only when a declarative view or sandboxed widget cannot meet requirements, for example:

- shell-level keyboard/navigation integration,
- host-owned DOM or slot integration points,
- APIs unavailable through the widget bridge.

Ordinary custom rendering is **not** sufficient justification for trusted frontend modules.

### Typed action execution

```python
import asyncio
from tau_extensions.web import ActionDefinition, ActionExecutor, ActionRegistry, ActionRequest, ActionResult

async def refresh(context) -> ActionResult:
    context.raise_if_cancelled()
    return ActionResult(data={"ok": True})

async def main() -> None:
    registry = ActionRegistry()
    registry.register("com.example.demo", ActionDefinition(id="refresh-status", handler=refresh, requires_approval=True, idempotent=True))
    result = await ActionExecutor(registry, approval_callback=lambda request, definition: True).execute(
        ActionRequest(request_id="req-1", extension_id="com.example.demo", action_id="refresh-status", view_id="status-view", payload={"force": True}, idempotency_key="refresh-1")
    )
    assert result.data == {"ok": True}

asyncio.run(main())
```

Current `ActionExecutor` semantics:

- `ActionDefinition.handler` must be an **async** callable.
- Requests, definitions, patches, invalidations, and results are validated types.
- Errors are raised as `ActionError` with stable `.code` values such as `action_not_found`, `approval_denied`, `cancelled`, `duplicate_request`, `idempotency_conflict`, `invalid_request`, `invalid_result`, `timeout`, and `internal`.
- `requires_approval=True` uses a host-supplied sync-or-async `approval_callback`.
- Execution is bounded by global executor concurrency, per-action concurrency, and per-action timeout.
- `cancel(request_id)` sets the request cancellation event and cancels the task.
- Idempotent actions require `idempotency_key` and deduplicate by `(extension_id, action_id, idempotency_key)` plus a canonical payload fingerprint.
- Completed idempotent results are cached with an LRU bound.
- `ActionResult` may include `data`, `invalidations`, and `patches`.

`PatchBuffer` is also available when a host wants to coalesce the latest property patch per `(view_id, path)` and reject stale sequence numbers.

## Compatibility path: legacy `*.py` `setup(tau)` extensions

This is the **current Tau Prime/TUI compatibility seam**, not the portable manifest runtime.

Current legacy discovery roots come from `TauResourcePaths` and are loaded as Python files:

- `~/.tau/extensions/*.py`
- `~/.agents/extensions/*.py`
- `<project>/.tau/extensions/*.py`
- `<project>/.agents/extensions/*.py`

Loading is best-effort:

- files are imported directly
- `setup(tau)` is called if present
- failures become diagnostics instead of aborting session start-up
- there is no manifest discovery, trust policy, fingerprint approval, or portable permission model here

Minimal example:

```python
from tau_coding.commands import CommandResult

def setup(tau):
    tau.register_prompt_guideline("Prefer concise answers.")
    tau.register_command(
        "hello",
        lambda context, args: CommandResult(handled=True, message=f"hello {args or 'world'}"),
        description="Say hello",
    )
```

The legacy API also exposes more Tau-specific hooks such as tools, input hooks, event/lifecycle listeners, message/tool renderers, and TUI-only UI helpers. Treat that seam as a compatibility layer, not as the portable extension contract.

## Security guidance

- Prefer portable manifest discovery over blind Python import when you need policy enforcement.
- Keep discovery roots explicit and narrow; do not scan arbitrary writable directories.
- Treat workspace extensions as untrusted until their current manifest fingerprint is approved.
- Re-approve when the manifest fingerprint changes, even if the JSON meaning looks the same.
- Grant the smallest permission set possible.
- Do not assume `entrypoint` validation means code is safe to import.
- Import extension code only after resolution, and isolate loader failures.
- For action flows, require approval for operations that mutate state or call external systems.
- If you expose browser-backed extension UI, remember that the shipped renderer exists before full public-services integration; wire auth, routing, and activation deliberately.
