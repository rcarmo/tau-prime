# API

Exact HTTP route/method index for the current `tau_web` aiohttp app, taken from `src/tau_web/app.py` and `src/tau_web/routes/*.py`.

This page is intentionally an index, not a schema reference. For runtime behavior and deployment context, see [web](./web.md), [extensions](./extensions.md), and [architecture](./architecture.md).

## Base path, auth, and mutations

- Most API routes live under `/api`.
- Registered non-`/api` routes also exist at `/meters`, `/dashboard`, `/`, `/index.html`, `/manifest.webmanifest`, `/sw.js`, and `/static/{filename}`.
- If `WebConfig.auth_token` is set, requests must send `Authorization: Bearer <token>`.
- Bearer auth is skipped for `/api/health` and frontend shell paths (`/`, `/index.html`, `/manifest.webmanifest`, `/sw.js`, `/static/*`).
- Unsafe methods (`POST`, `PUT`, `PATCH`, `DELETE`, etc.) are allowed without CSRF if there is no `Origin` header.
- If an unsafe request includes `Origin`, that origin must match the request origin or be listed in `allowed_origins`, and it must send `X-Tau-CSRF: 1`.
- Every response carries `X-Request-ID`; a valid incoming `X-Request-ID` is preserved.

## Structured errors

Tau returns JSON errors in this shape:

```json
{
  "error": {
    "code": "bad_request",
    "message": "...",
    "request_id": "..."
  }
}
```

Notes:

- `401` bearer failures also include `WWW-Authenticate: Bearer`.
- Oversized requests are structured `413` responses with `error.code = "request_entity_too_large"`.
- `PUT /api/sessions/{session_id}/plan` can also return `409` with the same `error` object plus a top-level `current` plan snapshot.
- Widget-action and extension-route failures keep the same `error` object shape, with route-specific `code` values.

## SSE, replay, and reconnect

- `GET /api/events` serves `text/event-stream`.
- Optional filter: `?session_id=<session_id>`.
- Reconnect uses the `Last-Event-ID` request header; it must be a non-negative integer.
- If the cursor is still in replay history, Tau replays missed events.
- If the cursor is stale or ahead of the current broker cursor, Tau falls back to a `tau.snapshot` event.
- Heartbeats are sent as SSE comments: `: heartbeat`.
- Current snapshot caps are 100 sessions, 100 timeline items, 100 runs, and 100 queue items.
- Replay and per-client buffers are bounded; slow subscribers can be closed, and some low-priority delta events may be coalesced.

## Bounded payload caveats

- Global request size is bounded by `client_max_size` (`max_request_bytes`, default `16 MiB`).
- `/api/files` reads are bounded by the same limit.
- Multipart `/api/media` uploads are bounded by the same limit.
- `/api/extensions/routes/...` accepts JSON bodies only, with request and response bodies capped at `1 MiB`.
- `/api/extensions/widgets/.../actions/...` accepts JSON only, with request payloads capped at `8 KiB` and action results capped at `64 KiB`.

## Route index

### Health

- `GET /api/health`

### Sessions

- `GET /api/sessions`
- `POST /api/sessions`
- `GET /api/sessions/{session_id}`
- `PATCH /api/sessions/{session_id}`
- `DELETE /api/sessions/{session_id}`
- `POST /api/sessions/{session_id}/restore`

### Aliases

- `GET /api/aliases/{address:.+}`

### Branches

- `GET /api/sessions/{session_id}/branches`
- `POST /api/sessions/{session_id}/branches/select`

### Messages

- `GET /api/sessions/{session_id}/messages`
- `GET /api/sessions/{session_id}/entries`
- `GET /api/sessions/{session_id}/timeline`

### Runs

- `GET /api/sessions/{session_id}/runs`
- `POST /api/sessions/{session_id}/runs`
- `GET /api/runs/{run_id}`
- `POST /api/runs/{run_id}/cancel`
- `POST /api/runs/{run_id}/abort`
- `POST /api/runs/{run_id}/retry`

### Queue

- `GET /api/sessions/{session_id}/queue`
- `POST /api/sessions/{session_id}/queue`
- `POST /api/runs/{run_id}/messages`
- `POST /api/runs/{run_id}/queue/{kind}/dispatch`

### Events

- `GET /api/events`

### Models

- `GET /api/models`
- `PATCH /api/sessions/{session_id}/model`

### Thinking

- `PATCH /api/sessions/{session_id}/thinking`

### Context

- `GET /api/sessions/{session_id}/context`

### Commands

- `GET /api/commands`

### Usage

- `GET /api/sessions/{session_id}/usage`

### Files

- `GET /api/files`

### Search

- `GET /api/search`

### Plans

- `GET /api/sessions/{session_id}/plan`
- `PUT /api/sessions/{session_id}/plan`

### Media

- `GET /api/media`
- `POST /api/media`
- `GET /api/media/{media_id}`
- `GET /api/media/{media_id}/content`
- `GET /api/media/{media_id}/thumbnail`
- `DELETE /api/media/{media_id}`

### Settings

- `GET /api/settings`

### Meters

- `GET /meters`

### Extensions

#### Frontend-modules

- `GET /api/extensions/frontend-modules`

#### Widgets

- `GET /api/extensions/widgets/{extension_id}/{widget_id}`

#### Actions

- `POST /api/extensions/widgets/{extension_id}/{widget_id}/actions/{action}`

#### Assets

- `GET /api/extensions/assets/{extension_id}/{path:.*}`

#### Routes

- `* /api/extensions/routes/{extension_id}`
- `* /api/extensions/routes/{extension_id}/{path:.*}`

### Other registered routes

- `GET /api/sessions/{session_id}/approvals`
- `POST /api/approvals/{approval_id}`
- `GET /api/audit`
- `GET /dashboard`
- `GET /`
- `GET /index.html`
- `GET /manifest.webmanifest`
- `GET /sw.js`
- `GET /static/{filename}`

## Representative curl examples

```sh
curl http://127.0.0.1:8080/api/health

curl \
  -H "Authorization: Bearer $TAU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"provider_name":"anthropic","model":"claude-sonnet"}' \
  http://127.0.0.1:8080/api/sessions

curl \
  -H "Authorization: Bearer $TAU_TOKEN" \
  -H "Origin: http://127.0.0.1:8080" \
  -H "X-Tau-CSRF: 1" \
  -H "Content-Type: application/json" \
  -d '{"content":"Summarize the current plan."}' \
  http://127.0.0.1:8080/api/sessions/$SESSION_ID/runs

curl -N \
  -H "Authorization: Bearer $TAU_TOKEN" \
  -H "Last-Event-ID: 42" \
  "http://127.0.0.1:8080/api/events?session_id=$SESSION_ID"
```