# Browser test harness (Playwright)

This directory contains an isolated Playwright harness for Tau web UI browser testing.

## Local setup

From `tests/browser/`:

```bash
bun install --frozen-lockfile
bun run install:browsers
```

### Linux browser dependencies

If system dependencies are missing, run:

```bash
bun x playwright install-deps chromium webkit
```

## Installed-package and alternate-port runs

Set `TAU_BROWSER_PORT` to avoid another application listening on 8765.
Set `TAU_BROWSER_BIN` to an absolute installed `tau` executable to test a wheel:
this mode removes `PYTHONPATH` instead of injecting the source checkout.

```bash
TAU_BROWSER_PORT=8877 TAU_BROWSER_BIN=/path/to/venv/bin/tau npx playwright test specs/classic-assets.spec.mjs specs/onboarding-layout.spec.mjs specs/settings-layout.spec.mjs
```

The sole UX reference is Piclaw **classic**, not visual mode. `full-reference.spec.mjs`
loads the pinned 2.15.3 classic index/bundle and editor vendor from
`/opt/piclaw/releases/piclaw-2.15.3-linux-x64-baseline/app/runtime/`.
`classic-paired.spec.mjs` captures Tau with shared message/time/model fixtures.
Run both, then `node build-visual-review.mjs` to export labeled classic-only
comparisons. These are review evidence, not approved pixel baselines.
`fixtures/classic-state.mjs` holds shared content; visual reference payloads
and the old source override have been removed.

## Run tests

```bash
bun test
bun run test:chromium
bun run test:webkit
```

## Project matrix

Six required projects are configured:

- Chromium phone (390x844)
- Chromium tablet (820x1180)
- Chromium desktop (1440x900)
- WebKit phone (390x844)
- WebKit tablet (820x1180)
- WebKit desktop (1440x900)

WebKit coverage is mandatory for release validation. `responsive.spec.mjs` and `accessibility.spec.mjs` cover behavior at all six targets. Full-layout pixel baselines must be recreated and approved after the Preact structural migration; do not use masks or CSS overlays to accept structural differences.

## Server isolation

`start-server.mjs` launches Tau web in a temporary isolated workspace/database:

- temp workspace directory created per run
- temp SQLite database per run
- UTF-8 fixture files seeded safely
- `TAU_WEB_AUTH_TOKEN` explicitly unset
- `PYTHONPATH` prepends `/workspace/tau/src` so the venv `tau` entrypoint loads the working tree (not stale site-packages)
- `PATH` prepends `/workspace/tau/.venv/bin` when needed
- Playwright launch readiness waits for `http://127.0.0.1:8765/api/health` (tests still use origin root as `baseURL`)
- signals forwarded with process-group-aware shutdown (no shell)
- temp data cleaned on exit

## Artifacts

On failures, Playwright keeps:

- traces
- screenshots
- videos

Artifacts are written under `test-results/` and `playwright-report/`.

### Reproduce the WebKit offline-navigation limitation

The normal suite skips WebKit offline reload (but verifies its precache).
To run the known failing path explicitly:

```sh
TAU_BROWSER_PORT=8876 TAU_PROBE_WEBKIT_OFFLINE=1 npx playwright test specs/service-worker.spec.mjs --project=webkit-desktop --reporter=line
```

Latest probe: cache verification passes; `page.reload` after `setOffline(true)`
reports `WebKit encountered an internal error`. This is not an offline-delivery
sign-off. The cache test also checks the root document and successful, nonempty
responses for every cached asset. Offline state is restored even when reload fails.
