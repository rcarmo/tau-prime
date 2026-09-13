# Imported Vibes frontend

Source: https://github.com/rcarmo/vibes
Revision: 4337868 (full revision in source-revision.txt), main, release 0.8.1.
License: MIT, retained in LICENSE; bundled third-party notices remain in assets.

This is the coherent replacement frontend source, not yet the production UI.
The existing Tau backend, authentication and Landlock implementation are unchanged.

Local changes at import: relocate build paths from src/vibes/static to static;
exclude generated dist and rebuild locally with `bun install --frozen-lockfile`
then `bun run build:frontend`. Keep upstream component/state ownership; adapt the
API boundary rather than reproducing components in Tau's old frontend.

Production switch and old-frontend removal are gated on Tau adapter tests and
real backend workflows. Import alone does not establish functional compatibility.

Import checkpoint validation: Bun frozen install, production JS/CSS build and
ESLint passed. Root-relative asset/API paths still target the Vibes contract;
this tree must not be advertised as a working Tau UI yet. Packaging/route wiring
and adapter contract mapping are pending. Generated dist is ignored during
integration; final packaging must explicitly ship the reproducibly built assets.
