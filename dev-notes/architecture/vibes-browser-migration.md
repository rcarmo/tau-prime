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
