# Tau Web Runtime and Python Web Extension Specification

Status: proposed design
Branch: `vibes`
Target: Tau Prime after 42.3.0
Reference Vibes branch: `rcarmo/vibes@python` at `41078033252fd02a54ddf2e9c9d1119038720b89`

## Purpose

Tau already has the part of an agent application that is hardest to keep correct: a provider-neutral loop, structured tool execution, an event stream, cancellation, steering, follow-ups, compaction and a durable branch model. Vibes has the browser product around that loop: a responsive timeline, compose box, workspace explorer, editor, media handling, search and an SSE transport.

This design brings the Vibes web product into Tau without retaining Vibes' Pi RPC or ACP agent runtimes. Tau remains the application. The adapted Vibes frontend becomes Tau's web shell, and a Python web-extension contract provides the supported route from Python state and actions to browser components.

The design has four non-negotiable properties:

* SQLite is the only durable runtime and session store. Tau's JSONL format remains available for import and export, but no live session depends on a JSONL sidecar.
* Named sessions are first-class addresses. `@name` works in the compose box and in the `chat` tool, with the same resolution rules.
* The runtime uses `asyncio` and can execute independent agent sessions in parallel. A busy session serialises its own turns but does not block another session.
* The initial distribution includes the Piclaw-equivalent compose box, Plan sidebar, system meters and session dashboard as baseline extensions or host contributions using the public contract.

## Scope

The first supported product is a single-user Tau web service with multiple concurrent Tau sessions in one workspace. The browser can create, rename, archive, restore and switch sessions; each active session has a unique `@name`. Sessions can send messages to each other without routing through the browser.

The service includes:

* Tau's in-process `CodingSession`, `AgentHarness` and provider implementations;
* a Vibes-derived Preact shell and CodeMirror workspace editor;
* aiohttp REST and SSE endpoints;
* SQLite sessions, messages, branch entries, plans, extension state, media and FTS;
* a Python web-extension host;
* sandboxed custom widgets as an escape hatch;
* a bounded asynchronous agent pool;
* loopback-safe defaults and explicit remote-deployment controls.

ACP and Pi RPC are not part of the Tau web runtime. Standalone Vibes may keep them, but Tau must not ship two competing agent loops.

## Architectural boundaries

```text
Browser
  |-- REST: sessions, messages, workspace, media, extensions
  `-- SSE: Tau events, run state, invalidations and notifications
          |
Tau Web (aiohttp)
  |-- web shell and declarative component renderer
  |-- extension host and action dispatcher
  |-- session router and chat service
  |-- SQLite repositories and single-writer service
  `-- AsyncAgentPool
       |-- @default -> CodingSession -> AgentHarness -> run_agent_loop
       |-- @review  -> CodingSession -> AgentHarness -> run_agent_loop
       `-- @tests   -> CodingSession -> AgentHarness -> run_agent_loop
```

The canonical Python event hierarchy remains `tau_agent.events.AgentEvent`. Web transport wraps those events but does not replace them with another Python hierarchy.

The browser shell owns DOM construction, layout, themes, accessibility, routing and error boundaries. Python extensions own semantics, data retrieval and actions. Declarative component descriptions cross that boundary.

## Package layout

```text
src/
  tau_ai/
  tau_agent/
  tau_coding/
  tau_extensions/
    api.py
    manifest.py
    permissions.py
    lifecycle.py
    tasks.py
    storage.py
    web/
      actions.py
      components.py
      contributions.py
      events.py
      schema.py
  tau_web/
    app.py
    config.py
    runtime.py
    agent_pool.py
    chat.py
    event_adapter.py
    extension_host.py
    session_factory.py
    sqlite/
      connection.py
      migrations.py
      writer.py
      repositories.py
    routes/
    baseline_extensions/
      compose.py
      plan.py
      meters.py
      session_dashboard.py
    static/
```

`tau_extensions` must not import aiohttp, SQLite drivers or frontend implementation modules. It is a portable contract. `tau_web` implements that contract.

## Runtime identities

Several identifiers are necessary because a visual conversation, a durable agent context and one execution are not the same object.

### Workspace

A workspace is a resolved filesystem root and a security boundary. Its identifier is a stable digest of the resolved path. Every session belongs to one workspace.

### Session

A session is one independent Tau agent context. It owns:

* a stable UUID `session_id`;
* an active unique alias `agent_name`, addressed as `@agent_name`;
* one workspace;
* a provider and model selection;
* a Tau session-entry tree and active leaf;
* a steering queue and a follow-up queue;
* at most one active agent run;
* zero or more browser connections.

The default session alias is `default`. Aliases use `[A-Za-z0-9][A-Za-z0-9._-]*`, are compared case-insensitively and are unique among non-archived sessions. Renaming is transactional.

### Session branch

Tau's existing entry-tree branching remains inside a session. A web session may also be cloned into a new named session. These are different operations:

* branch changes the active leaf inside one context;
* clone creates a new session with copied reachable entries and a new alias.

### Run

A run is one invocation of `CodingSession.prompt()` or `continue_()`. It has a `run_id`, timestamps, status and cancellation scope. Runs are persisted for recovery and observability, but streamed deltas need not all be stored individually.

### Connection

A connection is one browser SSE subscriber. Multiple tabs may observe the same session. Disconnecting a browser does not cancel a run unless policy explicitly says otherwise.

## Asyncio execution model

The web service has one asyncio event loop per process. All request handlers, extension actions, provider streams, SQLite writes and SSE broadcasts are asynchronous from the caller's point of view.

### Agent pool

`AsyncAgentPool` owns loaded session runtimes:

```python
class AsyncAgentPool:
    async def get(self, session_id: str) -> ManagedSession: ...
    async def resolve(self, address: SessionAddress) -> ManagedSession: ...
    async def create(self, request: CreateSessionRequest) -> ManagedSession: ...
    async def archive(self, session_id: str) -> None: ...
    async def shutdown(self) -> None: ...
```

Each `ManagedSession` owns:

```python
@dataclass
class ManagedSession:
    session: CodingSession
    turn_lock: asyncio.Lock
    run_task: asyncio.Task[None] | None
    run_id: str | None
    subscribers: set[EventSink]
    last_active_at: datetime
```

The turn lock is per session, never global. Different sessions can stream model responses and run tools concurrently. Submitting to a busy session uses `auto`, `steer` or `queue` semantics rather than waiting while holding an HTTP request open.

### Concurrency bounds

Parallel does not mean unbounded. The runtime provides independent limits for:

* active provider streams;
* subprocess tools;
* Python tools;
* extension actions;
* workspace mutations;
* loaded idle sessions.

The default provider-stream semaphore should allow at least four concurrent sessions. A provider may declare a stricter limit. File write/edit tools retain per-path locks so two sessions cannot interleave mutations to the same file. Shell and Python subprocesses run in their own process groups and honour cancellation.

No extension may call unmanaged `asyncio.create_task()` for durable work. `context.tasks.start()` creates an owned task in a runtime `TaskGroup`, associates it with the extension/session and ensures cancellation during unload or shutdown.

### Structured lifecycle

The application uses `asyncio.TaskGroup` for long-lived services:

```text
application TaskGroup
  |-- SQLite writer
  |-- system metrics sampler
  |-- workspace watcher
  |-- event broadcaster
  `-- agent pool
       `-- one child task per active run
```

An agent failure is isolated to its run. It does not tear down the pool or another session.

### Cancellation

Cancellation is cooperative from browser to provider/tool:

```text
POST cancel -> ManagedSession.session.cancel()
            -> provider CancellationToken
            -> tool cancellation token/process-group termination
            -> terminal Tau ErrorEvent/AgentEndEvent
```

Force-cancelling the run task is a bounded fallback after a grace period. The harness repairs dangling tool calls before the next prompt, and the repair is committed to SQLite.

## Named sessions and routing

### Address grammar

A session can be addressed by exactly one of:

```text
@name
session:<uuid>
chat_jid:<logical-id>
```

`@name` is preferred for people and agents. UUID is the durable API identifier. `chat_jid` is a compatibility field for imported Piclaw/Vibes data and transport adapters; Tau-native APIs use `session_id`. Public tool parameters retain `target_chat_jid` because this is the existing cross-session transport contract, while the local router resolves it to a session UUID before delivery.

The local alias registry is derived transactionally from the sessions table. It does not depend on a process-local map, although the pool caches active resolutions.

### Compose-box mentions

When the compose box is empty, typing `@` opens the session switcher, matching Piclaw. Inside non-empty text, `@name` provides mention completion. A leading mention followed by content is a routing instruction:

```text
@review check the API changes
```

The source timeline records the user's original message. The routed envelope is delivered to `@review`, and the API response includes source and target identities. A non-leading mention is ordinary content unless an extension explicitly interprets it.

Unknown names fail before a user message is committed as delivered. The UI keeps the draft and shows the resolution error.

### Chat tool contract

The baseline runtime registers `chat` as a Tau tool:

```python
class ChatArgs(BaseModel):
    target_address: str | None = None
    target_chat_jid: str | None = None
    target_agent_name: str | None = None
    content: str
    mode: Literal["auto", "queue", "steer"] = "auto"
    idempotency_key: str | None = None
    in_reply_to: str | None = None
```

Exactly one target field is required. `target_agent_name` accepts `name` or `@name` and is the preferred local form. `target_chat_jid` provides stable compatibility with existing callers. `target_address` is reserved for installed transports and accepts a single transport hop, for example `lab!@review`; multi-hop paths are rejected.

Delivery creates an immutable `chat_deliveries` row before dispatch. A unique `(transport, idempotency_key)` constraint provides retry deduplication. The target receives structured origin metadata:

```json
{
  "source_session_id": "...",
  "source_agent_name": "default",
  "target_session_id": "...",
  "target_agent_name": "review",
  "delivery_id": "...",
  "in_reply_to": null,
  "mode": "steer"
}
```

The message shown to the model uses a stable human-readable header equivalent to Piclaw's peer messages, but origin identity is not inferred from text. Sender identity always comes from the active session context and cannot be supplied by tool arguments.

### Delivery semantics

* `steer`: if the target is running, enqueue in Tau's steering queue; otherwise begin a prompt.
* `queue`: enqueue a follow-up behind an active run; if idle, begin a prompt.
* `auto`: steer an active local session and prompt an idle one. Transport adapters may choose queue when immediate steering is unavailable.

Delivery is non-blocking with respect to target completion. The tool returns after durable acceptance and dispatch. Waiting for the target's final answer would deadlock agent cycles and waste provider concurrency.

Cycle prevention is operational rather than absolute: each envelope carries a bounded hop count and ancestry list. A delivery that repeats a session in its ancestry beyond policy is rejected. Rate limits apply per source and target.

## SQLite as the only store

### Principles

The live runtime uses one SQLite database by default. It contains session metadata, Tau entry trees, web timeline records, media, plans, extension state, queues, deliveries, run state, usage data and FTS indexes.

SQLite settings:

```sql
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;
PRAGMA temp_store = MEMORY;
```

One asynchronous writer owns the write connection. Read-only connections are pooled and may execute concurrently. Python code uses `aiosqlite` initially; repository interfaces hide the driver so a future dedicated worker thread or APSW implementation does not alter callers.

### Writer service

All mutations are submitted to `SqliteWriter`:

```python
await writer.transaction(lambda tx: ...)
```

The writer processes requests in FIFO order, supports transaction priorities for cancellation and run-finalisation, and applies backpressure through a bounded queue. Extension storage uses the same service. Extensions never receive raw connections.

### Core schema

The exact migration SQL may evolve, but version 1 must represent the following entities.

```sql
CREATE TABLE workspaces (
  workspace_id TEXT PRIMARY KEY,
  root_path TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE sessions (
  session_id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id),
  agent_name TEXT NOT NULL COLLATE NOCASE,
  title TEXT,
  provider_name TEXT NOT NULL,
  model TEXT NOT NULL,
  thinking_level TEXT,
  active_leaf_entry_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  archived_at TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE UNIQUE INDEX sessions_active_agent_name
ON sessions(agent_name COLLATE NOCASE)
WHERE archived_at IS NULL;

CREATE TABLE session_entries (
  entry_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  parent_entry_id TEXT REFERENCES session_entries(entry_id),
  entry_type TEXT NOT NULL,
  timestamp REAL NOT NULL,
  ordinal INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  UNIQUE(session_id, ordinal)
);

CREATE INDEX session_entries_parent
ON session_entries(session_id, parent_entry_id);

CREATE TABLE timeline_messages (
  message_id INTEGER PRIMARY KEY AUTOINCREMENT,
  public_id TEXT NOT NULL UNIQUE,
  session_id TEXT REFERENCES sessions(session_id),
  entry_id TEXT REFERENCES session_entries(entry_id),
  thread_id INTEGER REFERENCES timeline_messages(message_id),
  role TEXT NOT NULL,
  content TEXT NOT NULL DEFAULT '',
  content_blocks_json TEXT,
  sender_session_id TEXT REFERENCES sessions(session_id),
  delivery_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  deleted_at TEXT
);

CREATE TABLE session_runs (
  run_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(session_id),
  status TEXT NOT NULL,
  started_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  ended_at TEXT,
  last_event_type TEXT,
  last_status_json TEXT,
  error_json TEXT
);
```

`session_entries.payload_json` is validated through Tau's Pydantic entry models. It stores the existing entry variants: session info, message, model change, thinking change, compaction, branch summary, label, leaf and custom.

The session's active leaf and appended entries are committed atomically. Appending a model response, tool result or compaction cannot leave the leaf pointing at a missing entry.

### Queues and deliveries

```sql
CREATE TABLE queued_messages (
  queue_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  queue_kind TEXT NOT NULL CHECK(queue_kind IN ('steer','follow_up')),
  position INTEGER NOT NULL,
  content_json TEXT NOT NULL,
  source_session_id TEXT REFERENCES sessions(session_id),
  created_at TEXT NOT NULL,
  consumed_at TEXT,
  UNIQUE(session_id, queue_kind, position)
);

CREATE TABLE chat_deliveries (
  delivery_id TEXT PRIMARY KEY,
  transport TEXT NOT NULL DEFAULT 'local',
  source_session_id TEXT NOT NULL REFERENCES sessions(session_id),
  target_session_id TEXT REFERENCES sessions(session_id),
  target_address TEXT,
  mode TEXT NOT NULL,
  content TEXT NOT NULL,
  idempotency_key TEXT,
  in_reply_to TEXT,
  ancestry_json TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  accepted_at TEXT,
  error_json TEXT
);

CREATE UNIQUE INDEX chat_delivery_dedupe
ON chat_deliveries(transport, idempotency_key)
WHERE idempotency_key IS NOT NULL;
```

Harness queue mutations are mirrored to SQLite before returning success. On load, unconsumed queue rows reconstruct harness state. Consumption and the resulting transcript entry are one transaction.

### Plans

Plan is session state, not an extension-specific side file:

```sql
CREATE TABLE session_plans (
  session_id TEXT PRIMARY KEY REFERENCES sessions(session_id) ON DELETE CASCADE,
  markdown TEXT NOT NULL,
  explanation TEXT,
  revision INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL,
  updated_by TEXT NOT NULL
);
```

The Markdown form is canonical for editing and export. Parsed checklist items are computed and validated on mutation. At most one item is `in_progress`. Optimistic revision checks prevent a stale browser save from overwriting a model update.

### Media and FTS

Vibes' media model is retained with explicit reference tables. Original bytes and thumbnails live in SQLite BLOBs by default. A future external-blob policy can be introduced without changing media IDs.

FTS5 indexes timeline text, session titles, aliases and readable extension-block fallbacks. Tau's provider transcript is not separately indexed because message entries link to timeline records or expose extractable payload text.

### Extension state

```sql
CREATE TABLE extension_state (
  extension_id TEXT NOT NULL,
  scope TEXT NOT NULL,
  scope_id TEXT NOT NULL,
  key TEXT NOT NULL,
  value_json TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL,
  PRIMARY KEY(extension_id, scope, scope_id, key)
);
```

Allowed scopes are `global`, `workspace`, `session` and `connection`. Connection state is normally memory-only; persisted connection rows are rejected unless the host explicitly enables them.

### Import and export

Tau JSONL becomes an interchange format:

* `tau import-session file.jsonl` validates and imports entries in one transaction;
* `tau export-session <id> --format jsonl` reproduces the append-only Tau format;
* HTML export reads SQLite through `SessionStorage`;
* Vibes/Piclaw import maps timelines, aliases, plans and media while preserving source IDs in metadata.

`SqliteSessionStorage` implements Tau's existing `SessionStorage` protocol and becomes the runtime storage used by TUI, print and web modes. JSONL remains an interchange codec and an in-memory/test fixture only; no supported mode writes a live JSONL session after migration, and no operation dual-writes SQLite and JSONL.

## Web transport and events

### SSE envelope

```json
{
  "schema": "tau.web-event/v1",
  "sequence": 1742,
  "workspace_id": "...",
  "session_id": "...",
  "agent_name": "review",
  "run_id": "...",
  "timestamp": "2026-08-04T09:30:00Z",
  "event": {
    "type": "message_delta",
    "delta": "Inspecting "
  }
}
```

Tau event names and serialised fields remain unchanged where possible. Web-only events use a `web.` namespace:

```text
web.connection_ready
web.session_created
web.session_updated
web.session_archived
web.timeline_updated
web.workspace_updated
web.extension_invalidated
web.notification
web.approval_requested
web.metrics_updated
web.plan_updated
web.chat_delivery_updated
```

Sequences are monotonic per server process. Clients reconnect with `Last-Event-ID`; persisted event replay is bounded to meaningful state transitions, while token deltas may require a current snapshot refresh after a long disconnect.

### Fan-out

A central broadcaster uses one bounded queue per connection. Delta and meter events are lossy under pressure; final messages, errors, queue changes, plan changes and delivery state are not. A slow browser cannot stall an agent stream.

## Python web-extension contract

### Design rule

Python defines semantics, state and actions. The web shell owns the DOM. Most extensions return validated declarative component trees. Arbitrary frontend code is confined to sandboxed widgets unless an administrator installs a trusted frontend module.

### Discovery

Installed extensions use Python entry points:

```toml
[project.entry-points."tau.extensions"]
code-review = "tau_code_review:extension"
```

Project-local `.tau/extensions/*.py` files require explicit workspace trust. Extensions load from installed packages or approved project files, never from Tau's source checkout by convention.

### Manifest

```python
manifest = ExtensionManifest(
    id="com.example.code-review",
    name="Code Review",
    version="1.2.0",
    api_version="1",
    web_schema="1",
    permissions=ExtensionPermissions(
        workspace_read=True,
        workspace_write=False,
        session_read=True,
        session_write=False,
        agent_submit=False,
        chat_send=False,
        network_hosts=(),
        web_routes=False,
        sandboxed_widgets=True,
        trusted_frontend=False,
    ),
)
```

Extension IDs are reverse-DNS or stable slug identifiers and cannot impersonate `tau.*` unless bundled by Tau.

### Registration

```python
def register(api: ExtensionAPI) -> None:
    api.tools.register(...)
    api.commands.register(...)
    api.events.subscribe(...)
    api.lifecycle.subscribe(...)
    api.web.panels.register(...)
    api.web.views.register(...)
    api.web.actions.register(...)
    api.web.timeline_renderers.register(...)
    api.web.compose.register(...)
    api.web.status_items.register(...)
    api.web.file_renderers.register(...)
    api.web.settings.register(...)
```

Registration is synchronous and side-effect-free. Database access, background tasks and network calls are forbidden during import/registration. The runtime calls async startup after SQLite and services are ready.

### Lifecycle

```text
registered
startup
workspace_opened
session_loaded
run_started
agent_event
run_finished
session_unloaded
workspace_closed
shutdown
```

Handlers may be `async def`. Event subscribers declare whether they are inline or observed. Inline hooks have strict timeouts and can transform input or authorise a tool. Observers run through owned tasks and cannot delay the agent loop.

### Context

Extensions receive capability-scoped contexts rather than raw application objects:

```python
@dataclass(frozen=True)
class WebContext:
    extension_id: str
    workspace: WorkspaceService
    session: SessionService | None
    timeline: TimelineService
    storage: ExtensionStorage
    web: WebService
    tasks: ExtensionTaskService
    chat: ChatService | None
    permissions: GrantedPermissions
    cancellation: CancellationToken
```

A context exposes only services granted by the manifest and installation policy. Python extensions are trusted code; permissions provide consent, auditability and stable seams, not an in-process security sandbox.

### Contributions

Version 1 supports:

```text
web.shell_slots
web.panels
web.views
web.timeline_renderers
web.compose
web.status_items
web.navigation_items
web.file_renderers
web.editor_tabs
web.settings
web.notifications
web.widgets
```

Host shell slots are stable names:

```text
shell.top_left
shell.top_center
shell.top_right
shell.left_sidebar
shell.right_sidebar
shell.main_overlay
compose.before_input
compose.after_input
compose.footer_left
compose.footer_right
compose.queue
session.dashboard
editor.preview
message.body
message.actions
```

Placement is negotiated. The host may collapse or move a contribution on narrow screens while preserving order and accessibility labels.

### Component schema

Every tree starts with:

```json
{
  "schema": "tau.web/v1",
  "type": "stack",
  "key": "root",
  "children": []
}
```

Version 1 components are:

Layout:

```text
stack, row, grid, split, tabs, section, divider, spacer, scroll
```

Display:

```text
text, markdown, code, badge, icon, image, link, progress,
spinner, key_value, table, tree, callout, sparkline
```

Input:

```text
button, text_input, text_area, select, checkbox, radio_group,
slider, file_picker
```

Tau-specific:

```text
timeline_message, thinking, tool_call, tool_result, context_usage,
model_selector, session_selector, compose_input, queue_stack,
approval_request, plan_editor, system_meters, session_dashboard,
file_reference
```

Components use semantic tones and roles, not arbitrary CSS classes:

```python
Badge(text="3 changed", tone="warning")
Button(label="Refresh", action="git.refresh", variant="secondary")
```

The schema forbids raw event-handler source, inline scripts and unsanitised HTML. Markdown is sanitised by the host. URLs pass a scheme and origin policy.

### Limits

Default limits per rendered tree:

```text
maximum depth: 32
maximum nodes: 2,000
maximum serialised size: 1 MiB
maximum table rows: 500
maximum text field: 256 KiB
maximum action payload: 256 KiB
```

Extensions paginate larger data. Validation failures render a host error boundary and preserve the declared fallback.

### Views and fallbacks

A persistent extension block stores semantic identity, props and a fallback:

```json
{
  "type": "extension_view",
  "extension_id": "test-results",
  "view": "summary",
  "version": 1,
  "props": {"run_id": "abc123"},
  "fallback": {
    "type": "markdown",
    "text": "Tests: 138 passed, 2 failed"
  }
}
```

The component tree itself is not the canonical historical record. On display, the host asks the installed extension to render the semantic block. If the extension is missing or incompatible, the fallback remains readable.

### Actions

Browser interactions call named Python handlers:

```text
POST /api/extensions/{extension_id}/actions/{action}
```

```python
@api.web.action("tests.rerun")
async def rerun(context: WebContext, payload: RerunPayload) -> ActionResult:
    ...
```

`ActionResult` may:

```text
replace a component tree
invalidate one or more views/panels
post a timeline block
show a notification
open or focus an editor file
prefill or submit compose text
switch session
start an owned background operation
```

Every action has a request ID, optional session ID, timeout, cancellation token and idempotency key. Handlers are bounded by a global and per-extension semaphore.

### Invalidation and patches

The default update model is invalidation:

```python
await context.web.invalidate(view="git.status", session_id=context.session.id)
```

SSE tells the browser to refetch the view. This avoids a distributed virtual DOM. Bounded property patches are allowed for high-rate built-ins such as progress and meters, but cannot alter component type or introduce unvalidated nodes.

### Extension storage

```python
await context.storage.get("preferences", scope="session")
await context.storage.set("preferences", value, scope="session", expected_revision=4)
```

The host automatically supplies extension ID and scope ID. Compare-and-swap revisions prevent lost updates. There is no raw SQL extension API in version 1.

### Assets and widgets

Package assets are served through:

```text
/api/extensions/{id}/assets/{content-hashed-path}
```

Resources use `importlib.resources` and strict MIME types.

Sandboxed widgets run in an iframe with no same-origin access and a narrow bridge:

```javascript
tauWidget.action({ name, payload })
tauWidget.submit({ text, mode })
tauWidget.requestRefresh({ key })
tauWidget.close({ reason })
```

Network access, downloads, clipboard and popups are separate capabilities. Widget CSP disallows remote scripts by default.

Trusted frontend modules are an administrator-only tier. They declare an integrity hash and frontend SDK version, and never load merely because a workspace contains JavaScript.

### Web routes

Ordinary extensions use views/actions. An extension requesting `web_routes` may register routes only below:

```text
/api/extensions/{extension_id}/routes/*
```

The host supplies authentication, size limits and error handling. Extensions cannot register top-level paths or static middleware.

### Tool approval policy

The extension contract includes an async tool policy seam:

```python
class ToolExecutionPolicy(Protocol):
    async def authorise(
        self,
        context: ToolPolicyContext,
        call: ToolCall,
    ) -> ToolAuthorisation: ...
```

The loop's default policy approves. Tau Web can require browser confirmation for configured tools, broadcast `web.approval_requested`, await a decision with timeout and consult an SQLite whitelist. The authorisation wait belongs to the target session run and does not block other agents.

## Baseline extension: Compose

Compose is a mandatory host extension because other extensions need its contribution slots and actions. Its visible behaviour should match Piclaw's compose box rather than the simpler Vibes box.

Required features:

* multiline auto-sizing input and Enter/Shift-Enter behaviour;
* per-session history, up/down recall and a 200-entry bound;
* slash-command autocomplete from Tau's command registry and extension commands;
* `@name` session autocomplete and blank-compose `@` session switcher;
* file drag/drop, paste, upload and removable attachment pills;
* workspace file references, message references and active-editor attachment;
* queue stack with reorder, remove, edit/recall and “Steer” actions;
* default busy-submit behaviour configurable as steer or follow-up;
* send button changing to abort while active, including compaction status;
* active model picker, thinking level, provider usage and model context size;
* clickable context pie with green/amber/red thresholds and compact action;
* current named-session control: switch, create, rename, archive, restore and clone;
* connection/reconnection status;
* extension working indicator and status notices;
* optional notifications, pop-out chat and search mode;
* mobile layout matching the web shell rather than desktop-only controls.

Compose contributions:

```python
api.web.compose.register_action(...)
api.web.compose.register_attachment_provider(...)
api.web.compose.register_command_source(...)
api.web.compose.register_footer_item(...)
api.web.compose.register_submit_interceptor(...)
```

Submit interceptors run in priority order under a short timeout. They may reject, transform, route or consume a submission. The built-in leading-`@name` router runs before the ordinary active-session submission.

## Baseline extension: Plan sidebar

Plan is a bundled extension using the public tool, storage, panel and invalidation contracts.

Required behaviour:

* right-side resizable slide-out panel following the active session;
* Markdown checklist editor with a textarea fallback;
* pending `[ ]`, in-progress `[-]` and complete `[x]` markers;
* at most one in-progress item after every mutation path;
* progress bar and collapsed-side meter;
* refresh, reset, save and submit-to-model controls;
* dirty-edit protection when the model updates the plan remotely;
* SQLite revision checks;
* `plan` tool actions `read`, `write`, `edit`, `patch` and `update` compatible with the existing Piclaw contract;
* optional explicit target session, defaulting to the caller's session;
* `web.plan_updated` invalidation events;
* hidden turn context or equivalent session prompt injection without making stale plan text part of the provider prompt cache.

Plan lives in `session_plans`, not generic extension state, because it participates in model context and cross-extension APIs.

## Baseline extension: System meters

The meters extension contributes to `shell.top_right` and registers `/meters`.

A single host sampler reads CPU, RAM, swap and Tau process RSS every two seconds. It keeps a 30-point in-memory series and publishes a snapshot; each browser must not start its own operating-system sampler.

Required fields:

```text
cpu_percent
ram_percent
swap_percent
cpu_series
ram_series
swap_series
process_rss_bytes
process_rss_series_bytes
sample_interval_ms
platform
```

The browser renders CPU/RAM/RSS/swap sparklines, supports collapsed and narrow layouts, pauses polling when hidden and stores enabled/collapsed preference in extension state or local browser preferences as appropriate. Metric events are lossy and coalesced.

On platforms without `/proc`, the sampler uses `os.getloadavg`, `resource`, `psutil` when installed, or marks fields unavailable. Metrics must never fail application startup.

## Baseline extension: Session dashboard

The dashboard is a bundled roll-down panel in `shell.top_center`, toggled by a tab or backtick when focus is outside an editor/form.

It reads the agent pool and SQLite repositories through public services. It does not inspect process globals or query provider catalogues.

Each tile includes:

* `@agent_name` and durable session identity;
* active/working/streaming/idle state;
* last activity and workspace;
* latest assistant summary;
* live preview with priority: draft, thinking, current tool, saved summary;
* context-window usage;
* model label when space permits;
* click-to-switch and Ctrl/Cmd-click new-tab behaviour.

Responsive capacity matches Piclaw's baseline:

```text
below 760 px: 2 columns, 4 sessions
760-1079 px: 3 columns, 6 sessions
1080 px and above: 4 columns, 8 sessions
```

Full state refresh occurs every 15 seconds while open; active previews update every three seconds or from SSE invalidations; footer age updates locally each second. The dashboard supports more than eight sessions through pagination or a full session manager view.

## Vibes adaptation

The following Vibes assets are retained and renamed around Tau concepts:

```text
aiohttp application shell
Preact timeline and compose foundations
workspace tree, watcher and file CRUD
CodeMirror editor and pop-outs
media upload, thumbnails and previews
SQLite FTS concepts
SSE connection and responsive PWA shell
OpenGraph previews where enabled
```

The following are removed:

```text
pi_client.py
acp_client.py
ACP protocol parsing
Pi RPC parser and subprocess management
Vibes follow-up state
Vibes agent lifecycle
Vibes slash-command implementation
```

Agent-facing Vibes names become Tau names:

```text
agent response -> session run/final assistant message
agent draft -> message_delta
agent thought -> thinking_delta
agent status -> run status
agent id -> session id or agent name
restart agent -> new session or runtime reload
```

The frontend is migrated incrementally, but the public `/api/v1` contract uses Tau naming from its first committed version. Temporary Vibes compatibility routes are private and removed before release.

## HTTP API v1

Representative endpoints:

```text
GET    /api/v1/sessions
POST   /api/v1/sessions
GET    /api/v1/sessions/{session_id}
PATCH  /api/v1/sessions/{session_id}
DELETE /api/v1/sessions/{session_id}
POST   /api/v1/sessions/{session_id}/restore
POST   /api/v1/sessions/{session_id}/clone
POST   /api/v1/sessions/{session_id}/prompt
POST   /api/v1/sessions/{session_id}/cancel
GET    /api/v1/sessions/{session_id}/queue
PATCH  /api/v1/sessions/{session_id}/queue
POST   /api/v1/sessions/{session_id}/compact
GET    /api/v1/sessions/{session_id}/context
GET    /api/v1/sessions/{session_id}/tree
POST   /api/v1/sessions/{session_id}/branch
GET    /api/v1/models
PUT    /api/v1/sessions/{session_id}/model
PUT    /api/v1/sessions/{session_id}/thinking
POST   /api/v1/chat/deliver
GET    /api/v1/events
GET    /api/v1/timeline
GET    /api/v1/search
/api/v1/workspace/*
/api/v1/media/*
/api/v1/extensions/*
```

Mutating requests accept idempotency keys. Errors use a stable JSON envelope with code, message, details and request ID.

## Security

Tau's tools make the web server equivalent to remote shell access. Safe defaults are therefore stricter than Vibes' current defaults:

* bind to `127.0.0.1` by default;
* same-origin CORS by default;
* require explicit acknowledgement and authentication for non-loopback binding;
* use secure cookies, CSRF protection and origin checks;
* rate-limit login, prompt, upload, action and chat-delivery endpoints;
* cap request, component, media and SSE queue sizes;
* never expose provider credentials or environment variables through extension contexts;
* apply Linux/macOS sandbox policy before starting the web runtime;
* require explicit trust for workspace Python extensions;
* audit extension installation, permission grants and chat deliveries.

SQLite content is application data and may contain secrets from conversations. File permissions must be owner-only, backups must be treated as sensitive, and no raw database download endpoint is enabled by default.

## Configuration and packaging

Web dependencies should be optional for constrained Tau installations:

```toml
[project.optional-dependencies]
web = [
  "aiohttp>=3.13,<4",
  "aiosqlite>=0.22,<1",
  "pillow>=12,<13",
  "watchfiles>=1.1,<2",
]
```

Command:

```text
tau web --cwd PATH --host 127.0.0.1 --port 8080
```

Tau's custom build backend must emit optional dependency metadata and include selected static assets. Source maps and development bundles are excluded from release wheels. Web imports remain lazy so a-Shell/mobile and ordinary TUI use do not import aiohttp or Pillow.

## Recovery and shutdown

On startup:

* acquire a process lock for the database path so two Tau server processes cannot assume the single-writer role for the same store;
* run SQLite migrations under an exclusive migration lock;
* mark stale `running` runs as interrupted;
* load queued messages;
* load sessions lazily;
* let `CodingSession` repair unmatched tool calls and commit repairs;
* start metrics and workspace services;
* announce `web.connection_ready` only after repositories are ready.

On shutdown:

* stop accepting new prompts;
* cancel or drain runs according to timeout policy;
* close extension task groups;
* close providers;
* flush the SQLite writer;
* checkpoint WAL opportunistically;
* close read connections and aiohttp.

A browser disconnect does not restart an agent or discard a session.

## Testing

### Contract tests

* component-schema validation and fallbacks;
* manifest and permission negotiation;
* action idempotency, cancellation and limits;
* extension state scopes and revision conflicts;
* widget bridge/CSP tests;
* Tau event to SSE serialisation.

### SQLite tests

* migrations from every released schema;
* atomic entry/leaf updates;
* queue consumption transactionality;
* active alias uniqueness and archive/reuse;
* chat delivery deduplication;
* WAL reader/writer concurrency;
* crash recovery and interrupted tool repair;
* JSONL round-trip import/export;
* FTS and media reference cleanup.

### Async multi-agent tests

Use fake providers with barriers to prove:

* two sessions stream concurrently;
* one session's turn lock does not block another;
* steering and follow-ups target only the addressed session;
* cancellation is isolated;
* per-path file locks prevent conflicting writes;
* global semaphores enforce configured bounds;
* chat delivery to a busy target does not deadlock;
* cyclic chat ancestry and rate limits are enforced;
* shutdown cancels owned tasks without leaks.

### Baseline extension tests

* compose parity for mentions, session switcher, queue, context and controls;
* Plan mutation compatibility and dirty-state protection;
* meter sampling/coalescing and platform fallbacks;
* dashboard preview priority, responsive capacity and navigation;
* browser accessibility and keyboard behaviour;
* Playwright coverage in Chromium and WebKit at phone, tablet and desktop widths.

Vibes' current 388 Python tests are preserved or deliberately replaced with Tau-native equivalents. Tau's existing suite remains green throughout.

## Delivery phases

### Foundation

Introduce the SQLite repositories, `SqliteSessionStorage`, reusable session factory and `AsyncAgentPool`. Prove parallel fake-agent runs and JSONL import/export before adding a browser.

### Native web path

Import the Vibes shell, remove Pi/ACP clients and connect one then several Tau sessions through typed events and SSE. Add session creation, aliases, queue, cancel, context, model and thinking APIs.

### Extension contract

Add manifests, component schema, views, actions, scoped storage, owned tasks, assets and invalidation. Ship one small diagnostic extension to validate the public API before converting large UI features.

### Baseline parity

Ship Compose, Plan, meters and session dashboard against the same public services. Add the `chat` tool and leading-mention routing. This is the minimum useful multi-agent release.

### Media, approval and hardening

Add native attachment tools, multimodal user blocks, browser tool approval, authentication, audit records, sandbox integration and migration utilities.

### Broader extension surface

Add file renderers, editor annotations, sandboxed widgets and, only when a real extension cannot use the declarative contract, the trusted frontend SDK.

## Release gates

The first public release must satisfy all of these:

* SQLite is the sole live store and passes crash/recovery tests;
* at least two Tau sessions execute provider streams concurrently;
* aliases are durable, unique and usable from Compose and `chat`;
* queue, steer, cancel and chat delivery have no cross-session leakage;
* Compose, Plan, meters and dashboard meet the specified baseline;
* extension trees and actions are validated and bounded;
* non-loopback startup is protected;
* the TUI and print modes remain usable without web dependencies;
* macOS and Linux sandbox behaviour is documented and tested;
* migration and export paths are reversible.

## Decisions recorded

* Tau owns the agent loop and session semantics; Vibes contributes the web product.
* The web runtime embeds Tau and does not spawn Pi or ACP agents.
* SQLite is the only durable live store.
* Tau's append-only entry and branch model is retained in SQLite.
* `@name` is a durable active-session address shared by Compose and `chat`.
* Parallelism is per session under asyncio with explicit global resource bounds.
* Tau's typed events are canonical; web-only events are namespaced.
* Python extensions normally return declarative components.
* Sandboxed widgets are the custom-rendering escape hatch.
* Trusted frontend modules are opt-in and administrator-installed.
* The browser shell owns DOM and security; extensions own semantics and actions.
* Compose, Plan, meters and session dashboard are baseline contract users, not private one-off integrations.
