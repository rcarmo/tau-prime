# Browser test ownership inventory

Read-only inventory of in-scope browser tests and Playwright-bearing scripts.
Nearest IDs are best-fit references from `references/fixtures-vibes/features`; `new` marks uncovered behavior.

Scope:
- `tests/browser/specs/*.mjs`
- `src/tau_web/vibes/tests/*browser*.mjs`
- `src/tau_web/vibes/tests/*installed*.mjs`
- other non-`node_modules` `.mjs` files importing Playwright

Classification: `SHARED` = canonical/shared UX contract, `RUNTIME` = runtime or skin-specific plumbing/audit, `MIXED` = shared UX exercised through runtime-specific integration.

## Tests: `tests/browser/specs/*.mjs`

| Path | Class | Behaviors | Nearest UX IDs |
| --- | --- | --- | --- |
| tests/browser/specs/accessibility.spec.mjs | MIXED | Shell accessibility coverage, keyboard focus indicator, composer/send/session controls | @ux-shared-001, @ux-shared-013, new |
| tests/browser/specs/approval.spec.mjs | MIXED | Approval dialog uses Piclaw modal mapping; Escape safely denies | new |
| tests/browser/specs/branches.spec.mjs | RUNTIME | Branch section hides empty state and preserves selection behavior | new |
| tests/browser/specs/classic-accessibility.spec.mjs | RUNTIME | Classic chat/navigation accessibility and large-code control bounds in light/dark | @ux-shared-033, new |
| tests/browser/specs/classic-assets.spec.mjs | RUNTIME | Classic fonts and SVG controls load without rejected visual assets | new |
| tests/browser/specs/classic-frame.spec.mjs | RUNTIME | Tau event bridge feeds classic timeline/composer/nav callbacks without activity bar | new |
| tests/browser/specs/classic-live.spec.mjs | MIXED | Real Tau adapter session nav, composer resize, workspace edge toggle, model settings focus | @ux-shared-002, @ux-shared-013, @ux-shared-020, new |
| tests/browser/specs/classic-paired.spec.mjs | RUNTIME | Reference-style populated classic capture with message list, status and workspace tree | new |
| tests/browser/specs/classic-settings-dialog.spec.mjs | MIXED | Classic Settings stays modal and preserves form state across close/reopen | @ux-settings-001, @ux-settings-dialog-001 |
| tests/browser/specs/composer-space.spec.mjs | RUNTIME | Classic composer spacing/bounds; hides context readout and delivery selector | new |
| tests/browser/specs/composer.spec.mjs | MIXED | Staged attachments render as chips; send surface omits visible Run selector | @ux-shared-026, new |
| tests/browser/specs/connection-live.spec.mjs | MIXED | Real SSE reports Live and changes indicator after interruption | @ux-shared-023 |
| tests/browser/specs/connection-state.spec.mjs | MIXED | Connection label only disappears while actually live | @ux-shared-023 |
| tests/browser/specs/dashboard-accessibility.spec.mjs | RUNTIME | Dashboard modal accessibility and viewport containment | new |
| tests/browser/specs/dashboard-focus.spec.mjs | MIXED | Dashboard focus trap, Tab cycling and Escape restoration | new |
| tests/browser/specs/dashboard-links.spec.mjs | MIXED | Dashboard only intercepts ordinary primary-link activation | new |
| tests/browser/specs/dashboard-select.spec.mjs | MIXED | Dashboard session switching closes modal; declined switch preserves unsaved plan | @ux-shared-010, @ux-shared-013 |
| tests/browser/specs/dashboard.spec.mjs | RUNTIME | Tau dashboard sessions render as Piclaw-managed tiles | new |
| tests/browser/specs/full-reference.spec.mjs | RUNTIME | Genuine classic populated reference harness and surface smoke | new |
| tests/browser/specs/keyboard.spec.mjs | SHARED | Keyboard shortcuts, completion behavior and focus traversal | @ux-shared-003, @ux-shared-013, @ux-shared-021 |
| tests/browser/specs/layout-audit.spec.mjs | RUNTIME | Shell/workspace visual audit capture | new |
| tests/browser/specs/markdown.spec.mjs | SHARED | Semantic markdown, safe HTML handling, code collapse/copy and UTF-8 byte thresholds | @ux-shared-028, @ux-shared-033 |
| tests/browser/specs/message-collapse-edge.spec.mjs | SHARED | Tool-only and long-message collapse keeps preview and full content available | new |
| tests/browser/specs/message-copy.spec.mjs | SHARED | Copy preserves stored markdown and surfaces clipboard failure state | @ux-shared-024, @ux-shared-033 |
| tests/browser/specs/meters.spec.mjs | RUNTIME | System meter snapshots render through Tau-to-Piclaw stats markup | @ux-settings-020 |
| tests/browser/specs/model-controls.spec.mjs | MIXED | Model picker and thinking controls remain Preact-owned | @ux-shared-020, @ux-shared-022 |
| tests/browser/specs/onboarding-accessibility.spec.mjs | MIXED | Provider onboarding wizard has no serious accessibility violations | @ux-auth-006, @ux-auth-007 |
| tests/browser/specs/onboarding-layout.spec.mjs | MIXED | Provider setup stays centered and reopens from Settings | @ux-auth-006, @ux-settings-007 |
| tests/browser/specs/panels-accessibility.spec.mjs | MIXED | Workspace and Plan controls stay accessible and within viewport | @ux-shared-009, @ux-workspace-005 |
| tests/browser/specs/plan-refresh.spec.mjs | SHARED | Background same-revision Plan refresh preserves local draft | @ux-shared-010 |
| tests/browser/specs/plan.spec.mjs | MIXED | Plan panel exposes revision/conflict state through task markup | @ux-shared-009, @ux-shared-010, @ux-shared-011 |
| tests/browser/specs/populated-layout.spec.mjs | RUNTIME | Populated chat/settings capture with status, meters, workspace and search surfaces | new |
| tests/browser/specs/queue.spec.mjs | SHARED | Accessible FIFO queue stack with dispatch, return and steer affordances | @ux-shared-016, @ux-shared-017, @ux-shared-018, @ux-shared-019 |
| tests/browser/specs/responsive.spec.mjs | MIXED | Responsive shell, nav drawers and UTF-8 workspace file rendering | @ux-shared-001, @ux-shared-002, @ux-workspace-008 |
| tests/browser/specs/search-accessibility.spec.mjs | MIXED | Search pane accessibility and containment inside its pane | @ux-workspace-005, new |
| tests/browser/specs/search.spec.mjs | MIXED | Search results render through Piclaw search cards | @ux-workspace-005 |
| tests/browser/specs/service-worker.spec.mjs | RUNTIME | Service worker caches shell assets without API data and supports offline reload | new |
| tests/browser/specs/sessions.spec.mjs | MIXED | Session navigation renders Tau sessions through sidebar cards | @ux-shared-013, @ux-shared-014, @ux-shared-015 |
| tests/browser/specs/settings-accessibility.spec.mjs | MIXED | Settings dialog accessibility coverage | @ux-settings-001, @ux-settings-004 |
| tests/browser/specs/settings-layout.spec.mjs | RUNTIME | Classic Settings dialog keeps Tau API form anchors mounted | @ux-settings-002, @ux-settings-003 |
| tests/browser/specs/system-theme.spec.mjs | RUNTIME | Classic shell follows system theme without visual-mode tokens | @ux-settings-018 |
| tests/browser/specs/theme-parity.spec.mjs | RUNTIME | Tau compatibility sheet preserves Piclaw root theme tokens | @ux-settings-018, new |
| tests/browser/specs/timeline-layout.spec.mjs | MIXED | Classic timeline keeps chronological visual order and bounded layout | @ux-shared-033, new |
| tests/browser/specs/timeline.spec.mjs | MIXED | Timeline maps message, tool and attachment surfaces into Piclaw components | @ux-shared-024, @ux-shared-027, @ux-shared-033 |
| tests/browser/specs/tool-output.spec.mjs | SHARED | Tool output tail, expand/collapse and copy-full-output behavior | @ux-shared-027 |
| tests/browser/specs/workspace.spec.mjs | MIXED | Workspace tree and annotations render through Preact with Tau data | @ux-workspace-004, @ux-workspace-005, @ux-workspace-008 |

## Tests: `src/tau_web/vibes/tests`

| Path | Class | Behaviors | Nearest UX IDs |
| --- | --- | --- | --- |
| src/tau_web/vibes/tests/browser-smoke.mjs | MIXED | Broad end-to-end smoke: session picker, widgets/extensions, safe markdown/code copy, queue mutations, model picker, plan, search, onboarding, resize and workspace | @ux-shared-013, @ux-shared-016, @ux-shared-020, @ux-shared-024, @ux-shared-027, @ux-shared-029, @ux-shared-033, @ux-settings-020, @ux-workspace-004, @ux-workspace-005, new |
| src/tau_web/vibes/tests/context-pie-browser.mjs | RUNTIME | Isolated ContextPie compaction callback, status class and elapsed label | new |
| src/tau_web/vibes/tests/full-host-visual.mjs | RUNTIME | Piclaw-vs-Tau visual parity diffs for host shell, plan, queue, picker and workspace states | @ux-shared-001, @ux-shared-002, @ux-shared-009, @ux-shared-013, @ux-shared-016, @ux-shared-027, @ux-workspace-004, new |
| src/tau_web/vibes/tests/live-backend.mjs | MIXED | Real backend sessions, SSE snapshot, meters, model/thinking changes, branches, media, workspace, plan conflict, archive/restore, new-session and offline/login flows | @ux-shared-009, @ux-shared-013, @ux-shared-020, @ux-shared-023, @ux-shared-026, @ux-workspace-008, @ux-auth-006, new |
| src/tau_web/vibes/tests/meters-browser.mjs | RUNTIME | System meters polling, collapse persistence and unavailable-state summary | @ux-settings-020 |
| src/tau_web/vibes/tests/offline-browser.mjs | RUNTIME | Service-worker precache hygiene, offline draft persistence and waiting-worker upgrade | new |
| src/tau_web/vibes/tests/plan-demo.mjs | RUNTIME | Deployed authenticated demo: plan sidebar open/close, live RSS meter and desktop/phone HUD behavior | @ux-shared-009, @ux-settings-020 |
| src/tau_web/vibes/tests/plan-editor-browser.mjs | MIXED | Plan editor decorations, session switch refresh and read-only behavior | @ux-shared-009, @ux-shared-010 |
| src/tau_web/vibes/tests/plan-installed.mjs | MIXED | Installed backend Plan save/conflict handling plus queue round-trip and meters endpoint | @ux-shared-010, @ux-shared-016, @ux-shared-017 |
| src/tau_web/vibes/tests/plan-reference-browser.mjs | RUNTIME | Plan/sidebar geometry compared to pinned reference across widths/themes | @ux-shared-009, new |
| src/tau_web/vibes/tests/plan-sidebar-browser.mjs | MIXED | Save-before-send, conflict blocking, session isolation, mobile bounds and SSE reconnect in Plan sidebar | @ux-shared-009, @ux-shared-010, @ux-shared-011 |
| src/tau_web/vibes/tests/provider-live.mjs | MIXED | Live local-provider approval, run completion and recovery path | new |
| src/tau_web/vibes/tests/quick-actions-browser.mjs | SHARED | Quick Actions typeahead open/filter/dismiss, skill prefill, excluded targets and wrap selection | @ux-shared-003, @ux-shared-004, @ux-shared-006, @ux-shared-008 |
| src/tau_web/vibes/tests/read-aloud-browser.mjs | SHARED | Read-aloud ownership transfer and stop/cancel behavior across posts | @ux-shared-029 |
| src/tau_web/vibes/tests/reference-layout.mjs | RUNTIME | Current layout/style compared against pinned browser reference geometry and styles | new |
| src/tau_web/vibes/tests/safe-svg-browser.mjs | SHARED | Sanitized SVG render blocks script/event/network execution | @ux-shared-028, @ux-shared-031 |
| src/tau_web/vibes/tests/steer-installed.mjs | MIXED | Installed steer flow consumes queued item into active run and retains history | @ux-shared-019 |
| src/tau_web/vibes/tests/stream-browser.mjs | SHARED | Authenticated browser SSE with split UTF-8 frame, reconnect cursor and replay dedupe | @ux-shared-023 |
| src/tau_web/vibes/tests/tool-status-browser.mjs | SHARED | Running-tool status label and elapsed timer freeze after completion | @ux-shared-027 |
| src/tau_web/vibes/tests/worker-upgrade.mjs | RUNTIME | Worker upgrade preserves unrelated caches and removes old app registrations | new |

## Runners and helpers

| Path | Kind | Behaviors | Notes |
| --- | --- | --- | --- |
| src/tau_web/vibes/tests/browser-matrix.mjs | runner | Sequential matrix runner for browser-smoke across engines, sizes and themes | Covers browser-smoke only |
| tests/browser/playwright.config.mjs | config | Playwright project matrix, service-worker blocking and web-server harness config | Harness only |
| tests/browser/start-server.mjs | helper | Isolated Tau web fixture server with temporary workspace/database seeding | Harness only |
| tests/browser/audits/capture-classic-reference.mjs | audit helper | Captures baseline classic DOM inventory and screenshot for reference inspection | Manual/reference capture |

## Counts

- Test files inventoried: **66**
- `SHARED`: **12**
- `RUNTIME`: **24**
- `MIXED`: **30**
- Runners/helpers: **4**
- Total in-scope files listed: **70**
