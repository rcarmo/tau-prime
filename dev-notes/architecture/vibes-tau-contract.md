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

Thinking policy checkpoint: imported catalogue lists Tau's six configurable
policy values (not per-model reasoning discovery); mutation uses /thinking with
loaded expected_updated_at. 33 unit tests/lint/build pass. Both authenticated
real browser API checks change policy to high successfully. Initial live run hit
an orphaned dev server (404); removed that stale process and reran successfully.
Harness port collision/cleanup hardening and picker UI interaction remain pending.

Harness ownership checkpoint: smoke/live harnesses reject occupied localhost
ports, monitor owned process readiness and await graceful child exit with bounded
kill escalation. Browser launch now falls within cleanup scope. Unit tests cover
collision rejection and awaited exit; smoke and authenticated live checks pass.
35 unit tests/lint pass. Free-port preflight is not an atomic reservation; owned-
process checks additionally catch bind failures, and permanent server reuse stays
disallowed.

Thinking picker browser checkpoint: authenticated Chromium/WebKit open actual
model picker, choose low via Select thinking level and poll real session API to
verify persistence, then dismiss picker. Initial test used wrong accessible
label (Thinking level); corrected to actual Select thinking level. Both pass with
existing live media/Plan/archive checks. 35 unit tests/lint pass. Full catalogue
selection and unsupported instance-pin controls still require attention.

Model picker checkpoint: real authenticated Chromium/WebKit seed a second model
via actual session API, select it through picker, verify saved model and retained
composer draft. Extra fixture session archived before archive-selection checks.
Unsupported instance-pin sync buttons removed; browser-local pins retained and
scope explained. 35 unit tests/lint/build pass. This verifies selection mechanics,
not execution or provider availability of fixture model names.

Packaging inventory correction: wheel asset allowlist previously omitted Vibes
.mjs runtime modules and extensionless license notices while collecting some
frontend build JS. Scoped Vibes packaging now includes runtime .mjs/licenses/
provenance and excludes tests/build/dev-server/source maps. Nine packaging tests
pass. Generated dist still needs a deterministic clean-source build/ship policy;
this patch alone does not make installed Vibes UI runnable or switch production.

Clean-checkout bundle checkpoint: runtime app.js/app.css now tracked; source maps
remain ignored. Frozen lockfile install and two consecutive builds produced
identical JS/CSS hashes. Ten packaging tests confirm bundle presence without Bun.
This settles shipping policy, not routing: production still uses old frontend
until remaining compatibility/security/visual gates are met. Future source edits
must regenerate and commit bundles alongside source.

Identity/capability checkpoint: default agent/page/app title and manifest name
now Tau; upstream license/provenance unchanged. Removed nonexistent terminal
session probe and disabled terminal popout URL mode. Bundles regenerated;
35 unit tests, lint/build, smoke and authenticated live checks pass. Imported
icon artwork and residual old agent/command requests remain to be reviewed.

Background contract cleanup: agent display registry now derives configured name
from authenticated /api/settings without fabricated capabilities; compatibility
'default' ID is display-only, not a session. Workspace visibility is explicitly
browser-local (existing app persistence) and no longer posts nonexistent Vibes
endpoint. 36 unit tests/lint/build and authenticated live checks pass. Command
catalogue/execution and remaining old event handlers still need migration.

Command capability checkpoint: removed inherited unsupported slash-command list
and nonexistent /agent/commands probe. Menu advertises only /thinking, mapped to
actual revision-checked policy mutation and rejects attached-media misuse.
Other slash input continues explicit error rather than model execution. 37 unit
tests/lint/build and authenticated live regression pass. New command dispatcher
still needs direct composer browser assertion; no claim all Tau CLI commands work.

Real command browser checkpoint: authenticated Chromium/WebKit submit /thinking
medium through composer, verify saved policy and cleared text, reject invalid
level with visible error/preserved draft, and assert zero agent runs created.
Existing model/Plan/media/archive checks remain green. No production code changed.

Real session-create UI checkpoint: authenticated Chromium/WebKit open New root
session dialog, submit a name, verify selected new URL/label and backend provider/
model equal saved onboarding defaults. No provider execution or credential
availability inferred. Existing Plan/media/archive/model workflows remain green.

Session draft isolation checkpoint: real authenticated Chromium/WebKit create a
second session, verify empty composer rather than leaked first draft, edit new
composer/Plan, switch back to first session and recover its prior draft, then
return and recover both new unsaved edits. Both pass. Plan draft persistence is
in-memory only; page reload durability not claimed. No provider execution needed.

Expanded real accessibility checkpoint: TAU_LIVE_AXE scans open dirty Plan and
open session-media section after authenticated workflows. Chromium/WebKit ×
light/dark pass no serious/critical findings in these scopes, with real Plan
revision/draft checks retained. New session media is empty at scan time; populated
media buttons/download are behavior-tested earlier, not included in this scan.
No production changes. Phone/tablet accessibility remains covered only by prior
fixture scopes, not this desktop live check.

Current visual capture checkpoint: smoke supports optional TAU_CAPTURE_DIR;
phone/desktop Chromium light populated chat PNGs captured and delivered. These
are current integration-fixture screenshots, not paired upstream evidence or
approval. Fixture includes unresolved API responses, open tool metadata and
approval controls. Visual comparison/gap correction remains a separate gate.
Both capture workflow runs passed; no production changes.

Transient stream isolation checkpoint: extracted session/run-scoped draft reducer,
ignoring mismatched run/session deltas and resetting on snapshot/session change.
Removed duplicate unscoped append path. Inspection also found focus handler called
missing reconnectIfNeeded; TauEventStream now implements it with connected state.
38 unit tests, lint/build and authenticated live regression pass. Actual streamed
draft browser/visibility reconnect assertions remain pending, not inferred here.

SSE lifecycle unit checkpoint: healthy connection focus leaves transport intact;
disconnect cancels reader, focus reconnects; throwing event consumer leaves cursor
and event-ID dedupe uncommitted for replay. 40 unit tests/126 assertions and lint
pass. These are transport units, not sustained browser/live-provider stream proof.

Pending reconnect race checkpoint: focus storms no longer abort/restart an
in-flight connection; connecting state is explicit and aborted retry callbacks
exit before notifying consumers. Unit test holds handshake pending across ten
focus requests and confirms one fetch. 41 unit tests, lint/build and real
authenticated regression pass. Sustained live provider stream gate remains open.

Critical browser transport correction: sustained stream-browser.mjs exposed
native fetch invoked as this.fetchImpl, producing Illegal invocation in actual
browsers. Default transport now wraps globalThis.fetch. Previous live snapshot
checks used separate direct fetch and did NOT prove application stream health;
unit injected functions also missed this. Chromium/WebKit now consume actual
chunked authenticated HTTP through proxy: split UTF-8, disconnect, Last-Event-ID
reconnect and duplicate suppression verified (two connections). 41 unit tests,
lint/build pass. This fixture server tests transport, not provider execution or
complete application draft presentation.

Application connected-state correction: new real browser assertion requires no
connection toast and preserves connected state after focus. It caught snapshot
handler's nonexistent estimateLineCount helper; replaced with existing
estimatePreviewLines. Earlier workflow successes did not assert app connection
health. Authenticated Chromium/WebKit now pass explicit connected/focus checks
alongside previous workflows. 41 unit tests/lint/build pass; provider runs remain
unverified. Diagnostic instrumentation removed before commit.

Static undefined-variable gate: enabled no-undef for first-party imported JS
(vendor excluded). Found stale api.getThread reference in scroll-to-message;
replaced with session-scoped Tau timeline lookup and stale-session guard. Lint
now passes with gate enabled; 41 unit tests/build and authenticated live workflows
pass. Message-reference navigation edge cases still need browser assertions.

Inline attachment implementation checkpoint: persisted original-message attachment
metadata now feeds TauAttachment. Raster-image previews use authenticated blob
fetch, no tokens in URLs; downloads use same blob and cleanup revokes on unmount.
No inline SVG/HTML preview. 42 unit tests, lint/build and live regression pass.
Actual inline image browser fixture, resource-size limits and preview accessibility
remain pending; session-media download is separately verified already.

Inline image validation INCOMPLETE: new authenticated raster fixture passes
Chromium checks but WebKit reports naturalWidth=0 despite visible blob image.
Keep failing assertion; no cross-browser image pass claimed. Tried known-valid
PNG fixture; forced MIME experiment did not resolve and was reverted. Added
native attachment-button styling for dark contrast. Snapshot mock now sends one
snapshot then heartbeats, avoiding artificial repeated timeline reanimations
during Axe scans. Current full matrix fails at WebKit image decode; investigate
blob lifecycle vs fixture transport before any production switch.

WebKit inline image resolution: debugging blob content showed application/json
with fixture error, not PNG. Catch-all Playwright routing intercepted WebKit blob
URLs and returned API fallback. Non-HTTP URLs now pass through untouched; no
production preview workaround needed. All 12 image/workflow/whole-page Axe cases
pass, including naturalWidth=1, blob source and bearer header checks. 42 unit
tests and strict lint pass. Supersedes unresolved 2445799 finding with evidence.

Media memory bound: authenticated blob reader enforces 32 MiB on declared length
and actual streamed bytes, cancelling oversized bodies and preserving content
type/bytes for valid downloads. This is a deliberate browser safety limit, not a
backend quota change; larger media errors visibly instead of unbounded buffering.
44 unit tests/lint/build and authenticated real download regression pass.

Token bootstrap UI checkpoint: provider modal now accepts Tau bearer token,
stores it in existing browser key only after explicit reload confirmation, and
warns unsaved Plan edits are lost across reload. Separate from provider credential
storage. Real Chromium/WebKit start without injected token, dismiss unauthorized
session picker, save token through UI and complete authenticated workflows. 44
unit tests/lint/build passed earlier in checkpoint. Token clearing/reload warning
edge cases and polished unauthenticated landing remain pending.

Unauthenticated entry checkpoint: session-list 401 opens token/provider setup
rather than empty session picker; non-auth errors retain explicit picker error.
Authenticated Chromium/WebKit login-UI test asserts direct modal, no picker,
then enters token and completes real workflows. 44 unit tests/lint/build pass.
Invalid-token retry and logout behavior still need final security review.

Invalid-token/logout browser checkpoint: Chromium/WebKit start unauthenticated,
save wrong token and verify setup reopens, replace with valid token and complete
workflows, then clear token with confirmed reload. Browser storage is empty and
unauthenticated /api/sessions returns 401 afterward. Both real tests pass; no
production edits. Server-side credential invalidation is not implied by local
logout; token remains valid elsewhere until operator rotation.

Entrypoint CSP preparation: removed imported inline script/error innerHTML paths;
external bootstrap imports tracked runtime and reports load failure with textContent.
Viewport no longer prohibits user zoom. 44 unit tests/strict lint and real auth
workflow pass. Inline style handling and complete production CSP/runtime module
routing remain pending; this is not a production route switch.

Production-policy probe: integration server opt-in TAU_VIBES_TEST_CSP applies
Tau's existing script/style/connect/img restrictions without weakening them.
Real authenticated Chromium/WebKit workflows reported one initial inline loading
style; moved to local CSS. Both now report zero CSP violations in exercised
workflows; assertion retained. 44 unit tests/strict lint/build pass. Unexercised
renderers/widgets may still require separate CSP review; production route switch
not performed by this checkpoint.

Installed candidate checkpoint cc41dae: built wheel, installed isolated venv,
served its packaged Vibes static tree through dev proxy and ran its installed
Tau executable (no checkout PYTHONPATH). Both authenticated Chromium/WebKit
workflows pass under existing CSP. Static-root override canonicalized with
realpath after symlink-prefix mismatch initially returned 404. 44 unit tests/
lint pass. Production route remains old UI: this verifies candidate assets and
backend installation, not completed root switch or final distributable artifact.

Production asset preparation: pinned public-assets.json allowlists imported
runtime modules/styles/fonts/icons; candidate response helper rejects unlisted
and traversal names, supplies explicit JS/MJS MIME and nosniff, and uses no-cache
until asset versioning policy is finalized. Manifest included in wheel. Sixteen
asset/packaging tests pass. Helper not wired to routes yet; production remains
unchanged. Manifest must be refreshed when adding runtime assets.

Asset drift gate: frontend build now deterministically regenerates sorted public
runtime manifest. Test compares allowlist exactly with runtime file suffixes;
source maps/tooling remain excluded. Rebuild leaves tracked bundles/manifest
unchanged; 17 asset/packaging tests pass. Production switch remains separate.

Asset HTTP prerequisite: isolated aiohttp test serves packaged replacement index,
manifest and explicit runtime files via helper, follows every index src/href and
checks success/nosniff plus map/build denial. 18 asset/packaging tests pass. This
is isolated route validation, not production router activation or new UI delivery.

Service-worker transition prerequisite: candidate retire-sw.js removes only
Tau shell cache names, claims clients then unregisters, with no fetch interception.
Test verifies unrelated caches preserved and no fetch handler. Build refreshes
asset manifest; 45 JS unit tests/lint and 8 asset tests pass. Not served at /sw.js
yet; actual cached-client upgrade/browser validation belongs to production switch.
Offline replacement support is not claimed by retirement.

Native worker retirement checkpoint: Chromium/WebKit seed Tau v12 cache and an
unrelated cache, register candidate retirement worker, then verify Tau cache gone,
unrelated content preserved and registration absent. Initial test awaited
activated state, but self-unregistration can transition past it; final assertions
poll actual cleanup effects instead. Both pass. Test scope is /static/, not a
cached production root navigation; actual upgrade routing still pending.

Production route switch checkpoint: / and /index.html now serve imported UI;
nested /static uses explicit allowlist, manifests mapped, /sw.js serves scoped
retirement worker. No alternate UI route. Both authenticated Chromium/WebKit
workflows pass with proxy forwarding ALL responses from actual Tau router.
18 asset/packaging tests pass. Full Python run: 1318 passed, 13 failed: 12 old
frontend asset/markup expectations plus bash stdin regression (not dismissed as
flaky without investigation). Old source cleanup and test migration required;
this checkpoint is not final acceptance or a green full suite.

Root switch test migration: preserved extension-ui/frontend-sdk/widget-bridge
asset contracts (widget route still embeds bridge), while old chat asset/index/
worker expectations now assert imported entrypoint and scoped worker retirement.
Focused frontend/assets/packaging 45 pass. Full Python with venv PATH: 1324 pass.
Prior bash stdin failure was missing python on PATH (isolated rerun passed), not
sandbox regression. Old frontend source and behavioral browser migration still
pending; extension functionality must not be removed as obsolete shell code.

Installed production-root checkpoint 0b50223: two epoch-pinned wheel builds
byte-identical (9,587,561 bytes). Isolated installed Tau with checkout PYTHONPATH
removed serves all HTML/assets/API via real production router (proxy-all).
Authenticated Chromium/WebKit perform wrong-token recovery/login/logout, model/
thinking commands, session creation/archive, Plan conflicts/drafts, media
upload/download and workspace preview successfully. Wheel/checksum delivered as
checkpoint, not final acceptance; obsolete source cleanup, provider execution,
remaining runtime parity and paired visuals still pending.

Superseded source cleanup: removed tracked old frontend TSX/build tree and old
chat app/index/CSS/fonts/service-worker bundle. Independent extension renderer,
SDK and widget bridge remain. Removed ten source-string ownership tests for the
deleted implementation; replacement behavioral coverage lives in imported
workflow tests. Packaging asserts no old frontend/app/preact bundle. Full Python
1313 pass (count reduced by obsolete assertions), real production-router
Chromium/WebKit authenticated workflows pass. Old browser spec migration and
untracked dependency directory cleanup remain separate; Git preserves recovery.

Branch selection restoration checkpoint: explicit Conversation branches disclosure
uses Tau leaf listing/select endpoint, confirmation and pending/error state;
accepted switch refreshes selected session through existing path. This is not
Vibes child-session creation. 46 unit tests/lint/build and real root regression
pass; nonempty branch fixture and confirmation/draft browser checks pending.

Branch browser checkpoint: Chromium desktop/WebKit phone display two leaf choices,
decline confirmation with no mutation, accept exact leaf POST, show selected leaf
active/disabled and retain composer draft. Fixture-only nonempty branch check;
real session storage branch mutation test still pending. 46 unit tests/lint pass.

Real branch storage checkpoint: authenticated Chromium/WebKit use actual model/
thinking session entries, select an earlier leaf via API, refresh real branch
list and choose another leaf through UI confirmation. Session API confirms active
leaf changes; composer draft retained. Both pass production-router workflows.
No synthetic IDs or provider execution required. Full branch context metadata
refresh and running-session interaction remain future regression cases.

Runtime metrics restoration checkpoint: collapsible host CPU/RAM/swap and Tau RSS
reads authenticated /meters only while open, distinguishes unavailable values and
retains explicit error. Both real production-router browsers open it and verify
labels/data surface; 46 unit tests/lint/build pass. Historical sparkline series,
Dashboard detail and responsive/a11y runtime review remain pending.

Runtime responsive checkpoint: expanded metrics fixture verifies CPU percent,
RSS conversion and explicit unavailable swap in all 12 workflow/Axe cases.
Fresh run also caught added provider-token help text contrast on dark tablet;
local text-primary correction applied. All 12 pass no serious/critical findings
in exercised scopes. Bundles rebuilt. No claim of complete Dashboard parity.

Dashboard implementation checkpoint: bounded paginated /dashboard display restores
session/activity/model/queue/summary/preview data with polling only while open.
Session selection requires confirmation and closes only after awaited selection
succeeds. 46 unit tests/lint/build and real root regression pass; open dashboard
browser selection/pagination and responsive accessibility remain pending.

Real Dashboard selection checkpoint: authenticated Chromium/WebKit open live
session summaries, decline selection and retain open Dashboard/current URL,
accept selection and await close, switch back and recover composer plus unsaved
Plan drafts. Both production-router workflows pass. Pagination, failure retention
and broad Dashboard accessibility remain pending. No production code changed.

Dashboard matrix checkpoint: all 12 workflow/Axe cases verify page navigation,
last-page next disabled, failed session selection keeps Dashboard open with error,
and return to prior page. Scoped open Dashboard accessibility passes with local
native-button styling (also applied to branch controls). Bundles rebuilt; failure
fixture deliberately uses unavailable session. Genuine paginated backend records
and dashboard visual pairing remain pending.

Dashboard request guard: ref-backed selection gate prevents concurrent switches;
polling pauses while selecting and successful refresh preserves selection errors
until next explicit selection. Chromium/WebKit fixture checks hold failure alert
past a 3.2s poll interval; 46 unit tests/lint/build pass. Full matrix rerun deferred
until next consolidated checkpoint, not claimed from these two targets.

Extension boundary inventory: SDK requires fetchAsset/request/submit/navigate and
six slot roots; preserving JS routes alone did not initialize these. Added module
listing and API-only authenticated request boundary with traversal/origin guards.
47 unit tests/lint/build pass. Actual SDK configure/loadAll, safe submit/navigation
adapters and slot mounting are still pending; extension integration not restored
by this transport preparation alone.

Extension host prerequisite: external bootstrap loads preserved renderer/SDK
before app; six stable slot roots restored in imported shell. Development server
serves only the two exact preserved support-script names outside imported static
root; production retains existing allowlist. 47 unit tests/lint/build, real root
and smoke checks pass. SDK is loaded but not configured/activated yet; sidebar/
dashboard slots are compatibility placements pending final layout review.

SDK activation checkpoint: imported app discovers enabled modules and configures
preserved integrity-checking SDK with authenticated asset/API and validated
submit/navigation adapters. Failures visible; disposeAll on unmount. Explicit
run mode restored in send adapter for SDK contract. 48 unit tests/lint/build and
real production-router regression pass. Nonempty enabled-module/browser slots
and action event integration remain pending; empty registry is not extension
feature completion.

Nonempty extension activation checkpoint: Chromium desktop/WebKit phone load an
actual SRI-hashed JS module through preserved SDK, assert bearer asset fetch,
module API request to Tau settings, and mounted text in compose_above slot.
No mocked SDK/import function. 48 unit tests/lint pass. Real enabled extension
registry and submit/navigation/view-action browser paths remain pending.

Extension action browser checkpoint: actual SRI module buttons submit explicit
run content through SDK to selected session and navigate to a verified session;
Chromium/WebKit assert acceptance and composer draft preservation. No SDK mocks.
48 unit tests/lint pass. General view-action event bridge and deployed nonfixture
extension registry remain separate gaps.

Widget action bridge checkpoint: validated frame/extension/widget/request/action
IDs route through authenticated API boundary and return correlated renderer
success/error; listener removed on disposal. 49 unit tests/lint/build and real
root regression pass. Embedded iframe message validation remains in preserved
renderer; end-to-end iframe action and widget submit/refresh paths still pending.
