# Remaining Piclaw/Tau visual audit gaps

This is the bounded follow-up list after the source/CSS/component corrections. Functional pass counts do not close these gaps.

## Confirmed intentional or backend-constrained differences

- Tau branding and fallback avatar glyph differ from Piclaw identity/avatar. Do not copy Piclaw identity merely to lower screenshot difference.
- Tau delivery mode/context controls use the existing wrapping compose-toolbar row. Extra height is intentional to avoid overlap while retaining run/follow-up/steer semantics.
- Message deletion is unavailable in Tau's existing API. Do not show a misleading delete control or map it to session archival.
- Contrast exceptions for chat/status/settings/onboarding are documented in piclaw-parity.css and the audit log. Exact vendor CSS remains unchanged.

## Open implementation/review items

1. Full-app captures: explicitly resolve session identity and connection state on both sides; current same-message fixture still differs in these status surfaces.
2. Message actions: copy/collapse are implemented; read-aloud remains unported. Decide whether this browser-only capability belongs in Tau scope before treating action inventories as equivalent.
3. Rich rendering: core Markdown/code wrappers match tested reference input; syntax highlighting, math, diagrams and broader upstream preprocessing are not ported. Existing tests must not imply coverage of these.
4. Sidebar content: sessions/workspace/search/plan/settings use Tau data and controls. Populated Search/Workspace, enabled Plan, Settings and Onboarding now have both-theme accessibility and bounds coverage, with confirmed contrast/clipping fixes. Their complete appearance still needs paired visual assessment; these tests are not visual approval.
5. Capture determinism: avatars, asynchronous connection announcements and remaining fallback API requests must be explicit before pixel-regression approval.
6. WebKit offline reload: cache validation passes, but offline navigation is skipped after internal browser errors. Browser offline delivery is not fully signed off.
7. Final visual acceptance: compare complete paired images and record accepted semantic/branding/accessibility deviations; no whole-image similarity score can substitute for this.

## Verified interaction checkpoint (a283f98)

- Real backend SSE Live → Offline → Live recovery passes all six browser/viewport targets.
- Dashboard focus, background inertness, native modified links, accepted selection and declined unsaved-plan selection are verified.
- Initial URL-selected session is preserved until the session list loads.
- Message copy/collapse, keyboard focus restoration, long/tool-only previews and clipboard failure/retry are verified.
- Full combined browser suite: 351 passed, 3 WebKit offline-navigation skips. Full Python suite: 1327 passed.
- These interaction findings can be closed for this checkpoint without closing any of the visual acceptance items above.

## Fixture correction from this review

The synthetic selected session lacked runs/queue responses. Added empty runs/queue fixtures and a no-queue-error assertion, avoiding unrelated backend errors in the visual sample. Populated capture matrix passes 12/12 after correction.

## Rich-rendering scope evidence (30cdb61 follow-up)

The pinned visual index loads Marked and the app bundle; it has a CodeMirror
import map but does not initialize `window.cmHighlight`. The highlighting
utility reads that optional global and otherwise escapes plain code. Reference
capture metadata now records renderer capabilities: across all 12 targets,
Marked is present, cmHighlight/KaTeX/Mermaid are absent and code token spans are
zero. This describes the isolated pinned bundle fixture, not every Piclaw runtime
or lazy-loaded feature. Therefore existing core-Markdown comparisons must not be
advertised as syntax-highlighting/math/diagram parity. Adding those capabilities
to Tau remains an explicit scope decision, not justified by this plain-code sample.
