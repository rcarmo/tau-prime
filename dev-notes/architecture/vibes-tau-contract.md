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

Search error checkpoint: failed requests now render a visible alert rather than
only empty results/console output; new requests clear prior error and stale
responses retain generation/session guards. Chromium desktop/WebKit phone test
400 failure followed by successful retry and alert removal. 28 unit tests,
lint/build pass. Remaining main integration gates are unchanged.

Plan transport checkpoint: plan read/save methods use Tau markdown and caller-
supplied expected_revision. Conflict errors retain code/current server plan for
explicit UI reconciliation; no retry or automatic revision replacement. Unit
test checks 409 payload, original submitted draft/revision and CSRF. 29 unit
tests, lint/build pass. Plan editor/state UI still pending; transport does not
claim mounted draft or conflict UX parity.

Plan UI checkpoint: explicit Plan disclosure with per-session in-memory draft,
revision save and confirmed force reload. Loads preserve cached dirty drafts;
409 retains edits and explains conflict. Real-backend Chromium opens Plan,
saves markdown through CSRF-protected route and verifies persisted markdown.
29 unit tests, lint/build pass. Conflict/reload/session-switch browser matrix,
styling/accessibility and remote plan-update notifications remain pending.

Real Plan conflict checkpoint: Chromium and WebKit against actual Tau server
save a plan, apply an independent API revision, reject stale browser save with
409, retain local draft, decline reload without loss, then confirm reload and
verify remote markdown. Live harness supports TAU_LIVE_ENGINE=webkit. Both also
verify workspace preview, archive/restore and SSE snapshot. 29 unit tests/lint
pass. This is real database/revision evidence, not a provider-model execution.

Approval UI checkpoint: selected session polls real pending-approval API; tool,
description and JSON arguments render as text. Explicit Allow/Deny posts actual
approval ID with CSRF and leaves item visible on failure. Pending guard prevents
double-click submission. 30 unit tests, lint/build and real startup regression
pass. Nonempty approval browser fixtures, denial/retry and genuine tool-run
validation remain pending; no approvals automatically granted.

Approval browser checkpoint: Chromium desktop and WebKit phone render pending
tool description/arguments, reject first Deny POST with 409, retain enabled
request and error, then retry Deny and remove only after acknowledgement. Request
payloads are asserted. Existing composer/setup/search checks remain passing.
30 unit tests/lint pass. These explicit denials are fixture-only; genuine runtime
tool approval and allow-path/security review remain open.

Media transport checkpoint: composer uploads multipart to Tau /api/media with
actual session ID, bearer token, CSRF and abort signal. Upload progress is only
0/100 completion (fetch does not report byte progress). Sends append explicit
[media:id] references with non-inline disclaimer, preserving existing Tau prompt
semantics. 31 unit tests, lint/build pass. Real upload/download and composer
attachment browser tests remain pending; no vision-input claim.

Attachment browser checkpoint: Chromium desktop/WebKit phone choose a file,
verify multipart CSRF upload, reject first referenced run submission while
retaining draft/media, then accept retry without duplicate upload. Retry payload
contains original media ID. Test exposed connection-status toast intercepting
composer clicks; informational toast now ignores pointer events via local CSS.
31 unit tests, lint/build pass. Real multipart/media download validation pending.

Real media checkpoint: Chromium and WebKit call imported uploadMedia in browser
against actual Tau /api/media, verify session association/filename/nonempty ID,
and fetch returned content_url with exact Unicode-byte content roundtrip.
Existing real plan conflicts/archive/workspace/SSE checks still pass. Harness
runs without bearer auth, so this is NOT evidence of authenticated download UI
or unauthorized rejection; those remain pending. 31 unit tests and lint pass.

Authenticated real backend checkpoint: test harness opt-in TAU_LIVE_AUTH uses an
isolated test-only bearer token, forwarded through Tau client/proxy. Chromium
and WebKit pass real session/plan/archive/workspace/SSE/media checks; raw media
content request without token is asserted 401 and bearer request returns exact
content. Regular browser harness remains unauthenticated unless explicit
TAU_BROWSER_TEST_AUTH_TOKEN is set. 31 unit tests/lint pass. Authenticated media
UI link handling still needs implementation; backend auth evidence is not that.

Authenticated media UI checkpoint: session media list offers downloads via bearer
fetch and temporary blob URL, never tokens in URLs. URLs revoked on timeout or
unmount. Chromium/WebKit real authenticated browser tests click Download and
verify filename plus exact saved Unicode content; unauthenticated content still
asserts 401. 31 unit tests, lint/build pass. Timeline inline-media rendering and
large-file resource limits remain separate pending work.

Persisted tool checkpoint: original message JSON now projects tool calls and
result name/call ID/failure status instead of dropping metadata. Calls render as
text-only argument disclosures, results have explicit tool/failure labels.
Malformed legacy JSON retains readable message text. 32 unit tests, lint/build
and live backend regression pass. Tool-call/result correlation, full browser
fixtures, rich result rendering and live tool events remain pending.

Persisted tool browser checkpoint: Chromium desktop/WebKit phone expand a tool-
only call, show literal HTML-shaped arguments without execution, and render a
failed tool result plus output. Fixture corrected to distinguish newly added
GET media listing from POST uploads. 32 unit tests/lint pass. Correlation and
live tool lifecycle remain separate pending requirements.

Full imported workflow matrix checkpoint: 12 fresh sequential cases passed:
Chromium/WebKit × phone 390×844/tablet 820×1180/desktop 1440×900 × light/dark.
Cases exercise persisted text/tools, approval denial/retry, composer accepted/
rejected sends and media retry, FIFO display, cancel, provider setup failure/
retry, search failure/retry and document horizontal bounds. New test:browser
script runs the matrix; test:adapter and test:live expose existing checks.
This is deterministic fixture behavior, NOT image comparison/a11y/full-live
provider acceptance. Production replacement and final installed wheel pending.

Scoped accessibility checkpoint: installed Axe dev dependency; optional
TAU_SMOKE_AXE=1 scans composer and provider dialog during workflow matrix.
Found/fixed small queue/model label contrast and WebKit dark native provider
button contrast with local styles, vendor CSS untouched. All 12 cases pass with
no serious/critical violations in those TWO scopes. Whole app/Plan/media/tools/
search scans and visual review remain pending; do not generalize scoped results.

Expanded accessibility checkpoint: all 12 cases now scan settled whole-page
populated chat (including tools/approvals) and search, plus provider modal.
Fixed missing Back accessible name and metadata/toast/search-link/native button
contrast via local CSS. Wait for finite animations before contrast scans.
All cases pass no serious/critical violations in exercised states; collapsed
Plan/media interiors and runtime loading/error states are not covered by this
claim. No vendor CSS changed; visual paired review still pending.
