# Hugging Face Tau adoption review

Final review of `feat/hf-upgrades-and-ui-parity` against upstream inventory commit `d2665af` and adoption base `5a2f915`.

## Selected patches

| Upstream behavior | Tau Prime result |
| --- | --- |
| Anthropic transient retries (`809e0e6`) | Covered by `ad002e3`; existing provider-layer retry implementation retained. |
| Provider-neutral tool history (`3583456`) | Manually adapted in `fffc90a` without replacing the agent loop or SQLite recovery. |
| One-hour Anthropic cache billing (`5bf70e5`) | Persisted in `d66da5f` and presented/priced in `3138cec`. |
| OpenAI cache affinity (`1401fcd`) | Added through current session/provider seams in `05d474d`. |
| Hugging Face resolved/sticky routing (`ee3d57f`, `ea84782`) | Persisted and isolated per session in `e0df0e6` and `5961f78`. |
| Kimi K3 reasoning levels (`a8b155a`) | Adapted to Tau Prime normalization in `252e6b5`. |
| Export cache analytics/CSS (`135b4b0`, `24a26e0`) | Adapted to aggregate `ProviderUsage` in `845ffb5`; unavailable per-request timestamps were intentionally not fabricated. |
| Light Markdown accents (`0d02472`) | Applied to the active theme in `1c3671d`. |
| Explicit invalid-model errors (`4ffef3e`) | Already present and covered by startup regression tests. |

## Intentional omissions

- `src/tau_coding/session_stats.py` and `src/tau_coding/session_usage.py` remain absent. Tau Prime keeps aggregate usage records and its existing exporter.
- Upstream product architecture, branding, installers, website/release machinery, and unrelated commits remain rejected as recorded in `huggingface-adoption-inventory.md`.
- Canonical model identity remains durable; provider aliases are request-boundary details.
- Tau Prime's `CodingSession`, SQLite live store, TUI/print behavior, extension seams, sandbox/mobile support, and custom packaging backend remain authoritative.

## Architecture checks

- `src/tau_agent/loop.py` was incrementally extended for Tau Prime event, approval, routing, and cache-usage behavior; it was not replaced with the upstream loop.
- No obsolete upstream statistics module was restored.
- Web onboarding uses the existing credential and provider-settings stores and returns redacted status only.
- Preact owns shell and interaction visibility/selection state; existing typed API/legacy bridges remain narrowly scoped to durable session, SSE, extension, and renderer contracts.

## Validation evidence

- Complete Python suite: 1,318 passed using Tau's venv (with a temporary `python` executable shim required only by this container).
- Browser matrix: 18 passed across Chromium/WebKit at phone, tablet, and desktop sizes.
- Reproducibility: two independent source distributions and wheels compared byte-for-byte.
- Clean-install smoke test: packaged CLI help, packaged static assets, `tau web`, `/api/health`, and first-run `/api/onboarding` all passed.
- Visual pixel approval remains pending because approved Vibes/Piclaw reference images are not present in the repository or Git history.
