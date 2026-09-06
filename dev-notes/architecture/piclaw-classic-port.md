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

## Classic composer surface

Added ClassicComposerSurface from actual classic compose-box hierarchy:
compose-input-wrapper, top session row, input-main, footer meta/actions.
Slots preserve Tau ownership of inputs and handlers; no delivery selector or
unsupported inert resize handle introduced. Integrated into isolated frame
fixture; 12/12 checks pass including footer below textarea and session/model
rows. TypeScript passes. This is staged structure, not live adapter cutover.

## Classic post structure

Added ClassicPost using classic post/avatar/body/actions/meta/content hierarchy.
Tau identity and actions are supplied by caller; no copied Piclaw identity or
unsupported delete action. Uses semantic article and noninteractive timestamp
until permalink behavior is wired. Combined staged frame/composer/posts pass
12/12 both-theme/engine/viewport checks, including chronology and messages above
composer. TypeScript passes. Live Timeline adapter remains to be switched.

## Timeline adapter integration

Timeline/MessageItem now accept internal classic mode, consume the same Tau
render events and use ClassicPost with chronological classic timeline-content.
Copy/collapse state and focus reuse existing handlers. Default remains old mode
until shell/composer cutover. Tool/attachment/code inner markup still needs
classic conversion; this is not full message fidelity. Combined classic frame,
real timeline event/collapse and existing message-copy checks: 24 passed.
Frontend build/TypeScript pass; generated bundle updated.

## Composer adapter integration

Composer now shares input, attachment, completion and hidden adapter controls
between default and internal classic layouts, using ClassicComposerSurface.
Classic mode hides legacy context/delivery controls, places attach/send in the
footer, and accepts session/model slots. Live default unchanged pending cutover.
24 classic frame/timeline/composer checks and 12 existing composer checks pass;
TypeScript/build pass. Completion and attachment styling still needs conversion.

## Composer file/completion markup

Classic mode now uses compose-file-pill/name/remove and clear-button classes
from FilePill/compose-box, plus slash-autocomplete/item/name/desc markup.
Listbox semantics remain Tau-owned (list reset to be included in scoped classic
adaptation stylesheet at cutover). Attachment removal event and completion
selection state checked; combined classic/existing composer suite 36 passed.
Build/TypeScript pass. No live-shell switch in this checkpoint.

## Tool output adaptation

Classic mode tool results now use agent-thinking/title/body structure from
classic status.ts, retaining Tau's persisted input/output and tail/full controls.
This is an explicit backend adaptation: classic normally presents this in live
status panels, not visual-mode tool cards. Copy feedback handler reused with
classic button class. Exact tail/full content checks plus classic and existing
tool matrix: 30 passed; build/TypeScript pass. Default live shell unchanged.

## Classic footer status adapter

StatusBar internal classic mode now consumes existing model/connection events
inside composer metadata, hides connected status (matching classic), and keeps
Dashboard action/count anchors. Session control is supplied by composer session
slot; SystemStats must move to a secondary surface at cutover, not disappear.
Classic CSS overrides display on the connection class, so hidden state lives on
an unstyled wrapper. Classic/status matrix 30 passed; build/TypeScript pass.
Live shell still unchanged.

## Classic session trigger

Added ClassicSessionControl using classic trigger/pill/label/chevron hierarchy,
retaining status-session adapter ID and expanded/controls semantics. Composer
fixture verifies label mutation and navigation callback. Classic matrix 24
passed; TypeScript passes. This is still staged; it does not itself implement
the session navigation surface or replace the live shell.
