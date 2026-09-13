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
