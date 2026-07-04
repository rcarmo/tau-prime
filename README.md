<p align="center">
  <img src="docs/assets/tau-header.svg" alt="Tau — a Python coding-agent harness inspired by Pi" width="100%" />
</p>

<p align="center">
  <strong>A small, readable terminal coding agent — and a working example of how coding agents are built.</strong>
</p>

<p align="center">
  <strong>This fork tracks the iOS/a-Shell port with GitHub Copilot support and mobile-friendly TUI defaults.</strong>
</p>

<p align="center">
  <a href="https://twotimespi.dev/">Documentation</a>
  ·
  <a href="https://twotimespi.dev/quickstart/">Quickstart</a>
  ·
  <a href="https://twotimespi.dev/internals/architecture/">Architecture</a>
  ·
  <a href="https://pypi.org/project/tau-ai/">PyPI</a>
  ·
  <a href="https://github.com/alejandro-ao/tau/issues/1">Roadmap</a>
</p>

---

## What is Tau?

**Tau is a coding agent that lives in your terminal.** You type requests like
"explain this repo", "add tests", or "fix this stack trace"; Tau can read files,
edit code, run commands, and keep a durable session history while streaming what
it is doing.

Tau is also meant to be read. It is a teaching project for understanding the
shape of a coding-agent system without starting from a giant production
codebase.

```text
tau_coding  →  tau_agent  →  tau_ai
```

- `tau_ai` translates model providers into Tau's provider-neutral stream.
- `tau_agent` owns the portable brain: messages, tools, events, loop, harness,
  and session primitives.
- `tau_coding` wraps the brain as a real coding app: CLI, TUI, file/shell tools,
  provider config, project instructions, skills, and on-disk sessions.

The important boundary is:

```text
AgentHarness = reusable brain
CodingSession = coding-agent environment
TUI = one possible frontend
```

The core does not know about Textual, Rich, local config paths, slash commands,
or rendering. Frontends consume events.

## Install

Tau is published on PyPI as `tau-ai` and installs a `tau` command.

```bash
uv tool install tau-ai
tau --version
```

Prefer `pip`?

```bash
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install tau-ai
```

To install from a source checkout or source tarball:

```bash
python -m pip install -r requirements.txt
python -m pip install .
tau --version
```

For this iOS/a-Shell fork:

```sh
git clone https://github.com/rcarmo/tau-a-shell.git
cd tau-a-shell
python3.13 -m pip install --user -r requirements.txt
python3.13 -m pip install --user .
tau --version
```

For local development on a regular desktop Python environment:

```bash
git clone https://github.com/rcarmo/tau-a-shell.git
cd tau-a-shell
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install .
tau --version
```

## Quickstart

Run Tau from the project you want it to work on:

```bash
cd my-project
tau
```

Then type a request and press **Enter**:

```text
explain what this project does
```

One-shot print mode is useful for scripts and quick prompts:

```bash
tau -p "summarize the architecture"
tau --cwd /path/to/project -p "find the CLI entry point"
```

Tau needs a model provider. Start Tau and connect one with `/login`:

```bash
tau
```

```text
/login
/login openai
/login openai-codex
/login github-copilot
/model
```

This fork adds GitHub Copilot subscription auth and live Copilot model discovery
alongside OpenAI, Anthropic, OpenAI Codex subscription auth, OpenRouter, Hugging
Face, and custom OpenAI-compatible endpoints, including local models. See the
[providers guide](https://twotimespi.dev/guides/providers-and-models/).

## What Tau can do

- Interactive Textual TUI and non-interactive print mode.
- iOS/a-Shell-friendly TUI behavior, including `Ctrl+C`/`Cmd+.` cancellation,
  responsive redraws, transcript auto-scroll, and a sidebar hidden by default
  with `Ctrl+B` to toggle it.
- Built-in coding tools: `read`, `write`, `edit`, `sh`, Python, and `pytest`,
  with compatibility aliases for existing `bash` integrations.
- Durable JSONL sessions under `~/.tau/sessions/` with resume and branching.
- Slash commands for login, model selection, sessions, compaction, export, theme,
  and more.
- Project instructions from `AGENTS.md`, `.tau/`, and `.agents/` resources.
- User skills and prompt templates.
- Context accounting, manual compaction, and optional automatic compaction.
- GitHub Copilot provider support with device login, dynamic model discovery,
  and Copilot-hosted Claude/Gemini/OpenAI models kept on the Copilot-compatible
  runtime path.
- Provider-neutral event rendering for Rich, plain text, JSON, transcripts, and
  custom frontends.

## Philosophy

Tau follows a few rules:

- **Small layers beat magic.** Each package has one job and can be read alone.
- **Events are the contract.** Providers, renderers, the TUI, and custom
  frontends meet at a typed event stream.
- **The core stays portable.** The reusable harness does not depend on the CLI,
  Textual, Rich, or Tau's file layout.
- **Tools are ordinary typed functions.** A tool is a schema plus an async
  executor returning a structured result.
- **Sessions are durable and inspectable.** History is append-only JSONL; active
  context can be compacted without rewriting the record.
- **Documentation follows implementation.** The public docs explain the result;
  `dev-notes/` preserves the phase-by-phase build journal.

## Use Tau as a library

```python
from tau_agent import AgentHarness, AgentHarnessConfig

harness = AgentHarness(
    AgentHarnessConfig(
        provider=provider,
        model="my-model",
        system="You are a helpful coding agent.",
        tools=tools,
    )
)

async for event in harness.prompt("Explain this package"):
    print(event)
```

Because the harness emits events instead of rendering UI directly, the same core
can drive the built-in TUI, print mode, or a frontend you build yourself.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for project philosophy, layer boundaries, testing expectations, and pull request guidelines.

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Run Tau from the checkout:

```bash
uv run tau
uv run tau -p "explain this repo"
```

Run the Astro/Starlight documentation site:

```bash
cd website
bun install
bun run dev
```

Open <http://localhost:4321/>. Build with `bun run build`.

## Documentation

User docs are published at <https://twotimespi.dev/> and live in
`website/src/content/docs/`.

Useful entry points:

- [What is Tau?](https://twotimespi.dev/what-is-tau/)
- [Quickstart](https://twotimespi.dev/quickstart/)
- [Core concepts](https://twotimespi.dev/concepts/)
- [Architecture overview](https://twotimespi.dev/internals/architecture/)
- [The agent loop & events](https://twotimespi.dev/internals/agent-loop/)
- [CLI reference](https://twotimespi.dev/reference/cli/)

Tau is under active development. The implementation roadmap is tracked in
[GitHub issue #1](https://github.com/alejandro-ao/tau/issues/1).

## License

Tau is released under the [MIT License](LICENSE).
