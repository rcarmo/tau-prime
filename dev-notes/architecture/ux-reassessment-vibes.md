# Tau UX reassessment against Vibes

Reviewed rcarmo/vibes main at 4337868 (0.8.1), source checkout in
/workspace/tmp/vibes-ux-review. This is source/document inspection, not a new
browser evaluation. Landlock work is independently committed at 7f5abec.

## Findings

Vibes uses vendored Preact/HTM with explicit application components and Piclaw
2.15.3 classic CSS split into ordered layers. See `build.js`,
`docs/CLASSIC_CSS.md`, `src/vibes/static/js/app.js`, and `components/session-picker.js`.
Its compatibility CSS remains substantial: importing classic CSS does not itself
establish visual parity. Its comparison docs explicitly retain outstanding
acceptance and geometry/density differences. Their historical test counts are
not fresh Tau evidence.

Useful concrete patterns:
- Session picker owns filtering, selection, focus, keyboard navigation, concurrent
  action gating and errors (`components/session-picker.js`).
- Composer uses classic model-meta hierarchy and targeted mobile containment
  (`docs/MODEL_CONTROL_MARKUP_AUDIT.md`, `components/compose-box.js`).
- Separate component comparisons identify exact differences before further
  changes (`docs/SESSION_PICKER_VISUAL_COMPARISON.md`).
- Frontend assets build locally from pinned sources, not an installed reference.

Tau currently has split ownership: `frontend/src/index.tsx` renders components,
while `static/app.js` (2924 lines at review) drives DOM anchors and custom events.
Keeping forms mounted fixed symptoms, but did not eliminate the competing state
and lifecycle paths. Changing framework from TSX to HTM would not fix that.

## Recommended approach

Retain classic as the only visual target and keep the working Tau backend.
Do not restart the port, transplant Vibes wholesale, or add its terminal/editor/
queue features merely because they exist there. Do not make universal Piclaw
feature equivalence a release gate.

1. Inventory DOM/event ownership, then move one vertical slice at a time into
   typed state/actions shared by Tau components. Begin with model selection:
   catalogue loading, current selection, submission and error state should have
   one owner, rather than a settings shortcut standing in for a picker.
2. Build the actual classic-style picker using only metadata Tau exposes. Reuse
   Vibes interaction patterns where applicable; never fabricate pricing/context
   fit. Preserve drafts and existing provider/model/thinking API semantics.
3. Repeat for session selection and Settings. Retire each old DOM/event path only
   when its replacement passes contract, focus, streaming and draft tests.
4. Review one realistic workflow at a time: select session/model, send/stream,
   inspect tools/media, change settings and return without losing a draft.
   Use stable paired screenshots in both themes, browsers and required sizes;
   select representative images for review instead of repeatedly shipping PDFs
   after every small patch.
5. Maintain an explicit supported-surface table. Read-aloud and full media lightbox
   remain separate features, not prerequisites invented by asset parity. Any
   decision to omit them must be visible, not silently called equivalent.

## Next implementation boundary

Model-selection slice only: inventory current catalogue API, extract state/action
ownership, implement picker with keyboard/focus/loading/error behavior, test
selection persistence and composer draft survival, then capture classic pairs.
No production UX code changed in this reassessment. Existing UX acceptance remains
open; old artifacts are evidence, not approved baselines.
