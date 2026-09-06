# Tau Web Preact frontend

Tau Web's browser shell is authored in TypeScript and Preact. The generated bundle is committed so installed wheels and source distributions can serve it without Node.js, Bun, or network access.

## Build and check

From the repository root:

```sh
cd src/tau_web/frontend
bun install --frozen-lockfile
bun run check
bun run build
```

`bun run check` runs TypeScript without emitting files. `bun run build` writes `src/tau_web/static/preact-shell.js`.

Do not hand-edit the generated bundle. Commit source and bundle changes together, and confirm packaging coverage with:

```sh
PYTHONPATH=.:src pytest -q tests/web/test_frontend.py tests/web/test_routes_assets.py tests/web/test_packaging.py
```

## Migration contract

The Preact shell owns the visible application markup. Components preserve IDs, extension slots, accessibility attributes, and event attachment points consumed by the headless `app.js` adapter, `extension-ui.js`, and `frontend-sdk.js`. Imperative DOM is restricted to extension/widget hosts.

Piclaw **classic** is the only UX. The pinned `piclaw-classic.css` is copied unchanged from its classic bundle; `tau-classic.css` contains scoped Tau semantic/accessibility adaptations. There is no visual-mode shell, stylesheet, or mode switch. Do not reintroduce an activity bar or alternative UX.

Component-owned regions include the classic chat frame, composer session/status controls, message and code blocks, session dashboard/navigation, workspace/search/plan/settings secondary panels, queue stack, and overlays. Some secondary-panel internals still require classic markup/style review; passing functional tests is not visual acceptance.

See `dev-notes/architecture/piclaw-classic-port.md` for source provenance, current tests, known adaptations and remaining review. Genuine reference captures use the shipped classic index/bundle, not the rejected visual frontend.
