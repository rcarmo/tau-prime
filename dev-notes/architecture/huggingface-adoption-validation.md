# Hugging Face adoption validation

Validated branch: `feat/hf-upgrades-and-ui-parity`

Validated commit: `44679f5876d06535758f5025dff6fb3a5b80ad1c`

Integration base: `c45d000c582b582ee5fb2e69fe1137ce44d479d6`

## Automated validation

Run from the repository root unless noted otherwise.

```sh
PATH="/workspace/tau/.venv/bin:$PATH" PYTHONPATH=src \
  .venv/bin/python -m pytest -q
```

Result: **1,319 passed** in 83.20 seconds. This includes SQLite migration and recovery, concurrent live-session/runtime behavior, CLI/TUI/print behavior, web API and SSE, extensions, provider behavior, packaging, and Linux/macOS sandbox policy tests.

The Makefile currently prepends the relative path `.venv/bin` to `PATH`. A shell-tool test changes its working directory and therefore cannot resolve `python` through that relative entry. Using the absolute virtual-environment path above avoids this test-harness defect; it does not change product behavior.

```sh
cd src/tau_web/frontend
bun run check
bun run build
cd ../../../tests/browser
npx playwright test --reporter=line
```

Result: TypeScript passed, the committed Preact shell was rebuilt, and **18/18** Chromium/WebKit interaction tests passed at `390x844`, `820x1180`, and `1440x900`.

Focused web and packaging validation:

```sh
PYTHONPATH=src:. .venv/bin/pytest -q \
  tests/web/test_frontend.py tests/web/test_packaging.py
```

Result: **35 passed**.

## Visual measurements

Live Piclaw and isolated Tau were captured in Chromium and WebKit at all target viewport sizes. After the canonical hierarchy, single-sidebar, chat-surface, light-theme, compact-composer, and status-bar changes, normalized whole-image RMS was:

| Browser | Phone | Tablet | Desktop |
| --- | ---: | ---: | ---: |
| Chromium | 0.2941 | 0.2815 | 0.2022 |
| WebKit | 0.2959 | 0.2828 | 0.2030 |

These are substantial improvements over the initial `0.76–0.84` range. They are **not** claimed as pixel-perfect approval: live Piclaw and isolated Tau contain different dynamic sessions and messages. The installed Piclaw application exposes no deterministic full-shell fixture, and no exact reference state or screenshot set has been approved. The adoption plan forbids masking those content differences or self-approving a baseline.

## Reproducible package

```sh
rm -rf dist && mkdir dist
PYTHONPATH=. .venv/bin/python - <<'PY'
import build_backend
print(build_backend.build_sdist("dist"))
PY
cp dist/tau_prime-42.3.0.tar.gz /tmp/tau-first.tar.gz
sleep 2
PYTHONPATH=. .venv/bin/python - <<'PY'
import build_backend
print(build_backend.build_sdist("dist"))
PY
cmp /tmp/tau-first.tar.gz dist/tau_prime-42.3.0.tar.gz
sha256sum dist/tau_prime-42.3.0.tar.gz
make uvx-test
```

Both builds were byte-identical. Artifact SHA-256:

```text
ff1c7ae615b0bf8da142e8958f014fa6edd6485ba7065d1b059c0078ab1b54b4
```

`make uvx-test` passed.

## Clean-install smoke test

A new virtual environment installed the generated source archive. With an isolated empty `HOME`, bare `tau` reached the provider/login onboarding surface rather than failing with `Model must not be empty`. Installing the archive's `web` extra and starting Tau Web produced:

```json
{"status":"ok","service":"tau-web","database":"ready","recovered_runs":0}
```

The packaged index referenced `preact-shell.js`, and the server returned the committed 65,598-byte bundle.

## Static-analysis status

Incremental Ruff and MyPy checks for adopted slices were run during implementation. Repository-wide checks still expose existing debt: 31 Ruff findings and 39 MyPy findings across 10 files. These findings are not introduced by the final visual slice and are not hidden in this report.

## Remaining approval gate

To complete the pixel-perfect visual-regression assertion, provide either:

1. approved Piclaw screenshots plus the exact theme, session, message, sidebar, overlay, and viewport state used to produce them; or
2. explicit approval to add and adopt a deterministic Piclaw full-shell fixture as the canonical baseline.
