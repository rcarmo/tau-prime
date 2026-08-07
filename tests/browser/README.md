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
