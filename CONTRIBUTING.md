# Contributing to Tau

Thanks for helping improve Tau. Tau is both a usable terminal coding agent and a teaching codebase for understanding how coding agents are built. Contributions should preserve that dual purpose: make the tool better while keeping the architecture small, readable, and easy to learn from.

## Project philosophy

Tau is organised around five packages:

```text
tau_ai          provider/model streaming layer
tau_agent       portable agent harness, loop, tools, events, sessions
tau_coding      CLI app, shared session/runtime orchestration, resources, skills, print mode and TUI
tau_extensions  portable extension discovery, manifests, resolution and runtime contracts
tau_web         optional browser runtime, HTTP routes, and shared SQLite persistence/interchange
```

The key boundary is still:

```text
AgentHarness = reusable agent brain
AgentSession = coding-agent environment
TUI, print mode, and Tau Web = frontends over shared session machinery
```

Please keep these principles in mind:

- **Small layers beat magic.** Each package should have one clear job.
- **Events are the contract.** The harness emits typed events; UI and renderers consume them.
- **The core stays portable.** `tau_agent` should not depend on the CLI, Textual, Rich, local config paths, or Tau-specific resource loading.
- **Tools are ordinary typed functions.** Prefer explicit schemas and structured results.
- **Sessions are durable and inspectable.** Avoid changes that make history hard to read, resume, or export.
- **Documentation follows implementation.** User-facing behaviour and architectural decisions should be documented.

## Local development

Use a Python 3.13+ virtual environment for Python commands so they run in the project environment. `uv` is supported, but the standard `pip` flow is:

```bash
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install .
# Optional, if you are touching tau web, SQLite import/export, or tests/web
python -m pip install ".[web]"
tau --version
```

The in-tree build backend does not provide editable installs, so run Tau from the checkout with `PYTHONPATH=.:src`:

```bash
PYTHONPATH=.:src tau
PYTHONPATH=.:src tau -p "explain this repo"
```

## Contributor workflow

### Starting from a GitHub issue

1. Pick an issue from the [issue tracker](https://github.com/huggingface/tau/issues)
2. Create a branch with a descriptive name:

```bash
# Feature
 git checkout -b feat/issue-123-short-description

# Bug fix
 git checkout -b fix/issue-456-short-description

# Documentation
 git checkout -b docs/issue-789-short-description
```

3. Make your changes, following the guidelines below
4. Open a pull request referencing the issue: `Fixes #123`

### Using Git worktrees (optional)

Worktrees let you work on multiple issues simultaneously without stashing or switching branches:

```bash
# Create a worktree for a new feature (from the repo root)
 git worktree add ../tau-feat-123 -b feat/issue-123-short-description

# Work inside it
cd ../tau-feat-123
uv sync --dev
uv run pytest

# When done, clean up
cd /path/to/tau
 git worktree remove ../tau-feat-123
```

This keeps your main checkout clean while you work on parallel features, bugfixes, or documentation.

### Using contributor prompts

Tau ships with reusable prompt templates in `.agents/prompts/` for common contributor tasks. Inside Tau, invoke them with a `/` prefix:

| Prompt | Description |
|--------|-------------|
| `/implement-feature` | Implement a feature from a GitHub issue |
| `/fix-bug` | Fix a bug with reproduction steps |
| `/add-test` | Add or update tests for an area |
| `/write-dev-notes` | Write developer notes for a phase |
| `/update-docs` | Update website documentation |

Example usage inside Tau:

```text
/implement-feature https://github.com/huggingface/tau/issues/123
/fix-bug https://github.com/huggingface/tau/issues/456
/add-test tau_coding/provider_config.py
```

These prompts guide the coding agent to follow Tau's conventions, including layer separation, testing, and documentation expectations.

### Using `gh` CLI for issues and PRs

The GitHub CLI (`gh`) makes it easy to work with issues and pull requests:

```bash
# List open issues
gh issue list --repo huggingface/tau

# View an issue
gh issue view 123 --repo huggingface/tau

# Create a PR from your branch
gh pr create --title "feat: description" --body "Fixes #123"

# Check PR status
gh pr status --repo huggingface/tau

# View PR checks
gh pr checks 207 --repo huggingface/tau
```

### Recommended development sequence

1. **Read the issue** — `gh issue view 123 --repo huggingface/tau`
2. **Set up your environment** — `python -m pip install -r requirements-dev.txt && python -m pip install .` (plus `python -m pip install ".[web]"` when working on Tau Web, SQLite import/export, or `tests/web`)
3. **Create a branch or worktree** — follow naming conventions above
4. **Implement changes** — follow layer boundaries below
5. **Write tests** — use fake providers/tools for deterministic tests
6. **Run checks** — `PYTHONPATH=.:src python -m pytest`, `python -m ruff check .`, `PYTHONPATH=.:src python -m mypy src`
7. **Update docs** — `dev-notes/` for substantial changes, `website/src/content/docs/` for published user docs, and `docs/` for technical runtime notes
8. **Commit** — one coherent change per commit
9. **Push and open a PR** — `git push origin feat/issue-123-desc` then `gh pr create`

## Checks before submitting

Run the relevant focused tests while developing, then run the full checks before opening a pull request when practical:

```bash
PYTHONPATH=.:src python -m pytest
python -m ruff check .
python -m ruff format --check .
PYTHONPATH=.:src python -m mypy src
```

If you touch Tau Web, SQLite-backed session import/export, or `tests/web`, install the optional web dependencies first and run the relevant web checks as well:

```bash
python -m pip install ".[web]"
PYTHONPATH=.:src python -m pytest tests/web
cd src/tau_web/frontend && bun install --frozen-lockfile && bun run check && bun run build && cd ../../..
node --check src/tau_web/static/app.js
node --check src/tau_web/static/live-ui.js
node --check src/tau_web/static/extension-ui.js
cd tests/browser && bun install --frozen-lockfile && bun test && cd ../..
```

For the documentation site:

```bash
cd website
bun install
bun run dev
bun run build
```

## Where changes belong

Use the layer boundaries to decide where code should live:

- Provider integrations, model adapters, and provider-neutral streaming belong in `tau_ai`.
- Agent loop behaviour, tool abstractions, events, messages, harnesses, and portable session primitives belong in `tau_agent`.
- CLI behaviour, slash commands, shared session/runtime orchestration, print mode, TUI integration, local config, resources, skills, prompt templates, and coding-specific tools belong in `tau_coding`.
- Portable extension discovery, manifests, resolution, and runtime contracts belong in `tau_extensions`.
- The optional browser runtime, HTTP routes, static shell assets, SQLite runtime store, and JSONL interchange live in `tau_web`.
- Textual-specific code should stay behind the TUI layer.
- Rich rendering should not leak into the reusable agent harness.
- Keep optional web dependencies lazy: non-web code paths should not require `aiohttp`, Pillow, or other `tau-prime[web]` extras.

If a change crosses layers, prefer adding a small typed boundary instead of importing app-specific details into core code.

## Storage and migration expectations

- The live durable session store is SQLite by default; do not add new features that depend on per-project JSONL files as live state.
- Session history remains append-only even in SQLite. Repairs, compaction, summaries, labels, branch updates, and similar changes should append durable entries instead of rewriting transcript history in place.
- JSONL still matters for export/import and older transcripts, but it is an interchange format rather than the primary live store.
- Database migrations in `src/tau_web/sqlite/migrations.py` are forward-only and append-only. Add a new numbered migration instead of editing an already-shipped migration in place.
- Preserve the current SQLite invariants: WAL mode, foreign keys, and `json_valid(...)`-style constraints on structured JSON columns.

## Testing expectations

- Add or update tests for behaviour changes.
- Use fake providers and fake tools for deterministic agent-loop tests.
- Keep core tests free of provider-specific assumptions.
- Add regression tests for bugs.
- Prefer focused tests that describe the behaviour being protected.
- If you touch `src/tau_web/static/`, keep DOM updates explicit and safe: prefer `createElement`, `textContent`, and `replaceChildren`; avoid `innerHTML`, `eval`, or HTML-string injection for data-bearing UI updates.

## Documentation expectations

For substantial architectural or phase-oriented work, add beginner-friendly notes under `dev-notes/` explaining:

- what changed
- why it exists
- how it maps to Tau's architecture
- how to test or use it

When behaviour changes, update the matching docs in the same change:

```text
website/src/content/docs/   published user documentation
docs/                       technical runtime and platform notes
README.md                   top-level install, packaging, and workflow expectations
```

## Release process

Tau is published to PyPI as `tau-prime`. Publishing is a production release action,
not a side effect of every commit merged to `main`.

To prepare a release, intentionally bump `[project].version` in `pyproject.toml`
and merge that change through a pull request. The PyPI workflow publishes only
when it detects that version change, or when a maintainer uses an explicit
release trigger such as a published GitHub Release or manual workflow dispatch.
See [dev-notes/release-process.md](dev-notes/release-process.md) for the full
process.

## Pull request guidelines

Good Tau pull requests are small, focused, and easy to review. Please include:

- the motivation for the change
- a summary of behaviour changes
- tests or checks you ran
- screenshots or terminal output for TUI/CLI changes when useful
- notes about compatibility, migrations, config changes, or provider-specific behaviour

Avoid unrelated refactors in feature or bug-fix PRs. If a larger design change is needed, open an issue or discussion first.

## Roadmap alignment

Tau is developed incrementally. For larger changes, check the roadmap issue before starting:

<https://github.com/alejandro-ao/tau/issues/1>

When in doubt, favor the smallest step that preserves the architecture and teaches the design clearly.
