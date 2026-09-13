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
