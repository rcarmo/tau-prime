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

## Classic secondary navigation adapter

SidePanel/Sidebar internal classic mode exposes Tau panel navigation within a
classic workspace-header wrapper (no visual activity/sidebar markup). Retains
existing IDs and close/select callbacks. This is a Tau navigation adaptation,
not a replica of all Piclaw sidebar features. Six classic callback checks pass;
18 existing sidebar/workspace/search checks pass; build/TypeScript pass.
Panel internals and scoped CSS still need conversion before production cutover.

## Classic control icon independence

Replaced classic-mode copy/collapse and attach Codicon dependencies with inline
SVGs. Copy geometry taken from classic post.ts; disclosure/attachment are
classic-style outline adaptations. Added checks for SVG presence and absence
of Codicon nodes in these controls. Combined classic/message-copy/composer
matrix 48 passed; build/TypeScript pass. Attachment preview and secondary panel
icons still require audit at cutover; no whole-interface icon equivalence claim.

## Classic attachment links

Classic message attachments now use post-file-pill/name and inline file SVG,
with original encoded media URL/authenticated download handler preserved.
Current classic branch renders image attachments as file links too: image
preview parity remains open and must be resolved before acceptance/cutover.
Checks cover encoded text-file link and absence of visual attachment chip;
classic plus existing timeline matrix 36 passed; build/TypeScript pass.

## Classic image previews

Classic image attachments now render media-preview thumbnails rather than file
pills. Filename alt text and encoded content link retained; existing authenticated
thumbnail/blob lifecycle and download handler reused. Checks verify src/alt/link
markup (not image decoding or an upstream lightbox); classic matrix 30 passed,
build/TypeScript pass. Tau still opens/downloads media, not Piclaw's lightbox.

## Real adapter preview cutover

`/?ui=classic` now assembles classic frame/timeline/composer/status/session and
secondary navigation against actual app.js, removing visual styles in this
preview only. Default unchanged. Metrics remain mounted in sidebar; forms and
approval/dashboard retained. Scoped tau-classic.css handles semantic hidden,
flex/adapter wrappers and completion list reset; no vendor edits.
Real-adapter six-target boot/navigation checks pass with zero page errors;
build/TypeScript and focused Python 46 pass. Panel styling, responsiveness,
submission/end-to-end behavior and screenshot review remain before default
cutover. Preview is not visual acceptance or offline-cache coverage.

## Integrated populated captures

classic-live.spec now captures populated preview across both themes and all six
targets with selected session and persistent synthetic SSE. Message text matches
the classic probe; timestamps/identity are not yet normalized for pixel review.
18 boot/populated checks pass, including textarea bounds and no horizontal page
overflow. Delivered tablet preview screenshot. Runtime/branch placement and
secondary panel appearance remain open; these are not acceptance captures.

## Integrated composer submission checks

Added classic-preview tests using real app.js and isolated POST /sessions/id/runs
responses (no model execution): Send click and Enter preserve exact content;
Shift+Enter inserts a newline without submission; rejected request retains draft
and re-enables Send; successful retry clears draft. Delivery selector remains
hidden. Both methods across six targets pass 12/12. Backend payload unchanged.

## Integrated secondary-panel reachability

Classic preview now has real panel-switching checks for Workspace/Search/Plan/
Settings, horizontal form-control bounds, scrolling to the last Settings button,
and closing Settings back to the composer. Six targets pass. No production fix
needed in this check; reachability is not visual/a11y approval of panel styling.

## Integrated accessibility correction

Both-theme classic chat/session navigation/Search/Settings axe scans exposed
low model text contrast, invalid aria-selected on ordinary navigation buttons,
and WebKit native-button dark backgrounds. Corrected pressed semantics and
scoped classic control/text colors/appearance without modifying vendor CSS.
Full six-target/both-theme scan 12 passed (four surfaces each); TypeScript passed.
Scans currently use idle/empty content, not complete populated message coverage.

## Classic-only direction (Rui correction)

Classic is now the sole root shell: no query switch or alternative render branch.
HTML/service worker use classic CSS plus scoped Tau adaptations; cache advanced
to v12. Deleted visual reference/parity CSS and both visual-only JetBrains fonts,
and removed their public routes and replaced wrong-reference packaging tests.
Classic root integration 36 passed; updated frontend/packaging 42 passed.
Obsolete visual component branches/tests still need removal. Populated dark axe
scan currently has unresolved failures; do not treat default cutover as complete
visual/accessibility acceptance. Prior preview wording is superseded.

## Populated accessibility at classic-only root

Resolved completion-description contrast and WebKit native styling on Tau's
persisted-tool disclosure button. Scoped style uses primary text and transparent
button background, retaining upstream CSS bytes. Full populated axe plus root
integration matrix: 48 passed (12 accessibility runs over four surfaces and 36
boot/capture/submission/navigation checks). This supersedes the earlier populated
dark failure, but is not whole-application accessibility or visual acceptance.

## Obsolete shell/theme removal

Deleted unreferenced visual ActivityBar/TabBar and visual JS theme modules,
plus the rejected TabBar parity spec. Replaced system-theme expectations with
classic --bg-primary media-query behavior and absence of visual stylesheet
links. Theme preservation test now compares classic vendor/scoped styles.
12 theme checks pass; build/TypeScript pass. Remaining dual component branches
and other visual fixture tests are still pending cleanup.

## Classic-only footer implementation

Deleted visual StatusBar render branch and unused session/meter props. The
single footer implementation retains model/connection events and Dashboard
access. Metrics continue in the secondary sidebar; session pill stays in the
composer row. Updated live/fixture callers. Classic frame + real adapter suite:
66 passed; build/TypeScript pass. Remaining dual-mode components still pending.

## Classic-only composer cleanup

Removed Composer mode prop, visual layout branch, conditional visual classes
and Codicon alternative. Classic surface is now its sole layout. Updated live
and fixture callers and existing attachment behavior test selectors. Classic
frame/root matrix 66 passed; composer regressions 12 passed; build/TypeScript
pass. Timeline/action/sidebar dual branches are separate pending cleanup.

## Classic-only timeline cleanup

Deleted visual post/tool/attachment branches and Timeline mode prop. Retained
classic chronological DOM order and shared state/download/clipboard handlers.
Updated callers; no visual message-list wrappers in Timeline rendering.
Classic component/root/accessibility matrix 78 passed; build/TypeScript pass.
Old visual-oriented specs still need replacement; these results are the named
classic suites, not a clean full legacy browser run.

## Classic-only message actions

Removed mode props and visual/Codicon alternatives from MessageActionBar and
CopyButton, updated Timeline callers. Classic clipboard feedback now uses
is-success/is-error state classes. Added message copy failure then retry checks
with exact copied Markdown; existing collapse-focus checks retained. Classic
components/populated accessibility: 42 passed; build/TypeScript pass.

## Classic-only sidebar wrapper

Removed Sidebar/SidePanel visual branches and mode props; navigation controls
are always available in classic secondary panel. Renamed legacy tab helper to
PanelNavigationButton. Removed obsolete visual Sidebar parity spec; classic
navigation/closure and accessibility coverage retained. Classic suite 78 passed;
frontend/packaging 42 passed; build/TypeScript pass.

## Classic-only offline cache validation

Service-worker spec now checks v12, classic CSS/adaptation assets, exactly two
font assets, no visual CSS/JetBrains entries, and no cached API data. Offline
Chromium asserts classic app-shell rather than rejected activity bar. Matrix:
9 passed / 3 existing documented WebKit offline skips. No skip was removed or
newly hidden. Remaining visual-reference test inventory is still being replaced.

## Browser asset-test replacement

Replaced visual-assets spec with classic-assets: both Fira Code fonts load via
FontFace under actual page CSP, composer SVG controls render, visual CSS links
are absent, and four removed visual assets return 404. Six targets pass.
Removed shell-styles spec whose only assertion preserved the rejected visual
shell geometry; classic-frame supplies the correct structural coverage instead.

## Classic-only Python checkpoint (4358283)

Complete Python suite: 1326 passed in 73.39s with PATH=.venv/bin and
PYTHONPATH=src:. Count differs from historical baselines because rejected
visual asset tests were replaced, not because this is the same suite unchanged.
Browser classic-focused suites are green as recorded above; full legacy browser
suite is not yet reconciled and no full-browser success is claimed.

## Retained action-regression migration

Migrated existing message-copy and tool-output specs to classic selectors and
labels, retaining Unicode/raw Markdown copying, clipboard rejection/retry,
keyboard focus restoration and exact full-output/tail assertions. These are
behavior tests, not deleted visual parity assertions. Six-target matrix 12
passed; production code unchanged in this checkpoint.

## Classic real-network recovery regression

Migrated connection tests from visual dot classes to classic label visibility:
live hidden, disconnected/reconnecting visible. Dismiss setup before asserting
composer visibility (previous status strip existed outside that setup surface).
Real backend sessions and actual network interruption/recovery plus injected
state matrix: 12 passed. No production behavior change in this checkpoint.

## Dashboard classic navigation regression

Retained focus/inertness and real-backend accept/decline tests. Updated Plan
access through classic session navigation, closed overlay sidebar before clicking
Dashboard, and awaited setup cancellation in focus test. These are actual user
steps, not forced clicks through overlay. Full matrix 18 passed; no Dashboard
production fix required. Unsaved plan stays intact when session switch declined.

## Full browser triage and content regression

Ran full browser suite with max-failures=12: 31 passed, 12 failed, 1 interrupted,
376 not run. Failures mix removed visual fixtures/selectors and migration gaps;
this is not a full green run. Migrated Markdown sanitization/Unicode code copy
and collapse-edge specs; restored missing truncated-preview ellipsis in classic
MessageItem. Await setup dismissal before interacting. Focused six-target matrix
12 passed; build/TypeScript pass. Remaining triage log:
/workspace/tmp/tau-classic-full-triage.log.

## Keyboard regression migrated

Keyboard test now opens session pill and classic secondary navigation instead
of activity/mobile-toolbar buttons. Keeps session creation/selection, Ctrl/Cmd-K,
new-session shortcut, slash completion dismissal, Tab/Shift-Tab traversal,
keyboard workspace reload, and Escape closure assertions. Six targets pass.
No production change required in this checkpoint.

## Composer spacing and model options regression

Replaced obsolete visible delivery/context wrapping assertions with classic
session-above/input/footer-below geometry and hidden legacy delivery/context
anchors, even with long context text. Updated model-option Settings navigation;
provider/model/thinking event ownership assertions retained. Matrix 18 passed.
No production code changes in this checkpoint.
