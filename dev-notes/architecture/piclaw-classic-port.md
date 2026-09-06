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

## Concrete shell adapter map

Observed classic tablet DOM at 820×1180 (populated idle fixture):
`app-shell.workspace-collapsed` fills viewport; `.container` is centered at
x=41, width=738; `.timeline.reverse` occupies y=0..1075; `.compose-box` is
105px high, with a 50px textarea and 26px footer. These are fixture observations,
not universal dimensions to hard-code.

| Current Tau owner | Classic structure to port | Preserve |
| --- | --- | --- |
| TauShell / ActivityBar / TabBar | app-shell + workspace-sidebar + centered container | session and panel selection callbacks; mounted settings |
| Timeline | timeline.reverse > timeline-content > post | message IDs, chronological presentation, tool association, copy/collapse |
| Message content | post-avatar + post-body + post-actions | Tau identity, sanitizer and clipboard failure handling |
| Composer | compose-box + resize handle + textarea + compose-footer | compose-form/input/submit anchors, upload, completions, Enter semantics |
| StatusBar | applicable compose-meta-row / model hint | model/context/connection adapter events; no separate visual status strip |

Do not hard-code the 738px measured width: import the classic layout rules and
verify responsive results. Runtime/queue/approval extension surfaces need explicit
placement during shell conversion, not removal to reduce screenshot differences.
The reference capture now fails on unknown endpoints/page errors and waits for
actual message/font readiness; it also exports a bounded DOM/geometry inventory.

## Classic asset staging

Vendored untouched classic bundle CSS as `static/piclaw-classic.css`, separately
from rejected visual reference. Registered public CSS route; SHA-256 pinned to
632b049f34a164f73b4f2a379d4bfc4ee76327955b32331c9af6db28281b0ab6.
Both referenced Fira Code fonts are byte-identical to already bundled/noticed
files. Added wheel-byte/font-reference checks and route coverage: focused
frontend/packaging 46 passed. The main page does NOT load this CSS yet: classic
components must replace visual markup before stylesheet cutover.

## Classic frame component

Added ClassicChatFrame with upstream app-shell/workspace-sidebar/container
hierarchy and slotted Tau content. Sidebar becomes inert when collapsed.
Not connected to live TauShell until child markup conversion is ready.
Isolated both-theme six-target checks pass 12/12 using classic CSS only:
centered bounded column, viewport height (0.02px WebKit rounding tolerance),
no visual activity/tab/status wrappers, and visible composer placeholder.
TypeScript passes. This checks frame structure, not whole-UI parity.
