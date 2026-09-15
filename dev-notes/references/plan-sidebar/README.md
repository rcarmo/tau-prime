# Deployed Plan sidebar reference

Source: installed `@rcarmo/piclaw-addon-plan-sidebar` 0.1.25, `web/index.ts`.
Package metadata declares MIT. Upstream: https://github.com/rcarmo/piclaw-addons
Snapshot: `index.ts.reference`, SHA-256 `db031d33487eb92ff7fa850b70e55242a3bb6dd83b5c8589c7cea5140bcdec3d`.

The CSS template was extracted unchanged into Vibes `static/css/plan-sidebar.css`.
It is now imported by the build; integration is in progress and visual parity remains unverified.
The installed package lacked a standalone license. The upstream MIT license was
retrieved from https://raw.githubusercontent.com/rcarmo/piclaw-addons/main/LICENSE
and preserved in `LICENSE` here and `static/PLAN-SIDEBAR-LICENSE.txt` in the frontend.
Copyright (c) 2026 Rui Carmo. Package inclusion still needs artifact verification.

Tau adaptation requirements:
- `session_id`, bearer/CSRF and `expected_revision`, not Piclaw chat_jid/overwrite.
- Preserve dirty drafts and reject stale response application after session switch.
- Close autosaves only if accepted; conflict keeps sidebar open and draft intact.
- Refresh/reset explicitly confirm discard; reset must remain revision-safe.
- Submit saves first, then uses normal session run/FIFO path; never clears composer.
- Wire tau.plan.updated to refresh clean state or flag dirty remote changes.
- Match deployed chrome, progress, 300–620 desktop resize and mobile sizing.
- Reuse CodeMirror with checklist decorations, fallback textarea only on load failure.
