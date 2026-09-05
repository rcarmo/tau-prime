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

## Remaining audit and fixes

1. Font notices: added upstream JetBrains Mono OFL, Fira Code OFL and Nerd Fonts combined licensing in `static/FONT-LICENSES.md`; Fira Code embedded copyright/license records inspected. Wheel-byte test includes this notice (7/7 packaging tests pass). Codicons attribution and upstream CC BY 4.0 notice are also now included; recheck the complete asset manifest before final delivery.
2. Build paired deterministic fixtures from genuine Piclaw components and Tau components, with identical visible data; do not use Tau captures as reference images.
3. Capture real browser screenshots and computed styles for shell, sidebar, tab bar, chat, composer, status, onboarding, settings, dashboard and workspace.
4. Port missing logical components and remove incompatible compatibility CSS based on those observations.
5. Verify wheel contents, binary font loading under CSP, all browser interactions, and full regression suite after structural changes.
6. Present paired visual evidence before claiming completion.
