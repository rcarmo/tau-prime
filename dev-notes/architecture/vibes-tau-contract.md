# Vibes → Tau integration boundary

Pinned Vibes source is recorded under src/tau_web/vibes/source-revision.txt.
The imported app is not wired to Tau yet. New tau-client.js is a unit-tested
transport foundation, not a claim that session UI integration is complete.

| Surface | Vibes assumption | Tau mapping / required work |
|---|---|---|
| Sessions | /sessions, id/name, synthetic default | /api/sessions, session_id/title; explicitly choose real initial session |
| Create | name/parent only | provider_name/model required; obtain real setup selection; branching is separate |
| Rename/delete | PATCH name / DELETE | PATCH title / explicit archive route; label Archive, never imply deletion |
| Models | /agent/models, session model-state | /api/models and session provider/model/thinking; inspect catalogue shape before projecting |
| Timeline | posts, before pagination | /api/sessions/{id}/timeline, after cursor; pagination cannot be renamed blindly |
| Send | /agent/{id}/message, media_ids/mode | Tau session messages/runs; translate attachments and queue/run semantics explicitly |
| SSE | global Vibes named events | /api/events canonical envelopes with session/run/sequence/payload; retain cursor/recovery and dedupe |
| Media | /media/upload plus direct URLs | use authenticated Tau asset routes; inspect IDs and upload format |
| Workspace/editor | writable file REST APIs | audit Tau workspace capabilities; no optimistic fake writes |
| Terminal | direct /terminal/session fetch and WebSocket | capability must be false until a real backend exists; bypasses api.js today |
| Preferences | ETag model pins | preserve real persistence/concurrency or explicitly disable unsupported preferences |
| Plan/approvals | not a drop-in Vibes equivalent | integrate Tau-specific APIs without losing conflicts or authorization |

Transport ownership: adapt api.js through a Tau client/projection layer, not a
global fetch monkeypatch. Direct terminal/media/WebSocket access must also be
accounted for. Unit tests check request/response projections; actual routes and
browser workflows remain separate gates. Preserve imported component ownership.

Checkpoint: four Tau client unit tests pass (eight assertions), lint passes.
Session list/create/rename transport scaffold is intentionally not connected to
the app until initial-session and catalogue decisions are implemented together.

Model adapter checkpoint: Tau `/api/models` is an observed-session catalogue,
not provider discovery. Projection retains the current model, deduplicates pairs
and omits unsupported pricing/context/reasoning capabilities. Model mutations
use the loaded session revision; 409 errors propagate without retries. Six
transport tests (14 assertions), lint and frontend build pass. Still not wired
to production; reasoning controls and initial selection need integration.

API wiring checkpoint: imported api.js now delegates session listing/rename and
model listing/state/change to Tau transport, reading the existing auth token.
Creation without provider setup and deletion explicitly fail instead of calling
wrong Vibes endpoints. These are interim integration errors, not finished UI:
creation controls need setup, deletion must become Archive, initial default and
timeline/SSE are still pending. Ten tests/31 assertions, lint and build pass.

Persisted timeline checkpoint: both imported timeline functions now use the Tau
adapter. Ascending backend pages are scanned into newest-first UI pages with
explicit older-message boundaries and monotonic cursor validation. Scan cap
fails visibly rather than truncating silently; a reverse-page backend endpoint
is preferable before large-history performance signoff. Current projection is
text/role/identity only: tool blocks/media and live SSE remain unimplemented.
Twelve tests/37 assertions, lint and build pass; not end-to-end acceptance.
