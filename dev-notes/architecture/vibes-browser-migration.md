# Browser regression migration ledger

The old `tests/browser/specs` suite targets deleted DOM anchors and must not be
presented as the active replacement suite. Do not delete its behavioral cases
until mapped or explicitly recorded as a remaining regression.

## Replacement evidence already implemented

- Session creation, selection, archive/restore, URL identity and draft isolation:
  `vibes/tests/live-backend.mjs`, real authenticated Tau in Chromium/WebKit.
- Model and thinking selection, thinking command: same live test.
- Plan revision conflicts, confirmed reload, per-session drafts: same live test.
- Media upload/download authorization: same live test; inline previews and retry:
  `browser-smoke.mjs` across the 12-case `browser-matrix.mjs`.
- Provider modal, token bootstrap/logout, denied save/retry/focus: smoke/live tests.
- FIFO presentation, explicit approval denial/retry, accepted/rejected send,
  search failure/retry, tool-only metadata: smoke matrix.
- SSE protocol/reconnect/cursor/UTF-8: `stream-browser.mjs` with actual HTTP;
  app connected/focus state: live test. Full streamed run is NOT yet equivalent.
- Accessibility/overflow: optional `TAU_SMOKE_AXE` and `TAU_LIVE_AXE` scopes;
  cannot substitute for old unexercised interactions or visual review.
- Service-worker retirement: `worker-upgrade.mjs`; NOT offline caching parity.

## Remaining parity checklist (reconciled at 1da1a0d)

Completed migrations (not full legacy-suite equivalence): existing branch-leaf
selection, Dashboard/metrics, unsaved-Plan selection confirmation, extension
slots/SDK/actions/refresh, Allow/Deny conflict/retry, code copy/collapse/UTF-8
thresholds/content reset, and search draft preservation. Evidence below records
which journeys are real Tau and which use fixtures.

Remaining bounded work:
- [x] Rich Markdown semantic rendering, unsafe protocol/active-content fixture
  rejection and literal user messages migrated (9feed70–8f83301); not exhaustive sanitizer audit.
- [ ] Keyboard completion and focus traversal beyond guarded Ctrl/Cmd+K/N;
  timeline scrolling and touch/viewport resize (`keyboard`, `composer`, `timeline`).
  Keyboard/mouse composer resizing and release cleanup now covered.
- [ ] Cross-session search source navigation remains; same-session real link
  navigation preserves text drafts. Pending-file unload warning/clear covered.
- [x] Settings surfaces mapped; unsupported instance pins documented, provider
  discard confirmation added, expanded installed Axe scopes pass. Final artifact
  rerun must include newer runtime changes.
- [ ] Live provider run, streamed tool lifecycle/approval, disconnect/recovery
  and subsequent persisted timeline. Requires provider credentials.
- [ ] Decide offline reload requirement: worker retirement is implemented but
  does not preserve the old offline shell behavior (`service-worker.spec.mjs`).
- [ ] Decide new-branch creation requirement separately from existing leaf
  selection; the imported new-session branch action is unsupported.
- [ ] Final paired aesthetic review and requirement audit. Automated matrix
  results cannot supply human approval.

Legacy visual/DOM-specific assertions (old IDs, exact old component structure)
are historical references, not compatible executable replacement tests. Preserve
them until their behavioral intent is mapped or an explicit scope decision is
recorded. Do not infer comprehensive parity from this grouped audit.

## Execution

Current replacement entrypoints live under `src/tau_web/vibes`:
`bun run test:adapter`, `bun run test:browser`, `bun run test:live`.
Use `TAU_VIBES_PROXY_ALL=1 TAU_LIVE_AUTH=1` for real production routing.
Old `tests/browser` command/config remains historical until migration completes;
do not relabel the small replacement matrix as all old tests passing.

## Updated restoration evidence

Branch leaf selection, Dashboard/metrics and extension SDK slots/actions have now
been restored with targeted real/fixture browser evidence (see chronological
contract log). Earlier gap bullets describe initial audit, not current absence.
Ctrl/Cmd+K search and Ctrl/Cmd+N composer focus restored; two-browser checks pass.
Full shortcut, modal exclusions and completion edge-case matrix still pending.

Clipboard failure checkpoint: both Chromium desktop and WebKit phone now force
primary clipboard rejection and a throwing execCommand fallback, assert truthful
error state and removal of the temporary textarea, then retry successfully with
exact Unicode contents. Fallback cleanup runs in finally and restores prior focus.
Strict lint, 51 unit tests and frontend build pass. Collapse parity remains open.

Code collapse restored in the imported renderer enhancement: >40 split lines or
>24576 UTF-8 bytes starts collapsed; native button toggles aria-expanded without
replacing focused control. Local CSS bounds the pre, leaving vendor CSS untouched.
Chromium desktop/WebKit phone verify real overflow, keyboard expand/collapse,
focus retention and exact full copying while collapsed. Unit 51/lint/build pass.
Threshold boundary and content-replacement reset fixtures remain to migrate.

Collapse boundary browser fixtures now verify 39/40 newline-terminated lines,
24576/24577-byte code, and 8192 Japanese characters plus newline (24577 UTF-8
bytes). Exact rendered contents retained; Chromium desktop/WebKit phone pass,
as do 51 unit tests and lint. Content-replacement expansion reset still pending.

Content replacement reset verified: expand post 4, change same-ID fixture text,
then refresh through accepted composer send. Chromium/WebKit assert new Unicode
contents, collapsed state, updated byte label and single wrapper/copy control.
51 unit tests/lint pass. Code collapse lifecycle coverage now includes initial
state, thresholds, keyboard focus, complete copy, and same-ID replacement reset.

## Consolidated refresh at f082c7e

- Full Chromium/WebKit × phone/tablet/desktop × light/dark workflow/Axe matrix:
  12/12 passed, including code-collapse lifecycle additions.
- Authenticated browser SSE: both engines pass split UTF-8 delivery, reconnect
  cursor and replay deduplication. This is transport fixture evidence.
- Real Tau production-route proxy journeys: both engines pass with bearer auth,
  then both pass again with login-UI validation enabled. No provider attempted.
- Service-worker upgrade/retirement test passes; this is not offline support.

These are source-tree production-route tests, not a refreshed installed wheel.
Paired visual review, provider execution, final artifact and remaining legacy
behavioral gaps remain separate gates.

## Installed artifact refresh: 52b4bb1

Two wheels built with SOURCE_DATE_EPOCH=1789344000 compare byte-identically.
Fresh venv wheel install with the declared [web] extra passes Chromium/WebKit
production-route authenticated login-UI journeys via TAU_BROWSER_BIN, which
removes checkout PYTHONPATH. Initial attempts without dependencies/web extra
failed startup; corrected by installing the declared extra, not source imports.
Artifact and checksums: /workspace/tmp/tau-vibes-52b4bb1/{a,SHA256SUMS}.
This refresh does not establish live-provider execution or paired visual approval.

## Installed responsive matrix

Added tests/live-matrix.mjs: requires installed TAU_BROWSER_BIN, runs both engines
at 390x844/820x1180/1440x900 in light/dark, authenticated login/logout and real Tau
workflows, with existing Plan/Session-media serious/critical Axe scopes enabled.
Harness now explicitly opens/closes the responsive workspace drawer.
52b4bb1 wheel: second complete run 12/12 passes. First run passed eight cases but
WebKit tablet/light timed out awaiting provider modal after logout reload; not
reproduced in full retry, remains an intermittent finding, not explained/fixed.
Logs retained in /workspace/tmp/tau-vibes-52b4bb1/installed-matrix{,-retry}.log.
51 unit tests and strict lint pass. Not a whole-page installed Axe audit or
provider/visual approval; source-tree fixture whole-page scans remain separate.

Logout reliability investigation: five consecutive installed-wheel WebKit
820x1180/light full authenticated/Axe journeys passed; sixth run with new
failure-only diagnostic capture also passed. Original intermittent timeout is
not reproduced or explained. Harness now captures readyState, token presence
(boolean only), unauthenticated sessions status, dialog identity and bounded
alerts before teardown on recurrence; no timeout increase or production change.
51 unit tests/lint pass. Keep finding open rather than treating repetition as fix.

Approval Allow migration: browser-smoke supports TAU_SMOKE_APPROVAL=allow (default
remains deny). Chromium desktop/WebKit phone pass explicit Allow click, 409 error,
retry availability, exact allow payload on both attempts and disappearance only
following accepted decision. This is fixture approval UI evidence, not live tool
execution. Existing deny matrix remains unchanged. 51 unit tests/lint pass.

Inline media recovery fixture: TAU_SMOKE_IMAGE_FAILURE=1 forces authenticated
image requests to fail (503) until explicit retry. Chromium/WebKit verify alert,
no fabricated image, enabled download retry, successful filename, error clearance
and decoded blob-backed raster preview. 51 unit tests/lint pass. This is fixture
failure/recovery coverage, not a real-provider media journey.

Widget transport boundary regression: declared oversize cancels before reads;
exact 2 MiB Unicode document survives split multibyte chunks; truncated stream
propagates failure rather than returning partial document. Existing streamed
oversize cancellation remains covered. 54 unit tests/166 assertions and lint pass.
No production changes; tests exercise Tau client streams, not browser rendering.

Widget lifecycle correction: superseded refresh failures now use the same
per-frame generation check as successes; action completions/errors are suppressed
after adapter disposal. Deferred-response regression verifies newer refresh wins,
stale failure is ignored and disposed action emits no response. 55 unit tests,
lint/build and Chromium/WebKit smoke pass. Updated runtime requires final wheel
refresh; 52b4bb1 artifact does not contain this correction.

Search draft migration: Chromium/WebKit verify the original rejected composer
draft survives search rejection, accepted results and Ctrl+N return to persisted
timeline. Entering search again, editing an unsent query and escaping restores
the same draft and focus. 55 unit tests/lint pass; no production change.
Source-session navigation and broader rich-Markdown parity remain separate.

Refresh input/disposal hardening: frame/extension/widget IDs must be nonempty
strings <=256 characters before dispatch. Tests reject malformed identities
without requests and suppress both pending successful/error refresh completions
after disposal. 56 unit tests/lint/build and Chromium/WebKit smoke pass.
Runtime change requires refreshed final artifact; earlier wheel remains checkpoint.

## Consolidated runtime checkpoint ff5deb1

Full Python suite: 1313 passed. Full 12-case Chromium/WebKit responsive light/dark
fixture workflow/Axe matrix passed after widget lifecycle fixes. Both engines'
real Tau production-route authenticated login/workflow journeys passed with
TAU_VIBES_TEST_CSP=1 (no captured CSP violations). These journeys still do not
execute a provider. Worktree clean before recording these results. Current JS
suite is 56 tests (last lint/build and JS run at ff5deb1 implementation).

Logout race reproduced and corrected: refreshed 5c242e6 wheel matrix failed at
WebKit tablet/dark with tokenPresent=true after attempted clearing/reload.
A deterministic same-turn input+save regression fails against that installed
wheel and passes on corrected source in Chromium/WebKit. Save now reads the
mounted named token input instead of a potentially stale rendered-state closure.
56 unit tests/lint/build pass. New installed artifact/matrix still required; the
failed 5c242e6 builds were not delivered as validated artifacts.

## Corrected installed artifact: 87aebdb

Two SOURCE_DATE_EPOCH=1789344000 wheels compare byte-identically. Installed wheel
(with existing declared [web] dependencies, checkout PYTHONPATH disabled) passes
all 12 engine/theme/viewport authenticated journeys on the first complete run,
including deterministic same-turn logout token clearing, Plan/media Axe scopes
and CSP capture assertions. This closes the reproduced stale-token logout race.
Artifact/checksums/log: /workspace/tmp/tau-vibes-87aebdb/. Still not provider
execution, offline parity, comprehensive legacy parity or paired visual approval.

Markdown safety migration found Markdown-generated javascript: links surviving
raw-HTML escaping. Normal/thinking Markdown now removes href/src protocols other
than HTTP(S)/mailto after parsing. Chromium/WebKit verify semantic headings,
emphasis, lists, inline code and absence of scripts/event handlers/javascript
links in the fixture; 56 unit tests/lint/build pass. Literal-user test remains
pending (initial fixture exceeded the ten-post initial page and was removed).
Final wheel must be refreshed for this runtime safety correction.

Literal user messages restored as escaped text nodes with preserved whitespace,
not parsed Markdown. Dedicated Chromium/WebKit fixture asserts literal Markdown
and HTML-looking text without created strong/img/script elements or execution.
Fixture uses increasing ID 16 (initial ID 6 after ID 14 was correctly filtered by
ascending pagination validation). 56 unit tests/lint/build and standard Chromium
smoke pass. User rendering is now distinct from assistant Markdown.

Markdown URL boundary browser checks: Chromium/WebKit verify javascript,
mixed-case javascript and data links lose href while HTTPS, mailto and relative
links retain exact href. 56 unit tests/lint pass. This is bounded protocol/semantic
coverage, not an exhaustive sanitizer security audit.

Composer resize keyboard migration: Chromium desktop/WebKit phone verify Home,
End and arrow increments clamp at advertised min/max, actual textarea geometry
matches maximum, separator keeps focus and draft remains intact. 56 unit tests
and lint pass. Pointer/touch drag cleanup and resize across viewport remain open.

Composer pointer migration: real Playwright mouse drag in Chromium/WebKit grows
input from minimum, enters/exits dragging state, restores body cursor/userSelect
on release and preserves draft. 56 unit tests/lint pass. Phone viewport WebKit
uses a mouse here; this is not a touch-device gesture claim.

## Settings audit (681c811 runtime)

Legacy settings-layout/accessibility specs cover Authentication, Model and Runtime
categories, category navigation, retained mounted forms, overflow and focus.
Replacement destinations: Provider setup (token/provider/credential), composer
model/thinking selector, Runtime metrics and Session dashboard. These are separate
Vibes-owned surfaces, not a recreation of the old category DOM.

- Token reload, failed provider save/input retention and modal focus are covered.
- Model/thinking revision-safe workflows run against real Tau in both engines.
- Runtime/dashboard open-only polling and branch selection have fixture coverage.
- Legacy category IDs/navigation and retained closed-dialog DOM are intentionally
  not reproduced. Provider modal unmounts on close: unsaved edits on explicit close
  are not currently retained. This is a concrete remaining draft-policy gap.
- Instance-wide model-pin sync controls are not exposed: Tau has no matching
  route, and UI explicitly labels pins browser-local. Legacy exported functions
  remain unused by exposed controls; do not claim server preference support.
- Existing installed Axe scopes cover Plan/media, not all runtime/model surfaces;
  fixture provider-modal scans do not substitute for that remaining audit.

Provider close draft protection: Cancel/Escape/backdrop now require explicit
confirmation after any input edit; pending saves cannot dismiss. Declining keeps
mounted form/error state. Chromium/WebKit verify cancelled Cancel/Escape after
failed provider save preserves model/error/focus, then normal save succeeds.
56 unit tests/lint/build pass. Credentials stay in component memory only; no new
browser persistence. Confirmed discard/backdrop browser cases remain to verify.

Provider discard completion: Chromium/WebKit verify a dispatched backdrop pointer
event with declined confirmation retains edit; confirmed Cancel closes and
restores trigger focus; reopen drops discarded edit and clean Cancel closes
without confirmation. Backdrop event is synthetic (not touch hit-testing).
56 unit tests/lint pass. No production changes.

Expanded installed Axe scopes: Provider setup, Runtime metrics and Session
dashboard added alongside Plan/media. Installed 87aebdb wheel passes all 12
engine/theme/viewport journeys with expanded scans and CSP assertions. Scope
regions are opened explicitly; provider waits for enabled model input. This
wheel predates Markdown/user rendering and provider-discard changes, so final
current-runtime artifact audit remains required. 56 unit tests/lint pass.

Current artifact attempt ca45478: identical wheels and expanded installed matrix
12/12 pass. Fixture Axe exposed 3:1 Markdown link contrast; local post-content
link override uses primary text color plus underline, vendor CSS unchanged.
Updated fixture matrix passes 12/12 on full retry. First fixed run had unrelated
WebKit phone/dark missing run-conflict alert timeout, not explained or fixed.
56 unit tests/lint/build pass. ca45478 artifact not attached because contrast fix
postdates it; final wheel refresh remains. Logs under tmp/tau-vibes-ca45478 and
/workspace/tmp/link-contrast-matrix-retry.log.

Widget rejection fixture sequencing: earlier WebKit failure was at second
submission immediately after prior content clear. Clear precedes onPost/finally;
receiver intentionally ignores submits while loading. Test now awaits enabled
textarea before beginning separate rejection/duplicate scenario. Three WebKit
phone/dark Axe runs pass; duplicate events remain same-turn. 56 unit tests/lint
pass. No production change or timeout increase; not a proven exhaustive flake fix.

Search navigation migration: Chromium/WebKit now click Open source session,
await real page navigation, assert explicit selected-session URL, persisted
message and retained composer text draft. Same-session source link exercised;
cross-session selection and nonpersistent File objects remain distinct cases.
56 unit tests/lint pass. No production changes.

Pending-file navigation protection: composer beforeunload handler checks all
in-memory session file drafts and requests browser confirmation if any exist.
Text-only drafts remain reloadable without warning. Chromium/WebKit fixture
uploads a pending file then asserts cancellation of a synthetic beforeunload;
this verifies handler behavior, not browser-native dialog policy. Initial test
selected the workspace file input; corrected to composer input. 56 unit tests,
lint/build and both smoke journeys pass. Runtime requires final wheel refresh.

Pending-file warning cleanup: Chromium/WebKit remove the attachment via its UI
button, verify synthetic beforeunload is no longer cancelled and text draft is
unchanged. 56 unit tests/lint pass. No production changes.

Consolidated c656c22 source checkpoint: full Python 1313 pass; 56 JS tests and
strict lint pass; complete 12-case workflow/Axe matrix passes first run after
Markdown contrast, provider discard and pending-file warning changes. Worktree
clean before evidence update. Latest runtime not yet in attached checkpoint.

Supported slash completion: Chromium/WebKit type /thi, Tab accepts /thinking
without a request, focus remains in composer, and Escape dismisses completion
without deleting typed text. 56 unit tests/lint pass. Slash popup currently lacks
listbox/option semantics (unlike session mentions); accessibility gap identified.

Slash accessibility: listbox/selected-option semantics plus textarea controls and
active-descendant relationships added. Expanded composer Axe scope exposed
2.5:1 command-name contrast; local primary-text override fixes it without vendor
CSS edits. Chromium/WebKit verify relationships and completion with Axe enabled;
56 unit tests/lint/build pass. No screen-reader usability claim from Axe alone.

Viewport resize migration: Chromium/WebKit expand composer to maximum, shrink
viewport height to 500px, assert actual height and aria-valuenow/max clamp to
250px, preserve draft, then restore original viewport and bounds. 56 unit tests
and lint pass. This is viewport resize, not mobile virtual-keyboard emulation.

Interrupted resize: Chromium/WebKit start a real mouse drag then dispatch window
blur, verify dragging state and body cursor/userSelect restore before pointer
release. Subsequent keyboard/viewport resize succeeds. 56 unit tests/lint pass.
Blur is synthetic; no OS-level focus-switch or touch-cancel claim.

Cross-session search navigation now covered in Chromium/WebKit: changed fixture
result points to search-other; actual navigation selects destination URL/timeline,
composer starts empty, and smoke session text remains in its separate stored
draft. 56 unit tests/lint pass. Fixture-backed navigation, not real Tau search API
integration evidence. No production change.

3a5942c artifact attempt: two identical wheels and installed expanded 12-case
matrix/CSP pass. Fixture dark-theme composer scan exposed slash-description
contrast 3.59:1. Local primary-text override extended to description; complete
12-case fixture matrix then passes. 56 unit tests/lint/build pass. Final artifact
must include this CSS correction; pre-correction wheel not delivered as final.

82d1f33 artifact attempt: epoch-pinned wheels byte-identical. Installed matrix
passes 11 cases then WebKit desktop/dark loses 'Draft survives model selection'
(expected text, actual empty). Three targeted repeats pass. Not explained/fixed;
do not claim complete installed pass or deliver as final. Logs/builds retained
under /workspace/tmp/tau-vibes-82d1f33. Further race diagnostics required.

Model-draft intermittent investigation: new pre-selection assertion reproduced
empty input immediately after fill, before opening/selecting another model. Thus
prior 'model-selection draft loss' attribution was not established. Picker close
schedules trigger focus in requestAnimationFrame; harness now waits for restored
focus before fill, plus verifies draft before mutation and captures bounded
remount/storage-length diagnostics on later failure. Five installed WebKit
desktop/dark repeats pass. 56 unit tests/lint pass. No production change or timeout
increase; complete installed matrix still required.

82d1f33 installed release checkpoint, harness 953745b: full 12-case authenticated
matrix now passes with expanded Axe scopes and CSP assertions after awaiting
picker focus restoration. Both epoch-pinned wheels remain identical; artifact
includes all runtime changes through 82d1f33 (later commits test/docs only).
Attached wheel/checksums supersede 87aebdb checkpoint. This closes the observed
fixture sequencing failure, not live-provider/offline or paired-visual gates.

Timeline scroll migration: Chromium/WebKit verify overflowing reverse timeline
accepts negative history scroll, composer focus returns scrollTop to zero/newest
and draft is unchanged. 56 unit tests/lint pass. Programmatic scroll assertion,
not touch momentum or full streamed auto-scroll behavior.

Markdown encoded protocol tests: Chromium/WebKit reject entity-obfuscated
javascript URL; tab-obfuscated source stays non-link text. Initial expectation
of an anchor for the latter was corrected to assert no actionable link. Delegate
security review timed out without findings. WebKit new layout twice settled at
1px scrollTop offset; scroll assertion now permits <=1 CSS pixel (was <1).
56 unit tests/lint pass; no production changes or exhaustive-security claim.

## Artifact/content audit at 75d9b04

All 113 packaged static files in delivered 82d1f33 wheel byte-match current
checkout; wheel contains no retired tau_web/frontend tree. Since 82d1f33 only
browser tests and documentation changed. Clean worktree verified before audit.
Thus no runtime rebuild is currently necessary. Automated installed/reproducible
artifact gate is complete, independently of pending human acceptance.

Remaining acceptance boundaries: provider-backed streamed run/tool/recovery,
real touch gesture evidence, offline/new-branch requirement resolution and paired
visual review. Basic history scroll, cross-session search, slash completion and
keyboard/mouse/viewport resize now have replacement checks. Existing real Tau
workspace/Plan/session/model/media/runtime workflows are covered by installed
matrix; they should not remain marked pending solely because provider runs are.
Independent review attempts timed out; no external audit completion claimed.

Branch capability cleanup: Tau exposes branches GET/select POST, not imported
empty-child-session creation. Removed onCreateBranch wiring that exposed a form
whose save always rejected. Existing leaf selector retained. Real Tau Chromium/
WebKit journeys verify no New branch button and normal root creation still works;
56 unit tests/lint/build pass. New-branch requirement remains unresolved, not
implemented by hiding UI. Current wheel predates this runtime cleanup.

Touch protocol check: TAU_SMOKE_TOUCH=1 uses Chromium CDP touchStart/move/end on
phone viewport, verifies composer growth, drag cleanup and draft retention.
Browser protocol events (not JS-dispatched pointer events) pass; 56 unit tests
and lint pass. This is emulated Chromium touch, not physical-device/WebKit gesture
or virtual-keyboard acceptance. Optional mode rejects non-Chromium engines.

## Offline parity implementation boundary (97555f0 audit)

Legacy service-worker.spec.mjs requires shell reload without network, excludes
API entries, and historically skips WebKit offline navigation except opt-in.
It does not establish offline conversations or offline mutation support.
Current replacement serves a retirement worker at /sw.js and does not register
a caching worker from bootstrap. Offline reload parity is genuinely absent.

Bounded implementation still required:
1. Build-versioned public shell cache: static index plus bootstrap, bundle/CSS,
   independent extension SDK/renderer and required static dependencies. Generate
   asset list/version from build inputs, rather than fixed ?v=1 alone.
2. Never cache API requests/responses, bearer-bearing requests, uploaded media,
   widget documents, provider data or externally fetched resources. Do not cache
   arbitrary navigations with session query strings as separate private pages.
3. Network-first navigation with static index fallback; exact allowlisted assets
   only. Avoid mixing old bootstrap/bundle versions during activation.
4. Remove only owned obsolete shell caches, preserve unrelated origin caches,
   and verify new-worker upgrade from retirement-worker installation.
5. Offline UI must report unavailable backend, preserve local text drafts and
   never claim sends/approvals succeeded. No queued replay of offline mutations.
6. Real-browser tests: online install, offline reload, reconnect, cache inventory
   excluding APIs/media, and version upgrade. Report WebKit engine limitations
   explicitly instead of converting a skipped case into a pass.

No caching implementation made in this audit; requirement remains pending.

Offline worker groundwork: build generates offline-sw.js with content-derived
version and exact public shell/font manifest. Worker omits credentials during
precache, ignores API/unknown/auth-bearing requests, has no offline mutation
queue, and avoids skipWaiting. Unit interception exclusions pass (57 total),
as do build/lint. Worker is NOT registered/routed yet; no offline parity claim.
Browser install/offline/upgrade tests must precede activation. Network-first
navigation/version coexistence remains to review before enabling.

Inactive offline worker positive unit paths: install passes omit/reload options
for every exact public asset; offline root navigation with a session query falls
back to cached '/' without storing the query URL. 58 unit tests/lint pass.
Bun Request reports credentials=include even when constructed with omit here;
unit uses an option-capture stub, so real-browser credential verification is still
required. Worker remains unregistered and offline implementation incomplete.

Inactive worker real-browser isolation: tests/offline-browser.mjs serves generated
worker and actual public assets from local HTTP, with a static fixture index.
Chromium verifies all precache requests omit cookie/Authorization, API is absent
from cache, offline session navigation returns public shell and API fetch fails.
WebKit reaches offline navigation then reports internal browser error (same class
as historical skip); recorded as failure, not pass. 58 unit tests/lint pass.
Production worker remains inactive; real app bootstrap/upgrade not yet validated.

Offline version policy correction: controlled root navigations now use cached
entry document paired with cached bundles, not newer network HTML. New worker
still waits for old clients to close (no skipWaiting). This supersedes the earlier
network-first proposal. Unit verifies online navigation stays on installed
version; 59 unit tests/lint/build and Chromium isolated worker journey pass.
Production remains inactive pending real-app and activation/upgrade tests.

Offline activation cache cleanup: Chromium isolation test seeds old Tau and
unrelated caches, installs generated worker, verifies only old owned caches are
removed and unrelated sentinel contents survive. Credential-free precache and
offline fallback assertions remain passing. 59 unit tests/lint pass. This is
cache migration on first activation, not waiting-worker/version upgrade coverage.

Waiting-worker upgrade verified in Chromium: serve next generated version,
registration.update reaches waiting while old controlled page stays open; close
page, reopen and verify old owned cache removed/new cache active, unrelated cache
retained. Offline/credential exclusions still pass. 59 unit tests/lint pass.
Still isolated static fixture index, not full application bootstrap; production
registration remains disabled pending that gate.

Offline full-app harness mode (TAU_OFFLINE_APP=1) serves actual index/bootstrap/
bundles with correct MIME types. Chromium boots .app-shell offline with unavailable
backend, API fetch still fails and worker upgrade succeeds. App's own credentialed
asset requests are excluded from precache counting; isolated mode continues to
assert every precache request is credential-free. Both modes pass plus 59 unit
tests/lint. No real Tau backend, offline mutation/draft UX or WebKit completion
claim; production registration remains disabled pending integration decision.

Offline install failure cleanup: partial current-version cache is deleted when
asset fetch/cache write fails and installation rejects. Regression verifies one
successful entry then failed asset removes only owned current cache. 60 unit
tests/lint/build and Chromium full-app offline/upgrade harness pass. Worker still
inactive in production; no offline acceptance completion claim.

Offline packaging regression: generated worker included in wheel; worker template
and build.js retained in source distribution inputs, template excluded from
runtime package. Packaging/build backend suite 13 pass. Initial assertion treated
archive-name strings as Paths; corrected test, no packaging implementation change.
Production offline registration still disabled.

Offline full-app feedback: Chromium offline reload shows an alert, attempted
composer submission retains 'Offline unsent draft' and alert remains visible;
API fetch fails. Existing cache privacy/upgrade checks pass. 60 unit tests/lint
pass. Fixture has unavailable backend throughout and no selected server session;
not a provider or online-to-offline active-session recovery test.

Real Tau offline route checkpoint: /offline-sw.js serves generated public worker
with root scope permission, separate from legacy retirement /sw.js. Explicit
public-route allowlist required (initial registration returned 401, corrected
only worker route). Opt-in TAU_LIVE_OFFLINE Chromium journey installs against
real authenticated Tau, reloads offline with shell/error and failing API, then
reloads online. Frontend/packaging Python gates, 60 unit tests/lint pass. Automatic
registration still disabled; active-session draft restoration assertion pending.

Real Tau offline draft round-trip: Chromium saves active-session text draft,
installs opt-in worker, reloads offline, verifies stored draft unchanged and API
unavailable, reconnects/reloads and verifies selected session and composer text
restored. 60 unit tests/lint and real authenticated journey pass. Offline UI does
not restore server-selected session until backend returns; no offline send queue.
Automatic registration remains disabled; WebKit offline limitation persists.

Offline registration enabled: external bootstrap registers /offline-sw.js in
secure contexts after app import, updateViaCache none; registration failure logs
warning without blocking app startup. Chromium real Tau automatic-registration
journey passes offline reload/draft/reconnect with CSP checks; WebKit authenticated
online/login journey with registration also passes CSP checks. 60 JS tests/lint/
build and 27 frontend/packaging Python tests pass. WebKit offline navigation still
fails in engine harness and is not claimed supported by evidence. Final installed
artifact/matrix refresh required; old delivered wheel predates offline feature.

75926fa production offline checkpoint: full Python 1314 pass, fixture/Axe matrix
12/12 pass, two epoch-pinned wheels byte-identical. Installed corrected runtime
passes all 12 expanded authenticated/Axe/CSP workflows; installed Chromium automatic
offline registration/draft/reconnect/CSP journey also passes. Wheel/checksum in
/workspace/tmp/tau-vibes-75926fa supersede older runtime checkpoints. WebKit offline
navigation remains a reported engine limitation, not a passing gate. Provider
execution, new-branch scope and human/device acceptance remain open.

WebKit offline isolation: TAU_OFFLINE_OUTAGE=1 drops incoming server sockets and
closes existing connections instead of context.setOffline. WebKit isolated and
actual-app fallback/upgrade journeys pass; Chromium actual-app outage also passes.
Both verify API network failure, cached shell, error/draft handling and upgrade.
Thus prior WebKit internal navigation error is specific to offline emulation in
this harness, not reproduced with server outage. Not proof of every device's
network-off behavior. 60 unit tests/lint pass; no production changes.

## New-branch parity resolution (historical audit)

At ca3e468^ (last tree before old frontend removal), frontend/src/api/tau.ts
createSession accepts only title/provider/model. Its branches/selectBranch methods
list/select existing entries; Timeline.tsx:167 exposes leaf-selection buttons.
No parent_session/parentId/fork/createBranch source matches exist in that frontend.
Legacy branches.spec.mjs likewise verifies listing/selection, not child creation.
Current routes/timeline.py retains list/select semantics, including validation.

Therefore earlier classification of imported 'New branch' as missing Tau parity
was incorrect. It creates an empty child session in upstream Vibes, a different
capability unsupported by Tau's session API. f335896 hides that invalid action;
existing Tau leaf selection has real-backend browser coverage. No backend feature
is removed or silently substituted. New child-session creation would require a
separate feature request, not completion of this replacement parity plan.

## Final automated delivery audit at 70738f4

Clean worktree; all 166 tau_web files packaged in delivered 75926fa wheel match
current checkout bytes. Retired frontend absent. Changes since artifact revision
are browser-test/docs only; no runtime rebuild required. Reproducible build,
installed online matrix, Chromium installed offline journey, both-engine outage
fallback/upgrade, and source regressions have explicit evidence above.

Unfinished acceptance gates are not build failures:
- No OpenRouter credential available in environment/keychain; live provider run,
  live tools/approval and disconnect recovery cannot be verified yet.
- Emulated Chromium touch passes; physical-device gestures and paired aesthetic
  acceptance require an actual reviewer/device. Automated scans are not approval.
- Independent delegated reviews timed out; no independent sign-off claimed.

Overall goal remains incomplete until required external acceptance is supplied
or explicitly scoped by the user. Do not loop on more passing fixture tests as a
substitute for those missing gates.

## Local provider execution failure (2026-09-14)

Added opt-in tests/provider-live.mjs using configured local-llama/qwen38-gsq,
authenticated production web routes and an isolated temporary database/workspace.
Actual browser submits a read-only README tool request. Run fails before provider
execution: submission_failed / UnknownSessionError, session not registered;
persisted timeline is empty. Direct server completion previously returned OK.

Evidence: services.py constructs AsyncAgentPool without a lazy session loader;
runtime._submit delegates directly to pool.submit_prompt. REST session creation
persists a repository record but does not load/register CodingSession. Existing
runtime unit tests explicitly register fake sessions. Full fixture/API suites did
not cover this real execution boundary. This is a release-blocking integration
failure, not missing credentials or a successful provider validation.

Next required implementation: lazy/concurrency-safe CodingSessionFactory loading
from durable session metadata/storage before run/queue submission, preserving
approval callbacks, Plan tools, provider config and ownership/shutdown semantics.
Then rerun real provider/browser/tools/reconnect and regenerate installed wheel.
Test output retained at /workspace/tmp/provider-live-chrom.log. No completion claim.

Runtime lazy-loading fix: DurableAgentRuntime optionally initializes unregistered
sessions under a lock, registers ownership and approval callback, and reuses the
agent. Web services use CodingSessionFactory with durable storage, provider/model/
thinking metadata and Plan hooks. Regression verifies sequential reuse and one
owned close. 278 web tests and changed-file Ruff checks pass. Previous orphan
route expectation updated: invalid provider now fails provider validation rather
than unconditional unregistered-session error.
Live browser now reaches agent execution/retries, but local llama endpoint refuses
connections (direct curl also fails); no successful live tool result claimed.
Provider harness now awaits selected session and reports run/approval states.
Broader model-change/reload/queue lifecycle review and full suite remain pending.

Lazy initialization recovery checkpoint: full Python suite at 2bd553e passes
1315 tests. Added regression: first loader failure records failed run without
prompt execution; second submission initializes successfully and completes,
owned agent closes once. Runtime suite now 16 pass; Ruff passes. Local llama
endpoint still refuses direct connections; successful provider run remains blocked.

Concurrent lazy-load regression: two first submissions overlap while loader is
blocked; loader called once, pool serializes both prompts, owned session closes
once. Runtime suite 17 pass and Ruff pass. Pool queues competing submissions;
it does not reject the second as busy (correcting initial investigation wording).

Lazy-load shutdown fix: shutdown marks runtime closing and holds initialization
lock while closing pool, preventing late construction from escaping cleanup.
New submissions rejected once shutdown starts. Deferred-loader regression verifies
shutdown waits, loaded owned agent closes once and subsequent submit rejects.
281 web tests pass; changed-file Ruff passes. Provider remains unavailable;
model/thinking mutation coherence after a loaded run still requires review.

Loaded-agent metadata coherence fix: model/thinking REST mutations now coordinate
with lazy-load lock, reject active/queued runs before metadata write, and close/
unregister idle loaded agents after successful transaction. Next run reloads
updated durable settings. Added idle pool removal API with busy guard. Tests
verify replacement agent and owned cleanup, plus no write during active run.
303 web/pool tests passed before additional active-run case; runtime now 20 pass,
changed-file Ruff passes. Initial current_run typo corrected to current_run_id.
Branch-selection coherence and broader execution lifecycle still require review.

Branch loaded-agent coherence: leaf selection uses runtime coordinated change,
rejects busy sessions with 409, and invalidates idle agent after durable selection.
Route regression verifies busy rejection writes no entry; existing branch route
and runtime reload tests pass (25 targeted tests), Ruff passes. Test setup mistakes
(fixture/storage method names) corrected before pass. Full suite still pending.

Runtime-coherence consolidated checkpoint bdaa844: full Python suite 1321 pass,
60 JS tests/lint pass, real authenticated source production-route Chromium/WebKit
journeys pass after lazy-load/model/thinking/branch changes. Local llama direct
probe still connection refused; live tool success/recovery not verified. Attached
75926fa wheel predates backend fixes and is no longer current final artifact.

269a82a runtime-fix wheel: two epoch-pinned builds byte-identical. Installed
12-case authenticated/Axe/CSP matrix and Chromium offline/draft/reconnect journey
pass with checkout PYTHONPATH disabled. Artifact/checksum in tmp/tau-vibes-269a82a
supersede old runtime wheel. These journeys do not supply a successful local
provider/tool run; endpoint outage remains a separate unresolved gate.

Metadata failure retention regression: rejected durable-change callback leaves
loaded agent open; subsequent run reuses it, then shutdown closes exactly once.
Runtime suite 21 pass, Ruff passes. No production changes. Local provider direct
probe still refuses connections, so live completion remains unavailable.

Metadata shutdown guard: coordinated model/thinking/branch changes now reject
once shutdown begins, before invoking durable write. Regression verifies no write
after shutdown. Runtime suite 22 pass; changed-file Ruff passes. New backend
change requires artifact refresh before final delivery.

fe04f58 installed checkpoint: full Python 1323 pass, two epoch-pinned wheels
identical, installed 12-case expanded Axe/CSP matrix pass. Local llama became
reachable; installed Chromium AND WebKit provider-live journeys now complete
qwen38-gsq run, browser Allow for requested read tool, real README tool execution,
assistant LOCAL_PROVIDER_OK answer and persisted timeline after reload. Logs:
/workspace/tmp/provider-online{,-web}.log. First successful live provider/tool
validation, not just direct curl/fixtures. Disconnect recovery still pending.

Installed live-provider recovery: TAU_PROVIDER_RECOVERY=1 disconnects browser at
pending real read approval, verifies browser API failure while backend retains
same approval, reconnects/reloads, approves through UI, waits for completion and
reloads persisted answer. Chromium/WebKit pass with exactly one run and at least
one actual approval. Provider execution continues server-side; no provider network
outage/restart claim. 60 JS tests/lint pass. Logs provider-recover-{chrom,web}.log.

Post-fix delivery audit 0bcd16f: clean worktree, all 235 packaged tau_web/tau_coding
files in delivered fe04f58 wheel byte-match current checkout. Later change is
provider recovery test only. Confirmed runtime defects addressed with regression
coverage and actual installed local-provider execution/recovery in both engines.
Physical-device gestures and paired visual acceptance remain unverified; they
must not be inferred from automated successes. Earlier broad mypy invocation
also emitted unrelated type errors; no clean project-wide mypy claim is made.

Typecheck audit: default mypy command previously resolved installed packages and
failed missing py.typed. Config now resolves checkout src explicitly. This exposes
49 strict errors; narrowed pool behavior protocol to actual steer/follow_up
literals, fixing CodingSession compatibility in new loader without a cast/ignore.
43 pool/runtime tests and Ruff pass. Mypy now checks 162 files and reports 48
remaining errors in 11 files; typecheck gate explicitly unfinished.

Tool JSON typing fixes: validated subprocess/pytest arguments narrowed to strings,
streamed edit line-number result checked as integer. Coding tools suite 25 pass;
mypy decreases 48 to 45 errors (10 files). Ruff on tools.py exposes existing
lint failures elsewhere in that file; not claimed clean. Full lint/type gates
remain open and must be addressed rather than suppressed.

Pydantic shim typing: TypeAdapter now declares a generic validated return/value
type using Python type parameters; runtime coercion remains unchanged. Session
JSONL Any/generic errors removed. 110 session/export/coding-session tests pass;
shim Ruff clean. Mypy now 43 errors in 9 files; remaining lint/type gate open.

Landlock typing: libc wrapper annotated as CDLL, syscall number/arguments explicit
and result converted to int, preserving error checks and confinement behavior.
Four Linux sandbox tests pass; file Ruff clean. Mypy decreases 43 to 34 errors in
8 files. No relaxation of ABI requirement, allowed roots or fail-closed policy.

Provider typing fixes: Anthropic payload list is contextually typed as JSON values;
Copilot compatible-provider path validates narrowed config before constructing
client. No blanket casts/ignores. 59 provider/config/history tests and file Ruff
pass. Mypy now 32 errors across 6 files; remaining strict checks pending.
