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

Piclaw's vendored `piclaw-reference.css` is the visual source of truth. Keep `piclaw-parity.css` limited to Tau-specific compatibility and accessibility bridges; do not hide structural differences with broad CSS overlays.

Component-owned regions include the activity bar, status bar, session dashboard, session navigation, central timeline, composer, workspace/search/plan/settings side panel, editor shell, queue stack, and overlays.
