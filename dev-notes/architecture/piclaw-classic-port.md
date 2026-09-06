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

## Rejected component comparisons removed; Plan coverage retained

Removed five tests importing visual MessageItem/tool/Markdown implementations or
asserting visual control CSS: collapsed-reference, message-reference,
tool-reference, markdown-reference, control-styles. Behavior remains covered by
classic-frame, message-copy, tool-output, markdown, collapse-edge and a11y specs;
new genuine classic paired visual evidence still pending (not replaced by self
baselines). Next capped full triage: 40 passed, 8 failed, 1 interrupted, 341 not
run. Migrated Plan/conflict and Workspace/Plan accessibility navigation, retaining
all state/contrast/bounds assertions: 18 passed. No production changes.

## Setup reopening overlay fix

Migrated onboarding layout spec to classic container, adding unsent draft
preservation. Exposed mobile/tablet sidebar intercepting wizard Cancel after
reopening setup from Settings. Settings now dispatches tau:close-drawers before
opening wizard; no forced clicks. Setup + full classic-live matrix 42 passed;
build/TypeScript pass. Composer remains mounted and retains draft.

## Responsive UTF-8 workspace regression

Migrated responsive test to classic session pill/navigation and Send (no Run).
Retained actual directory/file keyboard activation and café/日本語 file-content
checks. Exposed concatenated accessible names (`notesdirectory`); workspace
items now have explicit filename aria-label. Responsive + pane a11y matrix
18 passed; build/TypeScript pass. Visual workspace styling still needs review.

## Whole-page accessibility migration

Retained global axe and keyboard-focus indicator test, replacing visual shell
controls with classic Send/session pill and compose-input-wrapper. Whole-page
scan caught WebKit native dark background on Provider setup trigger, missed by
chat-scoped tests; applied scoped button color/appearance. Both themes/six-target
matrix 12 passed, including visible focus after Ctrl/Cmd-N and phone navigation.

## Capture migration to classic-only output

Migrated layout-audit/populated-layout to classic navigation, post/tool selectors,
hidden-live status and classic geometry inventory. Outputs use new
`tau-classic-audit` / `tau-classic-populated-review` directories, preventing silent
mixing with rejected visual-mode captures. Chat/Workspace/Search/Settings capture
matrix 18 passed. These are Tau-only captures pending genuine classic pairing.

## Third capped triage / Search migration

Capped full run reached 52 passed, 6 failed, 1 interrupted, 331 not run. Next
failures are Search/session/Settings navigation assumptions. Migrated populated
Search rendering and both-theme a11y specs to session-pill navigation, preserving
snippet/margin/action and contrast/bounds checks: 18 passed. No production changes.
Full browser suite remains unresolved; log /workspace/tmp/classic-triage-third.log.

## Settings/session regression migration

Updated Settings layout/axe and session event tests to classic session-pill
navigation. Preserved Settings form DOM identity, keyboard category activation,
control bounds, both-theme axe checks and selected-session event. Replaced
obsolete EventSource mock with persistent fetch SSE fixture for sessions.
24 checks passed. Settings currently occupies secondary sidebar, a Tau-specific
placement still subject to visual review; no production change in this pass.

## Fourth triage / timeline-workspace migration

Capped full run reached 168 passed, 6 failed, 1 interrupted, 215 not run.
Migrated remaining timeline/workspace specs to classic post/file/tool structure
and secondary navigation. Retained correct tool-result association, code payload,
annotations/editor data and chronological visual order; replaced wrong visual
DOM-reversal/10px-gap assertions with classic chronological DOM and composer
boundary checks. Focused matrix 18 passed. Full suite still needs rerun.

## Complete browser run and remaining-failure corrections

Complete suite at 3e3446c: 380 passed, 7 failed, 3 documented WebKit offline
skips. Six failures were WebKit native-button contrast in Dashboard/onboarding;
one Search fixture race. Scoped Dashboard/secondary wizard button appearance,
isolated Search fetch SSE and awaited Dashboard setup dismissal. Affected matrix
30 passed after fixes. Complete suite still needs rerun; no green full claim yet.

## Combined classic-only regression checkpoint (e478647)

Complete browser rerun: 387 passed, 3 documented WebKit offline skips, no
failures (390 total). Complete Python rerun: 1326 passed. Diff checks clean.
This verifies functional/interaction migration, not classic visual acceptance.
The remaining full-reference capture spec still targets the rejected visual
bundle and must be replaced; passing it does not contribute classic parity
proof. Fresh installed-classic artifact and paired screenshots remain pending.

## Genuine classic reference matrix replaces visual bundle

Replaced full-reference.spec's visual bundle fixture with actual classic index,
classic bundle and correct editor-vendor asset. Uses fixed time/shared message
text, persistent connected transport, expected model, explicit manifest and idle
API fixtures; rejects unknown endpoints/page errors. All 12 engine/size/theme
captures pass. Outputs /workspace/tmp/piclaw-classic-reference. Tool output is
not added to reference posts (classic live-status semantics differ); Tau pairing
must use equivalent message-only fixture, not imply identical tool presentation.

## Genuine classic paired chat delivery

New classic-paired spec uses shared message-only content, fixed time, matching
2m/1m labels and model; no tool result injected into either post sequence.
Genuine classic + Tau matrix 24 passed. Replaced review exporter input paths
with classic-only outputs and removed old visual/panel options. Delivered
Tau-Piclaw-Classic-Paired-Review.html with 12 labeled pairs. Identity/session/
runtime/action differences remain visible. This is evidence for review, not
acceptance; no pixel score or self-approved screenshot baseline used.

## Fresh reproducible classic artifact (afbdf82)

Built twice with SOURCE_DATE_EPOCH from afbdf82: byte-identical wheel.
SHA-256: 1ed5ff8e07a3af32e2b6e3a1fed40275f3e0d2f7244b3a5b65991a80e8dfd14b
Filename: tau_prime-42.3.0-py3-none-any.whl. Delivered wheel/checksum to chat.
Installed separately, tested using TAU_BROWSER_BIN audit venv and port 8877
(no checkout PYTHONPATH): classic root sending/navigation, populated a11y,
asset/font loading + removed-asset 404 checks, real SSE recovery: 60 passed.
This supersedes the earlier visual-mode wheel; visual acceptance still pending.

## Fixture/documentation cleanup

Removed unused visual Piclaw post/meter payloads, renamed shared fixture to
classic-state.mjs and updated all consumers. Browser README now documents actual
classic bundle pairing and classic asset checks, not PICLAW_VISUAL_SOURCE.
Reference/paired/populated capture matrix 36 passed. No runtime changes.

## Reference-driven composer correction

Current genuine DOM/CSS inspection revealed obsolete session-switcher class names
in the initial adapter. Replaced with compose-session-trigger-group/top/pill and
compose-current-agent-label; attach/send now include actual icon-btn class.
Classic session trigger overlays the top-right input rather than a separate row;
updated spacing check to require reserved text space. Tau's longer session title
needs right-padding on desktop too (scoped adaptation). Classic component/pair/
a11y batch had 54 passes with 12 outdated spacing failures; corrected spacing+
a11y matrix passes 24/24. Further refreshed paired review remains needed.

## Working classic resize handle

Refreshed comparison found matching column/footer dimensions; missing classic
resize handle accounted for remaining 8–10px composer height difference. Added
pointer capture plus ArrowUp/Down/Home keyboard resize, preserving draft. Uses
CSS responsive minimum (50px mobile, 70px desktop); textarea flex disabled while
applying explicit size. Six-target resize checks pass; build/TypeScript pass.
Final geometry and full regression must be rerun after this functional addition.

## Resize limits and refreshed geometry

Corrected resize clamp/ARIA to match classic responsive minimum/maximum rather
than assuming 50px/50vh everywhere. Tests verify pointer/keyboard, completion
rerender persistence, max clamp and Home reset: 6 passed; build/TypeScript pass.
Refreshed Tau pairs: 12 passed. Chromium light phone/tablet/desktop composer
heights now equal genuine classic (102/105/125px) with zero y delta. This bounded
geometry evidence is not full visual acceptance; identity/runtime/panels remain.

## Full post-resize checkpoint (f43ccbb)

Complete browser suite after real classic reference and resize integration:
405 passed, 3 documented WebKit offline skips, no failures (408 total).
Focused frontend/packaging 42 passed; diff checks clean. Regenerated and delivered
classic paired review HTML after composer corrections. Latest installed artifact
predates resize and needs refresh. Visual approval still not recorded.

## Installed post-resize artifact (8cecf00)

Rebuilt twice at SOURCE_DATE_EPOCH from 8cecf00: byte-identical classic wheel.
SHA-256 eb308c02af6b6a90dfd145d800f40dabe61ad3b0dc4b8bf4356f66f70912c1e0
for tau_prime-42.3.0-py3-none-any.whl. Delivered with checksum using valid wheel
filename. Separate installed audit venv, TAU_BROWSER_BIN and port 8877: 72 root,
submission/resize, populated accessibility, asset and spacing checks passed.
This supersedes afbdf82 artifact; explicit visual approval remains outstanding.

## Classic Markdown/code wrapper correction

Removed remaining visual message-list/code-block header and Codicon markup from
MarkdownContent. Uses actual classic post-code-block/post-code-copy-btn structure
with full Unicode copy payload and retained sanitizer/status feedback. Code copy
currently has text label rather than upstream SVG; large-code collapse remains
unported. Markdown safety/copy, populated a11y and paired captures: 30 passed;
build/TypeScript pass. Existing artifact/review predates this correction.

## Large-code collapse port

Added classic >40 lines / >24KiB code collapse with 16-line CSS preview,
state-owned expand/collapse and keyboard-focus restoration after sanitized HTML
rerender. Copy retains full UTF-8 payload while collapsed. Labels use byte count
rather than upstream compact formatting. Markdown safety/copy + large-code tests
12 passed; build/TypeScript pass. Threshold behavior and styling derive from
classic post.ts. Artifact/full regression refresh still required.

## Code-collapse boundary validation

Added exact 40-line/24KiB threshold checks, final-newline accounting, UTF-8
byte-size case (8192 Japanese characters plus newline = 24577 bytes), and reset
of expanded state when message content changes. Complete Markdown matrix
18 passed across six targets. No production changes in this checkpoint.

## Large-code visual/a11y corrections

Expanded/collapsed long-unbroken-line scans found expand-button contrast failure.
Scoped primary color fixes it; corrected toggle ordering to prepend before pre,
as classic does (preserving its adjoining border rules). Both-theme/six-target
large-code a11y/bounds 12 passed; Markdown safety/boundary/copy 18 passed;
build/TypeScript pass. No page horizontal overflow in tested long-code states.

## Code-copy icon fidelity

Replaced temporary Copy text with trusted static SVG from classic post.ts,
added only after user Markdown sanitization. Accessible Copy code name and
clipboard success/error status retained. SVG visibility/empty visible label
checks added; Markdown plus populated/large-code a11y matrix 42 passed;
build/TypeScript pass. Current artifact/review refresh remains pending.

## Full code-block integration checkpoint (af9ef66)

Complete browser suite: 429 passed, 3 documented WebKit offline skips (432 total),
no failures. Focused frontend/packaging 42 passed; diff checks clean. Refreshed
classic paired HTML/PDF from this run, including code-wrapper/copy-icon fixes.
PDF cover's earlier through-f43ccbb label is stale provenance text; actual images
are the current full-run outputs. Current artifact still predates code changes.
Explicit visual approval remains outstanding.

## Installed code-block artifact (58e98bf)

Two SOURCE_DATE_EPOCH-pinned wheel builds byte-identical. SHA-256:
9f82a942db92b5940f2f45e7290979a145fde639794ffbb88b98a334dcdd6aff
(tau_prime-42.3.0-py3-none-any.whl). Separate installed runtime passed 90 checks:
classic root/resize, populated and large-code a11y, classic assets, Markdown
sanitization/copy/threshold behavior. Delivered wheel/checksum and revised PDF
whose cover now correctly cites af9ef66 code / 58e98bf full regression.
Visual acceptance remains pending; no production change in this checkpoint.

## Remaining-source audit checkpoint

No visual source paths, mode conditionals or visual stylesheet loads remain in
runtime TS/JS; only negative browser asset checks mention deleted asset names.
Corrected stale frontend README. Secondary panels still contain old class names
and some Codicon nodes (Workspace/SessionList/metrics/queue etc.); these are not
approved merely because core chat matches classic. Their visual conversion/review
remains explicit engineering work. Audit script directory contains only classic
capture probe; no visual reference source override remains.

## Workspace icon repair

Removed Workspace Codicon nodes left without a font after classic-only cleanup.
Parent/refresh now use inline SVG icon-btn controls; directory/file rows use
inline folder/file SVGs. Existing IDs/keyboard navigation/editor/annotations
preserved. Workspace/responsive/pane a11y matrix 24 passed; build/TypeScript pass.
Broader Workspace container styling remains a separate visual review item.

## Session/queue icon repair

New-session and queued-message copy-to-compose controls now use inline add/edit
SVGs, not unavailable Codicon font nodes. Queue test asserts actual SVG visibility
and absence of Codicons while retaining dispatch/copy checks. Queue/session/
keyboard matrix 18 passed; build/TypeScript pass. Queue container styling remains
part of secondary-surface conversion, not closed by this icon change.

## Classic queue structure

Replaced queue-stack visual-era classes with actual compose-queue-stack/item/
content/actions/edit/steer classes and list semantics. Tau-specific kind/error
labels retain explicit tau-* names. FIFO per-kind dispatch and copy-to-compose
unchanged; no unsupported reorder/remove added. Queue controls stay within
viewport; queue/populated matrix 18 passed; build/TypeScript pass. Populated
queue both-theme accessibility and reference assessment remain to check.

## Populated queue accessibility

Extended existing queue dispatch/copy test to both themes and axe. Found low
contrast on faded Dispatch text and dark queue content; scoped primary-text/
opacity rules correct these without vendor edits. Both-theme/six-target queue
matrix 12 passed with FIFO route/copy behavior and bounds checks retained.

## Telemetry state/control repair

Removed visual sys-stats/status-bar classes and Codicon nodes from SystemStats.
Tau metrics remain a secondary-panel feature with explicit tau-* styles, readable
text buttons and Preact hidden semantics for compact/disabled state. Prior CSS-
only states stopped working when visual CSS was removed. Added visible toggling
checks (compact/hide/show/expand) retaining metric values/severity/sparklines;
six targets pass; build/TypeScript pass. No visual-mode status strip restored.

## Classic session rows

SessionList now uses classic compose-model-popup-item/session-item/label/jid
structure with active state and aria-current, preserving Tau filters/select
callbacks and IDs. Scoped list/reset/label layout and selected-row contrast
adaptations replace missing visual session classes. Session/keyboard/populated
accessibility matrix 36 passed after fixing low accent text contrast;
build/TypeScript pass. No unsupported pin/restore semantics copied from upstream.

## Classic workspace rows

Replaced visual file-tree item/name/meta classes with classic workspace-tree-list,
workspace-row and workspace-label/text structure. Kept native button keyboard
semantics, explicit filenames, and existing click adapter. Scoped button reset
accounts for upstream div rows; no unsupported rename/drop interactions added.
Workspace/responsive/pane accessibility matrix 24 passed; build/TypeScript pass.
Preview/header container conversion still pending.

## Workspace header/preview conversion

Replaced remaining workspace__ visual wrappers with classic workspace header,
tree, preview/header/body/title classes and scoped Tau read-only source styles.
Removed nonfunctional separator rather than implying unsupported drag resizing.
Native textarea resizing remains available. Existing file navigation/UTF-8,
annotations and pane a11y checks pass 24/24; build/TypeScript pass. No editor,
rename or delete functionality invented. Paired panel visual review still open.

## Secondary-surface full regression and fixture isolation

Complete browser run after secondary conversions: 434 passed, 1 failed, 3
existing WebKit offline skips (438 total). Failure: WebKit phone threshold
fixture replaced during click by live session updates. Added selected-session
and persistent SSE isolation to all Markdown tests; focused 18 passed. No
production change for this failure. Full rerun remains required.
