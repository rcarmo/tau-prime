# Tau Vibes implementation baseline

Captured on 2026-08-04 from branch `vibes` at design commit `399d99d`.

## Commands

```sh
PYTHONPATH=src /tmp/tau-venv/bin/python -m pytest -q
/tmp/tau-venv/bin/python -m ruff check src tests
PYTHONPATH=src /tmp/tau-venv/bin/python -m mypy src
```

## Results before implementation

* Pytest: 804 passed, one environment-only failure. `tests/test_coding_tools.py::test_bash_tool_does_not_read_parent_stdin` invokes bare `python`, which is not installed in this container; it exits 127 before exercising the assertion.
* Ruff: 33 existing findings across the source and tests.
* mypy: 17 existing errors across six source files.

These counts are the comparison baseline. New or touched implementation modules must pass Ruff and mypy even while unrelated historical findings remain.

## Adoption progress (2026-08-07)

The browser foundation now builds a committed TypeScript/Preact bundle and serves Piclaw-derived reference CSS. Preact owns the activity/status bars, dashboard, session navigation, central timeline, composer, and workspace/search/plan/settings side panel while preserving the IDs and extension slots consumed by the established runtime adapters. Only overlays remain transitional; full-layout visual baselines are intentionally deferred until that structural migration is complete.

Bare `tau` now reaches TUI provider discovery with an empty configuration instead of rejecting an empty model. Configured defaults still resolve normally, and explicitly invalid provider/model requests still fail cleanly. Tau Web credential APIs and browser onboarding remain outstanding.

## Compatibility gates

* TUI remains the default interactive mode and retains provider/model/thinking, command, tool, branch, compaction, queue and extension behaviour.
* Print mode remains usable without importing aiohttp, aiosqlite, Pillow or frontend assets.
* Existing `tau --web` continues to mean the legacy Textual web server during migration; the new browser product is invoked as `tau web`.
* macOS and Linux sandbox entry happens before either TUI, print or Tau Web starts.
* SQLite becomes the only live durable session store for TUI, print and Tau Web once migration lands. JSONL remains import/export and fixture data only.
* Existing session IDs and append-only entry/branch semantics survive JSONL import and SQLite export round trips.
* a-Shell and other constrained installs can install Tau without the `web` extra and import all ordinary CLI/TUI modules successfully.
