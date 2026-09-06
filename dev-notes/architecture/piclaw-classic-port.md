# Corrected target: Piclaw classic UI

Rui rejected the visual-mode port on 2026-09-06. The earlier visual-mode
screenshots, PDF and CSS pins are NOT reference evidence for this task.

## Source of truth

Pinned release: Piclaw 2.15.3, `runtime/web/static/classic/index.html`,
`classic/dist/app.bundle.{js,css}` and `app.bundle.js.map`.
The map embeds 211 first-party `../../../src/` sources. Inspection copies were
extracted to `/workspace/tmp/piclaw-classic-source` (not production dependencies).
Actual `/editor-vendor/codemirror.js` resolves to
`runtime/extensions/viewers/editor/vendor/codemirror.js`, not the similarly named
common/static vendor. The latter lacks the required `toml` export.

Initial tablet empty-chat capture delivered from actual classic index/bundle.
Auxiliary fixture endpoints are still incomplete; not acceptance evidence.

## Confirmed structural anchors

- `ui/app-main-shell-render.ts`: `app-shell` with workspace-collapsed,
  editor-open, chat-only and zen-mode state, NOT visual's activity-bar shell.
- `ui/app-main-shell-composition.ts`: main shell composition.
- `components/compose-box.ts`: compose footer with connection status,
  model metadata, attachment/send buttons and optional controls.
- Classic composer uses `compose-*` structure, not visual `chat__*` markup.

## Bounded implementation sequence

1. Finish actual classic reference fixture with explicit endpoint inventory;
   capture populated phone/tablet/desktop and inspect header/timeline/composer.
2. Map classic shell, timeline rows and composer to Tau's state/adapter anchors.
   Preserve APIs and mounted forms, not wrong-mode visual wrappers.
3. Port classic shell/composer and its stylesheet dependencies together. Avoid
   visual CSS plus overrides masquerading as classic.
4. Port message/tool rendering and applicable side panels; keep unsupported
   actions absent rather than invent backend behavior.
5. Replace wrong-target asset pins and reference tests; retain behavior tests
   where semantics still apply. Verify accessibility and package delivery.
6. Deliver labeled classic/Tau comparisons for explicit visual acceptance.

## Explicit user correction implemented

`b238fd7`: removed visible Run/Follow-up/Steer selector; hidden adapter anchor
retained, default run submission unchanged. Send accessible label corrected.
Composer matrix 12 passed; frontend/packaging 44 passed; frontend build,
TypeScript and diff checks passed. This is not the broader classic port.

## Populated reference checkpoint

`tests/browser/audits/capture-classic-reference.mjs` is an initial local capture
probe, not yet a portable regression test. Populated tablet capture delivered;
zero unknown endpoints and zero page errors on the successful run. Classic
posts require `{id, timestamp, data:{type, content}}`, with `agent_response` /
`user_message` types, unlike the earlier visual fixture. Auxiliary responses
are minimal idle mocks, not proof of those features. Timing and paths still
need normalization before the full comparison matrix.
