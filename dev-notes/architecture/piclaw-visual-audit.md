# Piclaw visual port audit — resumed 2026-09-05

## Baseline and source

Tau baseline: `773568d`, branch `feat/hf-upgrades-and-ui-parity`, clean before this pass.
Historical functional results (not visual approval): 1322 Python tests and 84 browser tests.
Reference now pinned to installed Piclaw **2.15.3**, rather than the obsolete 2.13.2 plan target.
Source: `/opt/piclaw/releases/piclaw-2.15.3-linux-x64-baseline/app/runtime/web/static/visual/`.

## Verified findings

- Tau used a modified 2.13.1 stylesheet. File-size differences alone do not establish which styles were missing or prove a visual root cause.
- Replacement `piclaw-reference.css` is byte-identical to Piclaw's `dist/app.bundle.css`: SHA-256 `50e8f293f4553cae89a383b2c35497c0a31c442a734ff38e858d7d3244e007ad`.
- The bundle references four local fonts, now copied alongside it. Tau previously had no corresponding font routes or font packaging suffixes; both have been added.
- Piclaw's App renders settings in the main panel, a real TabBar, conditional editor/widget views, and ProviderWizard inside the chat viewport. Tau currently renders its own settings sidebar and external onboarding modal. Those are not equivalent structures.
- Piclaw ActivityBar uses its Icon component; Tau uses codicon class elements. This requires actual glyph and computed-style inspection, not a static class count.
- Tau's compatibility CSS still overrides shell surfaces, controls, sidebar layout, and dashboard layout. Exact CSS replacement does not eliminate these differences.
- Static class-name differences are inventory clues only; interpolated classes and intentionally unsupported Piclaw features prevent treating counts as parity measurements.

## Changes and checks this pass

- Vendored exact 2.15.3 CSS plus four external font files; included Piclaw MIT notice.
- Added explicit public binary font routes and `.ttf`/`.woff2` wheel packaging support.
- Added font route MIME/status coverage.
- Made Playwright server port configurable using `TAU_BROWSER_PORT`. Port 8765 currently hosts an unrelated `vibes.app`; it was not stopped.
- Python frontend/packaging checks: **42 passed**.
- `TAU_BROWSER_PORT=8876 npx playwright test specs/responsive.spec.mjs specs/accessibility.spec.mjs --reporter=line`: **12 passed**.

These checks prove functional compatibility only. They do not approve visual parity.

## Browser-verified font defect and correction

The new `visual-assets.spec.mjs` reproduces an actual rendering failure: all four external fonts loaded, but `document.fonts.load()` failed for Codicon in the exact Piclaw bundle. Its embedded data-URL font was blocked by Tau's `font-src 'self'` CSP. Allowing `data:` specifically for fonts fixes the failure without broadening script/style policies. ActivityBar also lacked Piclaw's `icon--size-24` class; this is now mapped explicitly.

After correction: all six Chromium/WebKit viewport projects pass actual font loading, nonempty glyph content and 24px icon sizing checks. Frontend/packaging tests remain 42/42; TypeScript `tsc --noEmit`, bundle build and `git diff --check` pass. This is asset-level evidence, not full visual parity. Delegation was attempted but unavailable under the current model policy.

## Direct TabBar comparison

Added logical Tau `TabBar.tsx` matching Piclaw's single, nonclosable Chat tab state, including the previously missing label wrapper. `tab-bar-parity.spec.mjs` compiles the actual installed Piclaw component and Tau's component against identical CSS and data; checks HTML and selected computed styles in all six browser/viewport projects. Reference source can be supplied through `PICLAW_VISUAL_SOURCE`; the default is the pinned installed 2.15.3 source, which is a test prerequisite.

The comparison initially failed after loading Tau's compatibility sheet: its global body font override replaced Piclaw's IBM Plex Sans/Inter stack with a different system stack and changed label height. Removed that override; the comparison now passes. This fixture covers only the tab strip, not the full shell or pixel parity.

Following rebuild and TypeScript check, the entire browser suite passes **96/96** (including the 12 new asset/component checks). `git diff --check` passes.

## Direct Sidebar comparison

Extracted Tau `Sidebar.tsx` using Piclaw's container hierarchy, keeping optional Tau IDs/accessibility labels and drawer actions in SidePanel. Default shared-title/content fixture matches genuine upstream Sidebar HTML and selected computed styles. The first comparison exposed Tau's `--accent` alias overriding Piclaw's sidebar-title blue (`rgb(37, 99, 235)` became `rgb(29, 155, 240)`). Removed the accent aliases instead of adding a corrective selector.

Sidebar, tab-bar and responsive/workspace checks pass **18/18** across all viewport/engine projects; frontend/packaging checks **42/42**, rebuilt bundle and TypeScript pass. Drawer actions and populated sidebar panels are intentionally not yet covered by the isolated upstream fixture.

## Full-shell capture checkpoint

`layout-audit.spec.mjs` captures current Tau empty-shell and open-workspace states across six engine/viewport projects (12 images). Captures saved under `/workspace/tmp/tau-audit-september` and attached as an archive. These are work-in-progress audit captures, not approved references; a matching full Piclaw fixture is still required.

Added a built-wheel test verifying the exact bytes of CSS, all four referenced fonts, and Piclaw's license notice survive packaging. Packaging tests pass 7/7. This verifies archive contents, not installed-server browser loading or font licensing completeness.

## Settings placement correction

Extracted `SettingsPanel.tsx` and placed it directly in the central pane, matching the placement in upstream App. Settings hides the sidebar and chat viewport; clicking Settings again returns to chat. Tau forms stay mounted while hidden so app.js listeners and captured element references remain valid. This is a placement correction, not a claim that the settings internals match upstream.

New settings-layout test verifies central placement, hidden sidebar/chat, visible auth control, return navigation, and stable form node identity: 6/6 projects pass. Related model/keyboard/accessibility checks pass 18/18. Frontend/packaging tests pass 43/43; build, TypeScript and diff checks pass.

## Root token audit

Added browser comparison of every computed root custom property defined by Piclaw before/after Tau's compatibility CSS. This found two further collisions: `--border` changed from `#d4d4d4` to `#eff3f4`; `--text` from `#1e1e1e` to `#0f1419`. Removed both aliases. Root-token, Sidebar, TabBar and settings-layout tests pass **24/24** across Chromium/WebKit and all widths. This checks the default root theme only; descendant overrides and other theme states still require inspection.

## Standard control styles

Added representative standard-control computed-style comparison (provider primary, modal primary, send button, settings input/select, chat textarea) before/after compatibility CSS. It exposed forced `-webkit-text-fill-color` changing component-specific button text colors. Removed the global button/input/textarea/select/option color, border and background overrides. Disabled transitions/animations in this isolated measurement to avoid comparing intermediate interpolation values; no component colors or geometry are masked. Control-style, accessibility and model-control checks pass **18/18** across all six targets.

## Onboarding placement

Provider setup now uses the inline provider-wizard container/content classes inside the central tab viewport, not an aria-modal overlay. Chat remains mounted but hidden while setup is open. Reopening from settings switches back to the central chat view. Tau provider/model/credential API behavior remains unchanged; provider selection internals still differ from Piclaw's broader OAuth/custom-provider flow.

Bootstrap assertions now wait for the composer to be attached, not visible before onboarding is dismissed. Full existing browser suite passes 126/126; new explicit wizard-placement/cancel/reopen checks pass 6/6; frontend/packaging 43/43, build and TypeScript pass.

## Regression checkpoint

Full Python suite after the current asset, CSS, settings and onboarding corrections: **1327 passed**. Added embedded Codicons attribution and upstream CC BY 4.0 license to `FONT-LICENSES.md`; packaging checks still 7/7. These changes are checkpointed as partial visual-port corrections, not final delivery. Latest full browser run was 126/126 before adding the six passing onboarding-placement checks; a combined rerun remains required after subsequent changes.

## Installed-wheel browser verification

Built the wheel into `/workspace/tmp/tau-wheel-audit`, installed its `[web]` extra in a separate uv environment at `/workspace/tmp/tau-installed-audit`, and ran the font-loading, onboarding and settings-layout matrix against that executable on port 8877: **18/18 passed**. Launcher now supports `TAU_BROWSER_BIN` and deletes inherited PYTHONPATH in installed mode. Verified `tau_web.__file__` resolves under the separate environment's site-packages, not the source tree. Harness options documented in tests/browser/README.md.

## Shell CSS interference check

Added reduced App-container geometry fixture with identical markup before/after the compatibility stylesheet. It exposed `#app { display: contents }` replacing upstream's flex mount and a global sidebar-wrapper width of zero replacing upstream's 200px default. Removed both overrides; Tau's explicit state-controlled inline width still controls its own sidebar. The reduced shell, responsive/workspace and onboarding matrices pass 18/18. This is a CSS-interference check, not a genuine full-App or populated screenshot comparison.

## Timeline structure and open contrast regression

Removed Tau's unstyled ordered-list wrapper/list-item markup in favor of div message items, following upstream MessageList/MessageItem. Preserved timeline IDs/live region. Build/TypeScript and six timeline browser checks pass. Accessibility rerun fails in all six projects: delivery selector and model status have insufficient contrast after accumulated theme/layout corrections. Removing the selector's forced white background does not resolve this. Investigate the mixed theme/component token mapping before sign-off; do not count accessibility as green.

## Missing runtime theme initialization

Tau had no equivalent of Piclaw ThemeProvider: no light/dark root class and no runtime theme tokens. Added upstream theme.ts values plus system-theme application and change listener before render. Six browser projects verify light/dark class and background token changes; TypeScript passes. Corrected delivery selector's use of thinking-badge to settings-select styling, and removed error-banner styling from neutral timeline metadata. Accessibility remains red: status connection/model badges have contrast failures under the now-correct light background; inspect status component mapping next. Do not claim the theme fix alone resolves accessibility.

## Settled-state accessibility correction

Status model text is now Preact-owned, with upstream provider/name/empty wrappers and actual empty-state class switching rather than a permanently empty badge. Documented narrow accessibility exceptions use theme foreground on light connection/empty-model/compact-meter labels and sidebar title, and remove opacity reduction on mobile hover/provider prefixes. Tau's persistent branch section uses `--text-muted`, not legacy `--textMuted`.

An intermittent branch-text failure was sampled during upstream `agentFadeIn` (200ms). Accessibility scans now await finite animations' finished promises (not infinite running indicators), preserving actual animation behavior. Six-project accessibility matrix repeated twice: **12/12 passed**. Full suite, dark-theme axe, and paired visual acceptance remain pending; exceptions are deliberate deviations and not evidence of pixel parity.

## Dark-theme accessibility

Accessibility spec now explicitly runs both light/dark schemes at all six engine/viewports. Added narrow dark-surface text-token corrections for neutral timeline/status labels and retained provider prefix opacity. WebKit dark revealed native session buttons because Tau-only classes have no standard style rules; action/filter/session buttons now also use Piclaw's existing settings button primitive. This fixes native-color fallback, not full session-card fidelity. Both-theme accessibility plus session interaction checks pass **18/18**; build/TypeScript pass. Full matrix and visual review remain open.

## Full matrix follow-up

Full browser matrix is currently **149/150**, not green. Timeline injection test overwritten by server state: isolated its SSE endpoint and sequenced startup's previously fire-and-forget session-filter refresh. Timeline passed in the next full run, but the composer attachment fixture then failed on WebKit desktop. Thus startup/fixture isolation is not yet verified complete; inspect composer failure before sign-off. No renderer assertions were weakened.

## Regression recovery verified

Inspection corrected the earlier composer diagnosis: it timed out in `page.goto` waiting for `load`, before any attachment assertions. The composer test now uses DOMContentLoaded followed by its existing attached/shell-ready checks. Full combined matrix now **150/150 passed**; full Python suite **1327 passed**; diff check passes. This supersedes the 149/150 checkpoint, but does not establish full visual parity.

## Genuine populated MessageItem fixture

First actual Piclaw MessageItem fixture renders successfully in Chromium desktop; capture attached. Uses pinned release MessageItem unchanged, fixed plain user content/time, separate origin for storage, and one shared Preact runtime. Release omits dependencies: audit directory supplies signals 2.11.2 and dompurify 3.4.14; missing browser-title formatter is stubbed (unused by message rendering). This is not yet paired with Tau, and font/Markdown library completeness must be checked before visual approval. Initial npm install resolved the parent workspace because the audit directory lacked a package.json; removed added parent dependencies and recreated a proper isolated package before continuing.

## Paired plain user message

Extended genuine MessageItem fixture to render Tau's exported MessageItem with identical plain content, timestamp label and no-uploaded-avatar state. All six projects match message/content width, height and whitespace mode. Captured both versions and DOM/geometry JSON, attached archive. Remaining DOM differences include upstream collapse/delete action bar and timestamp tooltip. This fixture has no Markdown vendor global and covers plain user text only; it does not validate rich agent Markdown, tools, complete chat or pixel parity. Build/TypeScript/diff checks pass.

## Tool output mapping

Adapted upstream ToolCallBlock structure: argument/result pre wrappers, copy controls, 20-line output tail with hidden-line expansion and collapse. Copy sends complete output, not just displayed tail; Tau's failed/done semantics retained. New CopyButton uses clipboard API with feedback and timer cleanup; fallback clipboard behavior remains a difference from upstream. Tool-output interactions and timeline tests pass 12/12 across all six targets; build/TypeScript pass. Direct paired tool geometry/screenshots are not yet implemented.

## Paired tool fixture blocker

Work-in-progress `tests/browser/audits/tool-reference.spec.mjs` compiles genuine upstream and Tau ToolCallBlock but upstream does not expand on click in the isolated bundle (aria-expanded remains false, no page error). Removing clock interception and unifying Preact aliases did not resolve it. Kept outside standard spec discovery until this harness defect is understood. Tau live-page tool interaction tests remain passing; do not claim paired tool geometry or screenshots. Next inspect bundler module/runtime identity and synthetic-origin event dispatch before changing product code.

## Paired tool fixture recovered

Isolated the exact ToolCallBlock source region from installed MessageItem (unchanged function/body) and imported upstream CopyButton directly, avoiding unrelated module initialization. This restored reference state transitions; the precise global-hook interaction remains undiagnosed, so no production bug is inferred. Removed obsolete audits prototype; standard `tool-reference.spec.mjs` now compares collapsed, tail and full-result geometry/text/fonts/padding. All six projects pass, paired screenshots/JSON attached. Fixture source-boundary assertions fail if upstream structure changes. It covers successful string output, not failure states or clipboard fallback parity.

## Core rich agent Markdown

Tau previously rendered agent content as plain text. Added logical MarkdownContent with pinned Marked 18.0.0 and DOMPurify 3.4.14 bundled offline; agent headings/lists/emphasis/code now produce semantic markup in the Piclaw content container. User text remains literal. HTML is sanitized (active attributes/URLs removed; form/style/iframe controls forbidden). Added dependency notices. Six-target Markdown security/rendering and timeline tests pass 12/12; build/TypeScript pass. This implements core Markdown, not Piclaw's full preprocessing/math/highlighting/diagram pipeline; paired rich-agent comparison remains required.

## Rich Markdown direct comparison

Actual upstream pipeline versus Tau now matches HTML and measured styles/geometry for headings, emphasis, inline/fenced code, lists, quote and link fixture in six targets. Added missing code-block header, language label and copy button structure after sanitization; clipboard handler decodes full UTF-8 code. Detached template transformations occur only before Preact mounts sanitized output. Test rounds geometry to 0.001px to avoid WebKit floating-point noise and includes viewport meta. Combined rich reference/security tests 12/12, build/TypeScript pass. Optional syntax highlighting, math and diagrams remain absent; language alias coverage currently limited.

## Corrected mobile fixture viewport

Earlier isolated fixtures omitted viewport meta, permitting a 980px mobile layout viewport. Added viewport meta to message/tool/container/control/token fixtures; message/tool fixtures explicitly assert document clientWidth equals project viewport width. Re-ran paired message/tools 12/12 and container/control/token checks 30/30 at true target widths. Reattached corrected screenshot archives; these supersede earlier mobile reference captures. Full page application tests already used index.html's correct viewport meta.

## Reference dependency reproducibility and fixture guard

Moved signals 2.11.2 into browser package.json/bun.lock; reference tests no longer require temporary dependency installation. Message/tool/rich Markdown references pass 18/18. Full suite reached 178/180: tool-output injection was replaced by empty live-page state in two WebKit targets. Added attached composer and explicit 'Tau shell ready.' guards plus onboarding dismissal before injection; focused six-target tool suite repeated three times passes 18/18. Full rerun still required.

## Browser routing isolation and current result

Exact status-message readiness was invalid because later stream announcements replace it. Added durable data-tau-shell-ready marker after initial refresh and used it for tool/plan fixtures. Subsequent real data bypassing route mocks exposed service-worker interference; browser harness now blocks service workers so page-route fixtures remain interceptable. Full suite **180/180 passed** after this change. Service-worker behavior is excluded from that result and requires separate validation. Core app marker changes no API contract.

## Service-worker coverage

Found missing offline Preact bundle/font cache entries; added preact-shell.js and all four fonts and bumped cache to v11. Worker-enabled tests now explicitly override the default blocked-worker suite: cache contents/API exclusion pass on all six projects; true offline rendered reload passes on all three Chromium viewports. WebKit offline navigation fails with internal browser error, so its three offline-reload cases are explicitly skipped/unverified (cache cases remain enabled). Result 9 passed/3 skipped, frontend/packaging 43/43. This is not full WebKit offline sign-off.

## Rich-copy and Python checkpoint

Verified Markdown code-copy preserves full UTF-8 content (café, Japanese and emoji) through generated base64 data and clipboard handler; six-target security/render/copy checks pass. Full Python suite rerun: 1327 passed. Build, TypeScript and diff checks pass. Current batch remains a partial visual-port checkpoint; no complete paired-shell or optional-plugin sign-off.

## Populated full Tau captures

Added populated-layout.spec.mjs: fixed user/agent Markdown/tool result fixture, expanded tool, chat and settings captures in both themes for all six engine/viewports (24 PNGs). 12 capture tests pass; archive and desktop preview attached. These are explicitly the Tau side only, not a paired full-App approval. Runtime/status metadata still comes from test server, so additional stubbing is required for pixel-deterministic whole-shell comparisons.

## Actual full Piclaw bundle reference

Loaded unmodified installed app.bundle.js/CSS directly under an isolated routed origin. Correct oobe response enables actual ChatPanel/MessageList; fixed user post/time and valid static system metrics supplied. All six engine/viewports render without page errors and produce screenshots/request inventories, attached. This removes the assumption that full-reference capture needs user-supplied images. Remaining work: fill all requested endpoint contracts (unknown routes still return empty objects), match complete Tau fixture, avatar handling and deferred vendor libraries, then compare full geometry/screenshots. Not yet approved parity.

## Full-shell geometry finding

Full reference now explicitly maps all observed initial endpoints and fails on unexpected requests instead of silently returning {}. Six targets pass. Desktop shell measurements found Tau's activity/tab top at 19.5px vs Piclaw 0: unstyled skip link occupied a row. Fixed it as a fixed-position keyboard-revealed accessibility link, restoring top=0; populated capture assertions now guard this. Both-theme populated/accessibility checks pass 24/24. Reference default sidebar is open at 250px versus Tau collapsed; composer height differs (106.5 vs 116px in initial measurement); align fixture state and investigate rather than masking differences.

## Composer measurement

Measured actual Piclaw and Tau composer children. Textarea is identical at 83.5px; Tau container had extra 9.5px. Empty attachment region padding accounted for 4px; now hidden when empty while anchor stays mounted. Composer reduced 116→112px; reference is 106.5px. Remaining 5.5px baseline/child-layout discrepancy not yet fixed. Moving completion popup before textarea did not change it and was reverted. Composer/keyboard 12/12 and build/TypeScript pass. Toolbar content differs intentionally by current Tau controls; full parity not asserted.

## Composer gap resolved

Child-removal experiment ruled out hidden controls as remaining 5.5px source; focus did not change it. Narrow block-flow rule on Tau textarea removes inline baseline gap without fixing height. Desktop composer now measures 106.5px, equal to actual Piclaw reference, with identical 83.5px textarea. Temporary diagnostic mutations removed. Populated captures/composer/keyboard matrix passes 24/24. This rule is a documented layout adaptation; toolbar contents/width still differ.

## Aligned collapsed-sidebar shell geometry

Reference fixture now sets genuine piclaw-sidebar-collapsed preference to match Tau resting state. Tau open sidebar width changed 300→250px (upstream default). Full-reference/populated/responsive tests pass 24/24. Measured activity/tab/composer/status geometry agrees exactly on tablet/desktop across engines; phone composer y differs +0.5px (same width/height), other measured boxes match. JSON attached. This is shell-box agreement only: visible toolbar/session controls and message content are not yet equivalent, so no pixel-parity claim.

## Shared full-shell message data

Introduced fixtures/visual-state.mjs supplying identical user text, agent Markdown and read-tool result to both capture adapters. Actual Piclaw app now gets pinned Marked module via its expected global and real bundled fallback avatar image (avoids repeated failing image fallback). All six actual-app captures pass; Tau both-theme captures pass 12/12. Shared-content archive attached. Found deliberate remaining differences: Piclaw sorts/visually reverses messages vs Tau chronology, Piclaw avatar vs Tau glyph, action bar and runtime/status contents. These are not normalized away; inspect and decide component mapping next. Full screenshots are not yet pixel equivalent.

## Timeline flex ownership correction

Earlier 'message ordering' difference was incomplete diagnosis: Piclaw reverses DOM children inside column-reverse, preserving chronological visual order. Tau's extra list wrapper prevented its messages being direct flex children, losing 10px gaps and bottom anchoring. Moved message-list class onto timeline-list, reversed the rendered child array to match upstream, retained the focus container as chat__messages and moved duplicated metadata to sr-only. New six-target test verifies direct items, column-reverse, 10px gap and chronological top-to-bottom placement; Markdown security tests use role classes rather than DOM first/last. Combined 12/12 pass; existing timeline/accessibility 18/18 passed in preceding run; TypeScript/build pass. DOM reading order now follows upstream reverse pattern; screen-reader implications remain for review.

## Empty branch section cleanup

Tau's persistent empty 'Session branch / No persisted branches yet' section consumed timeline space with no actionable content. It is now hidden when branch list is empty, while branch-list anchor stays mounted. Real branch buttons use existing standard button primitive and still emit tau:branch-select. Six branch behavior plus twelve both-theme accessibility checks pass 18/18; build/TypeScript pass. Nonempty branch placement remains a Tau-specific interaction rather than an upstream parity claim.

## Combined checkpoint results

Combined browser suite now 219 passed / 3 explicitly skipped (WebKit offline navigation), no failures. Python full run 1326 passed / 1 stale 300px sidebar source assertion; updated to verified 250px mapping and focused frontend/packaging rerun 43/43 passes. TypeScript/diff checks pass. Full Python rerun after that assertion-only correction not yet performed; do not conflate prior full pass with current result.

## Current installed checkpoint verified

At ac6c1fa full Python suite rerun passes 1327/1327. Rebuilt its wheel and reinstalled tau-prime into separate audit venv; browser launcher removes PYTHONPATH. Installed Markdown/security/copy, tool output, both-theme axe/focus, onboarding and settings matrix passes 36/36 across all targets. Source/browser complete run remains 219 passed/3 documented WebKit offline skips. These establish current functional/package checks, not complete visual acceptance.

## Message copy action

Added logical MessageActionBar using verified upstream message-action-bar/button classes, with Copy message action for original source text and accessible success/failure feedback. Clipboard-denied branch tested; no unsupported delete control introduced. Initial guessed class names changed height and failed paired geometry, corrected to exact upstream classes. Copy keyboard/Unicode/failure and paired message geometry tests now pass 12/12. Remaining upstream collapse/delete/read-aloud actions are not ported; action-bar contents differ intentionally until Tau behavior mapping is established.

## Local message collapse

Added collapse/expand action and upstream collapsed body/name/time/120-character preview hierarchy. Collapse is local component state, not persisted and not a backend mutation. Keyboard collapse and expansion restore rich content; copy/failure and expanded paired geometry remain passing across six targets (12/12 checks). Build/TypeScript pass. Delete/read-aloud and collapsed-state direct reference comparison still pending.

## Collapse keyboard focus regression

Strengthened action test to require focus remain on the new Expand/Collapse button without manually refocusing it. Reproduced focus loss when the message subtree changes, fixed using a shared toggle ref and layout-effect restoration only when that control had focus. Six-target copy/collapse/expand/failure tests pass 6/6; build/TypeScript pass. Collapsed direct-reference geometry remains to implement; do not count it as verified by this interaction test.

## Collapsed reference verified

Actual Piclaw collapsed MessageItem compared to Tau after a real collapse click: preview text, message/preview geometry and whitespace match across six targets. Each renderer gets a separate document/runtime to prevent upstream signal hooks interfering with Tau state scheduling; no rendering code mocked. Paired screenshots/JSON attached. Test covers one user-text preview, not all long/tool-only/live states or identical action inventories.

## Message deletion capability audit

Tau web registers DELETE for session archival and media only, not individual messages. Do not map Piclaw's delete-post control onto either operation. Message deletion is intentionally absent pending explicit backend design; preservation of existing API semantics takes priority over a misleading button. Copy/collapse are implemented, read-aloud remains optional/unported. Combined current action/collapsed-reference/both-theme accessibility checks pass 24/24.

## Explicit full reference themes

Actual unmodified Piclaw bundle capture now explicitly emulates light/dark and asserts matching root class. Both Piclaw and Tau shared-content captures run at all six viewports/engines (24 capture tests pass). Attached 24 full-chat images named by engine/viewport/theme, Tau prefixed. These supersede light-only reference captures. Runtime identity/status and feature inventories still differ; screenshots are review evidence, not approved baselines.

## Composer control overlap fixed

Added text-line/toolbar intersection check; previous floating delivery selector and long context label invaded first half of typed line on phone/tablet (four failures). Moved Tau delivery/context controls into existing upstream chat__compose-toolbar wrapping row below textarea; floating toolbar now contains only attachment icon. Six-target space/composer/keyboard checks pass 18/18. This deliberately adds a control row: earlier 106.5px resting height equality is superseded, not maintained by clipping or hiding Tau functionality. Full screenshot review must reflect this functional adaptation.

## Composer row stress validation

Expanded text-space check to light/dark schemes with long provider/context/attachment metadata. Twelve engine/viewport/theme cases show no row horizontal overflow and send remains visible. Both-theme accessibility/populated captures also pass 24/24. These verify the deliberate extra control row is usable; no claim that its height equals Piclaw's icon-only composer.

## Shared telemetry fixture

Moved fixed CPU/RAM/RSS/swap values into shared visual-state fixture with Tau/Piclaw API shapes. Tau populated capture now routes meters to fixed data and asserts exact rendered summary before screenshot; reference consumes same values. Both-theme six-target captures pass 24/24. Session/model/connection labels and avatar identity remain differing; do not infer whole-image determinism solely from this telemetry fix.

## Current combined regression checkpoint

Latest full browser run after action/composer/shared telemetry updates: 249 passed / 3 documented WebKit offline skips, no failures. Build/TypeScript and focused frontend/packaging 43/43 pass; diff check clean. Visual differences and optional features remain open; do not infer acceptance from this test count.

## Model/session fixture work in progress

Reference models response now uses explicit test/review-model from shared fixture. Attempted Tau session-response normalization did not select a session (empty-server state); reverted that incomplete interception rather than weakening the expected label. Desktop both-app/theme captures pass 4/4; Tau session/model determinism still requires a fully seeded selected session/context fixture. No production behavior changed.

## Selected-session fixture and model listener race

Added complete selected visual-review session/detail/branches/messages/context/plan/approvals GET fixture; status session/model labels now asserted. Prior normalization failure traced to request.method function being compared instead of invoked; fixed fixture method(). Fast fixture exposed status model event missed by deferred useEffect in WebKit; changed listener registration to useLayoutEffect. Both-theme populated matrix passes 12/12 after fix; build/TypeScript pass. Messages still injected separately for component capture; connection/avatar semantics remain differing.

## Collapse edge states

Verified tool-only message collapse/expand restores tool blocks, and long text previews truncate at 120 characters while expansion preserves full source. Removed meaningless Copy message action for empty content, matching upstream conditional action behavior. Edge-state and existing copy/focus tests pass 12/12 across six targets; build/TypeScript pass.

## Connection indicator state

Status dot was permanently disconnected while app.js updated only text. Moved connection message/state rendering into StatusBar via tau:connection-state; dot now uses upstream connected/disconnected classes from same state as label. Reconnecting is correctly classified as connecting. Six-target state tests plus both-theme accessibility pass 18/18; frontend Python 36/36 and build/TypeScript pass. Tests inject adapter states; a full real-SSE transition check is still distinct.

## Real SSE connectivity regression

Added real-backend session/SSE test (no stream route mocking), network offline then online recovery. Initial test reproduced Live state persisting through offline in all engines. Added browser offline handler to abort stream and show Offline; online restarts selected-session stream. Six-target real Live→Offline→Live indicator tests pass; frontend/packaging 43/43. Test sessions are isolated harness data. This verifies browser network events, not every server failure mode.

## Connection/fixture integrated checkpoint

Combined current browser suite: 267 passed / 3 documented WebKit offline-navigation skips, including real SSE connectivity. Full Python: 1327 passed. Build/TypeScript/diff checks pass. This checkpoint includes explicit selected-session capture fixture, initial status-model subscription timing fix, conditional empty copy action, connection label/dot state and offline/online recovery. Visual acceptance and optional feature gaps remain open.

## Phone settings clipping

Stronger per-control bounds check found auth/provider/model inputs and thinking Apply button outside phone settings pane even though document/panel scroll overflow was zero. Tau fields combine fixed-width controls in nonwrapping rows. Added scoped wrapping/maximum-width constraints for Tau settings fields, preserving standard control styles. Six settings bounds and six model-control checks pass 12/12. This is a documented responsive adaptation; screenshots still require acceptance.

## Settings category active state

Replaced hard-coded Authentication active styling with local selected-category state and aria-current. Normal keyboard/click navigation updates selected category; modifier clicks retain native link behavior and do not change current selection. Forms remain mounted. Settings layout/category keyboard and model-control tests pass 12/12; build/TypeScript pass. Scroll-position-driven active tracking is not implemented.

## Open-settings accessibility coverage

Added explicit light/dark axe scans of open settings pane across all targets (previous scans covered chat/mobile navigation, not settings). Found helper-text opacity failures and dark inactive-link/button secondary colors below 4.5:1. Scoped description opacity/active-theme muted color and dark link/button foreground corrections documented as accessibility exceptions; vendor CSS unchanged. Settings axe plus layout checks pass 18/18. These checks do not replace visual acceptance.

## Onboarding accessibility coverage

Added both-theme scoped axe/control-bounds checks to inline onboarding. Light passed; dark subtitle/labels/Cancel used legacy gray with 3.57:1 contrast. Scoped active-theme muted token corrections restore contrast without modifying vendor CSS. Onboarding axe/bounds plus open/cancel/reopen checks pass 18/18 across targets; no clipping observed.

## Pane-accessibility checkpoint

Combined current browser run after settings wrapping/category and onboarding contrast changes: 291 passed / 3 documented WebKit offline skips. Build/TypeScript, frontend/packaging 43/43 and diff checks pass. Full Python last 1327 passed at prior connection checkpoint; this batch changes frontend/styles/tests only. Visual approval and optional feature gaps still remain.

## Tool clipboard failure/retry

Tool copy no longer silently returns to idle after denial: accessible label/title reports 'Copy failed — retry', and a subsequent successful click restores copied feedback. Pending success timer is cleared when starting another attempt. Failure/retry/full-output and direct tool geometry tests pass 12/12; build/TypeScript/diff checks pass. This does not add a deprecated execCommand fallback.

## Markdown clipboard feedback

Added separate screen-reader status for code-copy success/failure/retry; previously errors were swallowed. Visible rich-content region remains unchanged and directly compared to actual upstream pipeline; additional sr-only status is asserted separately as deliberate accessibility difference. Unicode/security/retry and reference checks pass 12/12, build/TypeScript pass.

## Workspace/Plan accessibility

Added both-theme scans and per-control bounds checks for opened Workspace and Plan. Found light workspace heading contrast, dark/native file-tree button colors, preview metadata and plan revision/status contrast issues. Scoped button reset preserves standard file-tree geometry while avoiding native fill; labels use active theme text/muted tokens. Panel scans plus existing populated-workspace/plan-conflict tests pass 24/24. Axe workspace scan uses server's populated tree; plan scan starts with default plan state, while separate conflict test exercises injected revision.

## Enabled Plan scan correction

Combined run exposed dark Plan label/reload failures that isolated empty-session state missed. Panel axe fixture now explicitly injects dirty enabled plan and asserts both Save/Reload enabled before scanning. Scoped dark card-label and card-action foreground corrections resolve contrast; 12/12 both-theme panel cases pass. Earlier combined run was 297 pass/6 fail/3 skips; not yet superseded by a complete rerun.

## Latest pane/clipboard integration

After enabled Plan contrast corrections, combined browser run passes 303 tests with 3 documented WebKit offline skips and no failures. Frontend/packaging 43/43, build/TypeScript/diff checks pass. Checkpoint includes clipboard retry feedback, queue/run fixture completeness and Workspace/Plan accessibility fixes. Remaining full-image/feature gaps are tracked separately; no visual approval implied.

## Latest installed package and remote sync

Rebuilt wheel at 4a90859 and reinstalled into separate audit environment. Installed-pane accessibility (both themes), tool/Markdown clipboard and real SSE connectivity matrix passes 54/54, with no checkout PYTHONPATH. Pushed pending commits f9f193e/a829bc8/4a90859 to tau-prime branch. This is verified partial delivery; optional rendering/features and final paired visual acceptance remain unresolved.

## Populated Search audit

Added populated search result both-theme axe/control-bounds checks. Found light result-type and dark metadata contrast plus native action buttons. Mapped Tau submit/open-session buttons to existing standard button primitive and scoped result metadata to active theme tokens. Twelve search accessibility/bounds cases pass, build/TypeScript pass. Full app snapshot comparison still distinct.

## Search checkpoint

Search result behavior, both-theme populated Search axe/bounds and settings layout pass 24/24 together. Frontend/packaging 43/43 and diff checks pass. This checkpoint does not extend the last full-suite result; final visual gaps remain documented in the separate gap inventory.

## Dashboard modal focus

Reproduced Dashboard leaving keyboard focus on its background trigger. Added component-owned initial Close focus, Tab/Shift-Tab wrapping, Escape dismissal and connected-trigger restoration. Stable close callback ref avoids effect reset on renders. Six-target focus + dashboard content tests pass 12/12; build/TypeScript pass. Background inertness and a full dashboard axe scan remain separate follow-up checks.

## Populated Dashboard audit

Dashboard axe/bounds test now uses a fixed routed API response (not injected state raced by polling). Found light All sessions action contrast, dark description contrast, and phone footer overflow. Scoped contrast exceptions and wrapping header/footer/page-controls fix them. Populated both-theme axe/bounds plus keyboard modal tests pass 18/18. Background inertness still not independently verified.

## Dashboard background inertness

Dashboard now marks sibling regions along its ancestor path inert while open, preserving and restoring prior inert flags. It does not inert the ancestor containing the overlay. Test attempts programmatic composer focus while open (blocked), then verifies focus and interactivity restore on close. Modal focus + both-theme populated axe/bounds checks pass 18/18; build/TypeScript pass. Nested modal behavior still requires care if future overlays can open concurrently.

## Dashboard modified links

Dashboard link handler now intercepts only unmodified primary activation; Shift/Alt/middle behavior is preserved alongside Ctrl/Cmd. Synthetic-event test observes default prevention before suppressing navigation in the harness and confirms only ordinary click dispatches selection. Link/focus matrix passes 12/12; build/TypeScript pass. Test verifies handler semantics, not OS popup/download UX.

## Dashboard integrated checkpoint

Full combined run initially hit model-options injection replaced by server data. Added durable shell-ready/SSE isolation to that component spec; full rerun 339 passed / 3 documented WebKit offline skips. Frontend/packaging 43/43, TypeScript/diff checks pass. Dashboard focus/inertness/modified-links/contrast/wrapping fixes are checkpointed without claiming final visual acceptance.

## Dashboard session-selection dismissal

Real backend session-selection test reproduced Dashboard staying open after selecting a tile. selectSession now closes it after unsaved-plan confirmation, before session refresh/focus; modal inert cleanup uses layout effect. Six-target selection checks confirm modal hidden, target selected, timeline focused and not inert. Initial test route glob also matched synthetic session ID paths; narrowed it to /dashboard? so session API remains real. Existing focus tests passed 6/6 during fix. Build/TypeScript pass.

## Unsaved-plan cancellation and startup selection

New decline-switch test first exposed startup losing URL-selected session: applySessionFilter ran against an empty list before initial refresh. Removed that premature selection synchronization (persist filter only, let refreshShell resolve requested ID against fetched sessions). Real backend acceptance/cancellation matrix passes 12/12: decline preserves current session, dirty plan and open modal. Real SSE/populated capture checks pass 18/18; frontend/packaging 43/43. This corrects earlier startup sequencing attempts rather than adding another wait.

## Session-selection integration checkpoint

Complete browser suite after initialization/selection dismissal corrections: 351 passed / 3 documented WebKit offline skips, no failures. Full Python suite 1327 passed; diff checks pass. This checkpoint verifies functional regression coverage, not the still-open optional rendering/full visual acceptance items.

## Current installed Dashboard/session checkpoint

Built wheel at 677d974, reinstalled in separate audit venv, ran installed Dashboard accept/decline/focus/inertness/accessibility, populated Search both themes, and real SSE network recovery: 48/48 pass. No source PYTHONPATH injection. This closes installed validation lag for these fixes; whole-image approval and optional rendering gaps remain.

## Remaining audit and fixes

1. Font notices: added upstream JetBrains Mono OFL, Fira Code OFL and Nerd Fonts combined licensing in `static/FONT-LICENSES.md`; Fira Code embedded copyright/license records inspected. Wheel-byte test includes this notice (7/7 packaging tests pass). Codicons attribution and upstream CC BY 4.0 notice are also now included; recheck the complete asset manifest before final delivery.
2. Build paired deterministic fixtures from genuine Piclaw components and Tau components, with identical visible data; do not use Tau captures as reference images.
3. Capture real browser screenshots and computed styles for shell, sidebar, tab bar, chat, composer, status, onboarding, settings, dashboard and workspace.
4. Port missing logical components and remove incompatible compatibility CSS based on those observations.
5. Verify wheel contents, binary font loading under CSP, all browser interactions, and full regression suite after structural changes.
6. Present paired visual evidence before claiming completion.

## Pinned reference asset provenance

Compared `piclaw-reference.css` byte-for-byte with the installed Piclaw
2.15.3 `runtime/web/static/visual/dist/app.bundle.css`, and all four referenced
fonts with their corresponding upstream dist files: identical. Added a portable
SHA-256 pin test in `tests/web/test_packaging.py`, separate from the existing
wheel/source-byte preservation check. This prevents accidental local vendor
edits from silently changing both sides of component comparisons. Focused
frontend/packaging suite: 44 passed; `git diff --check` clean. No runtime changes
or visual-acceptance claim in this checkpoint.

## Reference idle-status fixture correction

Upstream `components/model-context-bar/useStatusPolling.ts` reads
`statusData.addon_api` before requesting models. Returning JSON null from
`/agent/status` made that polling path throw internally. The reference now
returns `{status:"idle",data:null}` and asserts both mounted model badges show
`test/review-model` before screenshots. All 12 reference captures pass; Tau's
12 populated captures also pass. These refresh the paired evidence, not approval.
Connection probes/SSE lifetime and identity/avatar deviations remain to review.

## Persistent connected capture fixtures

Replaced finite SSE lifetime for the populated comparison with screenshot-only
persistent transports: fetch ReadableStream for Tau, EventSource open lifecycle
for Piclaw. No application/runtime changes. Both capture suites pass 24/24;
reference rerun with explicit absence-of-offline assertion passes 12/12.
Tau asserts Live + connected dot. Piclaw intentionally hides its connection
indicator when connected (App.tsx), whereas Tau retains the Live indicator;
this is now a documented UI difference rather than an accidental EOF race.
Real backend SSE recovery remains covered independently, not by this mock.

## Renderer capability inventory

Added runtime capability metadata to genuine-bundle captures (12/12 pass).
The fixture has Marked but no cmHighlight, KaTeX or Mermaid globals; the sample
has zero token spans. Inspected the pinned visual index script list and
code-highlighting fallback. No new renderer dependency added speculatively.
See remaining-gap inventory for the limits of this evidence.

## Labeled paired review delivery

`node tests/browser/build-visual-review.mjs` generates a self-contained HTML
review from existing capture directories, with 12 labeled pairs / 24 embedded
images and explicit limitations. Delivered `tau-piclaw-paired-review.html` for
human assessment. This is not a fresh capture or an approval. Generator output
structure verified (12 sections, 24 images); diff checks clean. Current inputs
are connected-state captures from the 30cdb61/8c3977c fixture checkpoints.

## Reproducible bdf435a artifact and full installed suite

Built twice with `SOURCE_DATE_EPOCH=$(git show -s --format=%ct bdf435a)` using
`build_backend.build_wheel`: byte-identical wheels.
SHA-256 `bfd1d8d662e666cd7fa96c5ab471a228d81c0300279ffef12384fb323ce8ae9a`
for `tau_prime-42.3.0-py3-none-any.whl`.
Installed into the separate audit venv and ran the entire browser suite with
`TAU_BROWSER_PORT=8877 TAU_BROWSER_BIN=/workspace/tmp/tau-installed-audit/bin/tau`.
Initial run: 350 passed, 3 skipped, 1 meters fixture race. That test still mocked
EventSource rather than Tau's fetch SSE; replaced the obsolete stub with the
persistent test stream and durable shell-ready wait. Full installed rerun:
351 passed, 3 documented WebKit offline skips. No application bytes changed.
Focused frontend/packaging tests: 44 passed. Visual approval is still pending.

## Populated Workspace comparison

Added a two-entry Workspace fixture (src directory, README.md file) to both
capture adapters, and asserted visible file content before screenshots.
Both-theme/six-target capture suites pass 24/24. Exporter accepts `workspace`
as its second argument to produce 12 populated panel pairs. Tau retains its
read-only preview/annotation controls; this is a comparison, not a claim that
its filesystem API or editor is equivalent to Piclaw's. No runtime changes.

## Populated Search comparison

Added shared query/message text to populated Search screenshots on both sides.
Reference uses the real search endpoint adapter and nested data.type for author
label; Tau uses its existing component event fixture and session-open control.
Tau captures pass 12/12; reference corrected-selector rerun passes 12/12.
Exporter now supports `search`, delivering twelve labeled pairs. Search author,
timestamp, filters and navigation differ; do not equate Tau's Open session with
Piclaw's scroll-to-message action. No production changes or acceptance claim.

## WebKit offline repro follow-up

Added opt-in TAU_PROBE_WEBKIT_OFFLINE=1 path. Desktop probe reproduces the
internal WebKit reload error, with cache verification passing. Strengthened
cache assertions to require root document and all successful/nonempty asset
responses; default six-target service-worker run: 9 passed, 3 existing skips.
No unsupported claim that this proves browser-engine fault or fixes offline
navigation. Production service worker unchanged; repro command in browser README.
