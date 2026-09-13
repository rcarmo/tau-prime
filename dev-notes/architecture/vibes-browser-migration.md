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

## Behavioral coverage not yet replaced (release gaps)

- Existing branch selection/context controls (`branches.spec.mjs`). Imported
  New branch currently rejects; this is a real missing Tau feature.
- Dashboard/metrics/runtime surfaces and unsaved-plan selection confirmation.
- Full keyboard shortcuts/completion/focus traversal (`keyboard.spec.mjs`),
  including behavior beyond the currently supported /thinking command.
- Long-code copy/collapse edge cases, clipboard failures, scrolling/resizing,
  rich Markdown and search selection navigation/draft interactions.
- Real run streaming/tool lifecycle, approval Allow and recovery after disconnect.
- Offline reload support: retirement intentionally does not implement it.
- Full extension slots/SDK initialization in replacement shell (static assets
  remain served, but availability is not integration).

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
