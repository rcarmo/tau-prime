# Web

Tau has **two different browser-facing modes**.

## Optional install

`pyproject.toml` defines a `web` extra with `aiohttp`, `pillow` and `watchfiles`.

```sh
python -m pip install "tau-prime[web]"
# or from a checkout
python -m pip install ".[web]"
```

That extra is for **Tau Web** (`tau web`).

`tau --web` is separate: it runs the normal Textual TUI through Textual's own web server command and requires `textual-web` or `textual-serve` on `PATH`.

## Modes and exact options

| Mode | What it starts | Exact web-specific options from source | Defaults |
| --- | --- | --- | --- |
| `tau web` | Tau Web HTTP server, browser shell, REST API, SSE | `--cwd PATH`, `--host HOST`, `--port PORT`, `--database PATH` | host `127.0.0.1`, port `8080`, cwd `Path.cwd()`, database `TauPaths().home / "tau.sqlite3"` |
| `tau --web` | Textual TUI via Textual's separate web server | `--web`, `--web-host HOST`, `--web-address HOST`, `--host HOST`, `--web-port PORT` | host `127.0.0.1`, port `8000` |

Examples:

```sh
tau web
tau web --cwd /path/to/worktree --host 127.0.0.1 --port 8080 --database /path/to/tau.sqlite3
tau --web
tau --web --web-host 127.0.0.1 --web-port 8000
```

`tau --web` also accepts the usual TUI flags such as `--cwd`, `--resume`, `--new-session`, `--provider`, `--model` and `--auto-compact-threshold`.

Do not confuse the two: the REST routes, middleware, PWA assets, auth and SSE behaviour below apply to `tau web`, not to Textual's separate server.

## Shared database and live-process model

Tau's live durable store is SQLite, shared in format and default path across normal TUI sessions, print mode, `tau sessions`, `tau --resume`, `tau web`, and indirectly `tau --web` because it runs the normal TUI.

Default live database path:

- `~/.tau/tau.sqlite3`
- `$TAU_HOME/tau.sqlite3` if `TAU_HOME` is set

Inside one process, Tau uses one write connection, a serialised writer queue, a default pool of four read-only connections, and WAL mode.

Across processes, the database is **single-owner**. Opening it acquires a sibling `tau.sqlite3.lock` advisory lock; a second live Tau process against the same database raises `DatabaseLockedError` instead of waiting. So the modes share one durable store, but they are not a multi-process shared-writer deployment.

On open, Tau applies migrations, runs `PRAGMA quick_check`, and marks stale `session_runs` rows left as `running` to `interrupted`. `GET /api/health` reports `recovered_runs` once services have started.

## Security, auth and request handling

The current `tau web` CLI exposes only `--cwd`, `--host`, `--port` and `--database`.

Real `WebConfig` settings exist in source, but they are **not current CLI flags**: `auth_token`, `allowed_origins`, `max_request_bytes`, `max_active_runs`, `sse_replay_capacity`, `sse_client_capacity`, `sse_heartbeat_seconds`.

### Bearer auth

If `WebConfig.auth_token` is set, middleware requires:

```text
Authorization: Bearer <token>
```

Auth is skipped for `/api/health` and the frontend shell paths `/`, `/index.html`, `/manifest.webmanifest`, `/sw.js` and `/static/*`. Failure returns `401` with `WWW-Authenticate: Bearer`.

### Origin and CSRF

For unsafe methods:

- if there is **no** `Origin` header, the request is allowed
- if `Origin` is present, it must match the request origin or be in `allowed_origins`
- if `Origin` is present, `X-Tau-CSRF: 1` is required

So CSRF handling is aimed at browser-originated unsafe requests, not at non-browser API clients.

### Request IDs and size limits

Every response gets `X-Request-ID`; a valid incoming value is preserved, otherwise Tau generates one.

Default request-size limit is `16 MiB` (`16 * 1024 * 1024` bytes) via `client_max_size`. That same limit also bounds JSON bodies, `/api/files` text-file reads and multipart `/api/media` uploads. Oversized requests return structured `413` JSON errors.

## API surface under the actual `/api` prefix

All current API routes live under `/api`.

- Health: `/api/health`
- Sessions and aliases: `/api/sessions`, `/api/sessions/{session_id}`, `/api/sessions/{session_id}/restore`, `/api/aliases/{address}`
- Timeline and context: `/api/sessions/{session_id}/entries`, `/messages`, `/timeline`, `/branches`, `/branches/select`, `/context`
- Runs and queue: `/api/sessions/{session_id}/runs`, `/api/runs/{run_id}`, `/api/runs/{run_id}/cancel`, `/abort`, `/retry`, `/api/sessions/{session_id}/queue`, `/api/runs/{run_id}/messages`, `/api/runs/{run_id}/queue/{kind}/dispatch`
- Metadata and search: `/api/settings`, `/api/models`, `/api/commands`, `/api/sessions/{session_id}/model`, `/thinking`, `/plan`, `/usage`, `/api/search`
- Workspace and media: `/api/files`, `/api/media`, `/api/media/{media_id}`, `/api/media/{media_id}/content`
- Events: `/api/events`

There are currently **no** public `/api/extensions/...` routes.

## SSE cursors, replay and recovery

`GET /api/events` serves canonical SSE with an optional `?session_id=...` filter.

Current behaviour from the route and broker code:

- SSE `id:` fields are integer cursors
- event names are namespaced, for example `tau.agent.message_delta`
- full-state fallback is sent as `tau.snapshot`
- reconnect resume uses the `Last-Event-ID` header
- malformed or negative `Last-Event-ID` values return `400`

Resume rules are exact:

- if the cursor is retained in replay history, Tau replays the missing events
- if the cursor is stale or ahead of the current broker cursor, Tau falls back to `tau.snapshot`

Current snapshot caps in route code are 100 sessions, 100 timeline items, 100 runs and 100 queue items.

Default SSE tuning in `WebConfig` is replay capacity `512`, per-client buffer capacity `64`, and heartbeat interval `15` seconds. Slow subscribers may be closed if their per-client buffer overflows; low-priority deltas may be coalesced before that happens.

The bundled browser shell reconnects automatically with exponential back-off from 1s up to 16s and re-sends `Last-Event-ID`.

## PWA and frontend shell

Tau Web serves these public shell assets: `/`, `/index.html`, `/manifest.webmanifest`, `/sw.js`, `/static/app.css`, `/static/app.js`, `/static/live-ui.js`, `/static/extension-ui.js`.

The manifest sets `start_url: "/"`, `scope: "/"` and `display: "standalone"`. The shell registers `/sw.js` as a service worker.

Current offline support is limited: the service worker caches only the shell assets above. It does **not** cache API responses, session state, timeline data or media blobs for offline use.

## Workspace path confinement

`/api/files` is confined to `WebConfig.cwd`, which defaults to the server's working directory.

The file browser rejects absolute paths, `..` traversal, symlink traversal, binary files and non-UTF-8 text files. Only directories and regular UTF-8 files are readable there, and reads are bounded by `max_request_bytes`.

Important distinction: session records may store their own `workspace_root`, but `/api/files` browsing is rooted in **server `cwd`**, not in each session's recorded workspace root. Creating or importing a session does not widen file-browser access.

## Declarative extension UI: current status

There is a real declarative web UI contract in `tau_extensions.web`, and the shell ships an `extension-ui.js` renderer with six slots: `compose_above`, `compose_below`, `sidebar`, `timeline_before`, `timeline_after`, `dashboard`.

The SQLite schema also includes persistent `extension_state` storage.

However, Tau Web does **not** currently expose public extension HTTP routes or a built-in end-user activation path for extension views and actions. The renderer and contracts exist, but server-side extension UI integration is not yet a complete user feature.

Current declarative UI limits enforced in source:

- canonical view size `64 KiB`
- action payload size `8 KiB`
- maximum depth `12`
- maximum node count `256`
- maximum text size `16 KiB`
- maximum table size `50` rows and `20` columns

## Non-loopback cautions and known limits

- Default binding is deliberately loopback-only: `127.0.0.1`.
- If you bind `tau web` to a non-loopback address such as `0.0.0.0`, the frontend shell and `/api/health` remain public.
- Without a programmatically supplied `auth_token`, the API is fully open on that interface.
- Even with bearer auth enabled, frontend assets remain public by design.
- The current CLI does not expose flags for bearer auth, allowed origins, request-size tuning or SSE tuning.
- The live SQLite store is single-owner per database path; another live Tau process on the same file fails rather than joining a shared writer.
- PWA support is shell-only, not offline API or offline session replay.
- `tau --web` is Textual's separate server path; do not assume Tau Web's routes, middleware or security model apply there.
