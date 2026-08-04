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

## Compatibility gates

* TUI remains the default interactive mode and retains provider/model/thinking, command, tool, branch, compaction, queue and extension behaviour.
* Print mode remains usable without importing aiohttp, aiosqlite, Pillow or frontend assets.
* Existing `tau --web` continues to mean the legacy Textual web server during migration; the new browser product is invoked as `tau web`.
* macOS and Linux sandbox entry happens before either TUI, print or Tau Web starts.
* SQLite becomes the only live durable session store for TUI, print and Tau Web once migration lands. JSONL remains import/export and fixture data only.
* Existing session IDs and append-only entry/branch semantics survive JSONL import and SQLite export round trips.
* a-Shell and other constrained installs can install Tau without the `web` extra and import all ordinary CLI/TUI modules successfully.
