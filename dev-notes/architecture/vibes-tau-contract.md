# Vibes → Tau integration boundary

Pinned Vibes source is recorded under src/tau_web/vibes/source-revision.txt.
The imported app is not wired to Tau yet. New tau-client.js is a unit-tested
transport foundation, not a claim that session UI integration is complete.

| Surface | Vibes assumption | Tau mapping / required work |
|---|---|---|
| Sessions | /sessions, id/name, synthetic default | /api/sessions, session_id/title; explicitly choose real initial session |
| Create | name/parent only | provider_name/model required; obtain real setup selection; branching is separate |
| Rename/delete | PATCH name / DELETE | PATCH title / explicit archive route; label Archive, never imply deletion |
| Models | /agent/models, session model-state | /api/models and session provider/model/thinking; inspect catalogue shape before projecting |
| Timeline | posts, before pagination | /api/sessions/{id}/timeline, after cursor; pagination cannot be renamed blindly |
| Send | /agent/{id}/message, media_ids/mode | Tau session messages/runs; translate attachments and queue/run semantics explicitly |
| SSE | global Vibes named events | /api/events canonical envelopes with session/run/sequence/payload; retain cursor/recovery and dedupe |
| Media | /media/upload plus direct URLs | use authenticated Tau asset routes; inspect IDs and upload format |
| Workspace/editor | writable file REST APIs | audit Tau workspace capabilities; no optimistic fake writes |
| Terminal | direct /terminal/session fetch and WebSocket | capability must be false until a real backend exists; bypasses api.js today |
| Preferences | ETag model pins | preserve real persistence/concurrency or explicitly disable unsupported preferences |
| Plan/approvals | not a drop-in Vibes equivalent | integrate Tau-specific APIs without losing conflicts or authorization |

Transport ownership: adapt api.js through a Tau client/projection layer, not a
global fetch monkeypatch. Direct terminal/media/WebSocket access must also be
accounted for. Unit tests check request/response projections; actual routes and
browser workflows remain separate gates. Preserve imported component ownership.

Checkpoint: four Tau client unit tests pass (eight assertions), lint passes.
Session list/create/rename transport scaffold is intentionally not connected to
the app until initial-session and catalogue decisions are implemented together.

Model adapter checkpoint: Tau `/api/models` is an observed-session catalogue,
not provider discovery. Projection retains the current model, deduplicates pairs
and omits unsupported pricing/context/reasoning capabilities. Model mutations
use the loaded session revision; 409 errors propagate without retries. Six
transport tests (14 assertions), lint and frontend build pass. Still not wired
to production; reasoning controls and initial selection need integration.

API wiring checkpoint: imported api.js now delegates session listing/rename and
model listing/state/change to Tau transport, reading the existing auth token.
Creation without provider setup and deletion explicitly fail instead of calling
wrong Vibes endpoints. These are interim integration errors, not finished UI:
creation controls need setup, deletion must become Archive, initial default and
timeline/SSE are still pending. Ten tests/31 assertions, lint and build pass.

Persisted timeline checkpoint: both imported timeline functions now use the Tau
adapter. Ascending backend pages are scanned into newest-first UI pages with
explicit older-message boundaries and monotonic cursor validation. Scan cap
fails visibly rather than truncating silently; a reverse-page backend endpoint
is preferable before large-history performance signoff. Current projection is
text/role/identity only: tool blocks/media and live SSE remain unimplemented.
Twelve tests/37 assertions, lint and build pass; not end-to-end acceptance.

Initial selection checkpoint: imported app starts without a synthetic session,
loads actual active sessions and preserves ?session= selection. Missing explicit
sessions surface an error rather than selecting another conversation. Timeline
startup waits for selection. Fourteen tests/42 assertions, lint and build pass.
Browser lifecycle validation and remaining default-dependent agent/event paths
are pending; this is not a production-ready startup claim.

First Chromium integration smoke executed against imported app and deterministic
Tau session/timeline fixtures. It caught an undefined startup generation ref and
an incompatible model-state shape; both corrected. No page errors after fixes;
real session label, persisted text and model label render. Null-session polling
is gated. Fourteen unit tests, build/lint and browser smoke pass. The smoke
explicitly reports nine unimplemented endpoint families, with 501 fixture
responses: not a full passing workflow or live backend/SSE validation.

Text submit checkpoint: imported sendAgentMessage now uses Tau durable runs when
idle and FIFO follow-up queue when a run is active; explicit steer is queued as
steer. HTTP rejection throws before the composer success/clear path. Unsupported
attachments/commands/thread submission fail explicitly. Sixteen tests/51
assertions, lint/build pass. Busy detection and submission are separate requests;
server contention errors must remain visible, not retried automatically. Actual
composer send/clear browser tests and live SSE still required before release.

Composer browser checkpoint: Chromium desktop and WebKit phone exercise actual
imported textarea/Enter submission. Accepted Tau run POST clears the draft;
409 conflict shows its message and preserves rejected draft text. Both report
zero page errors. These use deterministic route fixtures, not real agent runs.
Unimplemented endpoint requests remain printed by the smoke harness. Unit suite
16 passed; lint passed. Smoke supports TAU_SMOKE_ENGINE and TAU_SMOKE_PHONE.

Authenticated SSE transport foundation: tau-events.js uses fetch streaming,
bearer token, Last-Event-ID reconnect and abortable reader lifecycle. Incremental
UTF-8/CRLF/comment decoding and reconnect/disconnect tests pass (18 total tests,
56 assertions; lint pass). Not connected to app yet: canonical event projection,
snapshot recovery, deduplication and live-delta presentation remain required.

SSE app checkpoint: production candidate app now instantiates TauEventStream,
not Vibes SSEClient. Snapshot refreshes sessions/persisted timeline; selected-
session message start/delta/end updates draft and reloads persisted results.
Bounded event-id replay suppression retains the latest cursor. Nineteen tests/
58 assertions, lint/build and Chromium fixture smoke pass. Snapshot fixture
closes its stream, so Reconnecting remains expected; this is not live SSE
acceptance. Run status/cancel, tools/approvals, reset snapshots and stronger
lifecycle/race tests remain pending. Old Vibes handlers remain until replacement
coverage permits removal.

Run/queue read checkpoint: imported status and queue functions use Tau routes.
Only pending/running runs become active turns. Queue projection preserves backend
order and identity; unsupported reorder/promote/remove controls are hidden for
Tau items. Twenty unit tests/62 assertions, lint/build pass. Active-status UI,
queue browser assertions and actual cancellation remain pending.

Queue browser checkpoint: Chromium desktop and WebKit phone verify two FIFO
messages in backend order and no visible queue mutation actions. Browser checks
caught classic CSS overriding HTML hidden; local display override fixes that
without editing vendor CSS. Accepted/rejected composer checks still pass with
queue populated, no page errors. Remaining missing requests now exclude queue
and agent status. Twenty unit tests and lint/build pass. Fixtures are not live
backend evidence; final integration remains open.

Cancellation checkpoint: Tau-specific run control reads the selected session's
active run and POSTs its actual ID to /api/runs/{id}/cancel. Pending/error states
are explicit; status is reloaded after acknowledgement. Chromium desktop/WebKit
phone verify the control appears, cancellation POST occurs, control disappears
and composer draft survives. Build/lint and 20 unit tests pass. Browser fixtures
are not runtime cancellation evidence; real backend integration still required.

Real-backend baseline checkpoint: live-backend.mjs launches the existing isolated
Tau browser server plus the local Vibes proxy. Real session POST returns 201;
real SSE snapshot streams through proxy; Chromium loads actual session/model/
timeline without API route mocks or page errors. Full Python baseline: 1321
passed. No agent provider run attempted. Rui requested OpenRouter free models;
this instance has neither configured credentials nor reachable Smith/Flint chat
transport, so provider execution remains blocked, not passed.

Context reads now use Tau context endpoint and expose only actual structural
counts/leaf identity: no invented tokens, cost, context occupancy or compaction
action. 21 unit tests/65 assertions, lint/build and real-backend startup pass.

Session-create defaults checkpoint: imported creation now loads actual Tau
onboarding default_provider/default_model and submits those explicit values.
Missing configuration rejects before POST and leaves the dialog error path intact.
No inferred catalogue choice or fabricated provider. Branch creation remains
unsupported and explicit. 23 unit tests/69 assertions, lint/build pass; provider
setup UI and browser creation workflow still pending.

Provider setup UI checkpoint: imported app can read/save Tau onboarding defaults
through a focused modal. Optional credential is never placed in browser storage;
blank credential is omitted so existing credentials remain. Chromium desktop and
WebKit phone verify prefill, save payload, dismissal and composer draft survival.
23 existing unit tests, lint/build pass. This modal still needs complete inert-
background/accessibility and failure-path coverage before production switch.

Provider modal lifecycle checkpoint: sibling branches up to body are made inert
and original inert values restored on unmount. Initial focus targets an enabled
control. Chromium desktop/WebKit phone verify background inertness, rejected
save retains editable values, successful retry, focus return and composer draft
preservation. 23 unit tests, lint/build pass. Comprehensive accessibility matrix
and nested/concurrent modal review remain pending.

Archive adapter checkpoint: archived state updates use explicit Tau archive/
restore POST routes, not DELETE. Archiving selected session chooses another
actual active session or clears selection/URL if none remain, rather than using
synthetic default. Unsupported pin/delete callbacks removed. 24 unit tests,
lint/build and real-backend startup pass. Archive UI edge cases and stale
selection races still need browser coverage; not marked complete.

Correction from real archive browser test: Tau archives via DELETE /api/sessions/
{id}, not POST /archive. Restore is POST /restore. Earlier contract notes and
fixture assertions claiming POST archive were wrong and are superseded here.
Real mutations also exposed missing X-Tau-CSRF and proxy Origin mismatch. Client
now sends Tau CSRF header; localhost proxy rejects foreign origins and translates
its own validated origin to backend origin. Real browser archive/restore now
passes and verifies database-facing API state and selection URL clearing.
25 unit tests, lint/build pass. This corrects fixture-only blind spots.

Workspace tree checkpoint: imported explorer reads real Tau /api/files listings
through bounded-depth projection, filters hidden names when requested and omits
symlink/special nodes rather than treating them as writable files. Real-backend
Chromium confirms seeded README.md appears. 26 unit tests, lint/build and live
startup/archive checks pass. Preview/edit/upload and workspace visibility writes
remain unmapped; directory visibility is not editor support.

Correction to dccf5a4 checkpoint: newly added README visibility assertion initially
FAILED; shell chaining incorrectly allowed the success note/commit afterward.
The imported explorer expands '.' by default, while projection supplied an empty
root path. Root normalized to '.'; rebuilt and reran live-backend check including
README visibility successfully, followed by 26 unit tests and lint. Earlier
success claim applies only after this correction, not to dccf5a4 itself.

Read-only preview checkpoint: /api/files UTF-8 content maps to bounded plain-text
preview, dropping incomplete trailing UTF-8 at truncation. Does not infer safe
Markdown HTML or writable editor capability. Save API explicitly rejects instead
of invoking missing Vibes endpoint. Real backend Chromium selects README and
verifies seeded content; 27 unit tests and lint/build pass. Editor affordances,
other workspace mutation controls and richer media remain to be reconciled.

Workspace capability checkpoint: Tau opts imported explorer into readOnly mode.
Create/delete/edit/download/upload buttons hidden; rename/delete/drop/drag-start
handlers gated and editor callback absent. Browsing/preview live test, lint/build
pass. Broader keyboard/touch and capability assertions still needed before
production; these gates describe current Tau API, not a request to add file-write
endpoints or discard the imported editor source.

Search transport checkpoint: imported searchPosts delegates to Tau FTS, retaining
entity/session IDs and text without invented post timestamps. Unsupported image/
attachment/thread/root filters and offsets fail explicitly. 28 unit tests,
lint/build pass. Browser rendering, source-session navigation and disabling
unsupported filter controls remain pending; not complete Search UX.

Search browser checkpoint: Chromium desktop/WebKit phone submit composer search,
render matched FTS text and verify explicit source-session link. Unsupported
branch-family/image/attachment filter controls removed/hidden. Null timestamps
no longer render epoch dates. 28 unit tests, lint/build pass. Real FTS fixture
seeding, navigation draft handling and search-error presentation remain pending.
