# Tau Prime

![Tau Prime icon](docs/icon_256.png)

Tau Prime is a derivative of [Tau](https://github.com/alejandro-ao/tau) maintained for running a terminal coding agent on iOS through [a-Shell](https://holzschu.github.io/a-Shell_iOS/) and with native sandboxing on macOS. The command remains `tau`.

The project keeps Tau's original Python agent architecture, but changes the parts that do not translate cleanly to a constrained mobile shell: terminal behaviour, command execution, provider support, installation and packaging. It also runs on ordinary Python 3.13 environments, which is useful for development and for testing changes before moving them to an iPhone or iPad.

It is not intended to track the upstream user experience or branding.

## What this fork changes

* The Textual interface uses mobile-friendly defaults: the sidebar starts hidden, `Ctrl+B` toggles it, transcript output follows new content, and terminal size is polled as a fallback when a-Shell does not deliver resize events.

* Shell tools work with a-Shell's constrained `sh` environment. The existing `bash` tool names remain available as compatibility aliases, so older sessions and prompts do not need to change.

* GitHub Copilot is a built-in provider. Device login, token refresh, live model discovery and Copilot-hosted OpenAI, Claude and Gemini models use the appropriate Copilot endpoint rather than being treated as generic OpenAI traffic.

* LM Studio is a built-in, credential-free provider. It defaults to `http://localhost:1234/v1`, accepts a persistent LAN URL override, discovers loaded models with a 3-second timeout and always uses `/v1/chat/completions`. `/reload` refreshes the active LM Studio model list.

* Session initialisation, OAuth polling and asynchronous cleanup have additional checks for the failure modes encountered on iOS and during interrupted logins.

* The source distribution has a repeatable Makefile workflow that runs the test suite, builds the package and checks it through an isolated `uvx` installation.

## Current limitations

The a-Shell port has to work around terminal behaviour rather than control it. Resize polling is present because resize events are not dependable on iOS, but exact redraw behaviour can still vary with the a-Shell and iOS versions in use.

On macOS, the command uses `/usr/bin/sandbox-exec`, which Apple has deprecated but still ships with current releases. Tau Prime stops rather than silently running without the sandbox if that executable is unavailable; `--no-sandbox` is the explicit override.

Local model servers normally run on another machine. Set LM Studio's provider URL to that machine's LAN address; `localhost` only works when the server is reachable from the same environment.

The repository contains upstream documentation and development notes, but this README describes the supported fork. Some upstream pages may refer to features, commands or installation paths that have not been checked on a-Shell.

## Requirements

* Python 3.13
* a-Shell on iOS or iPadOS for the mobile target
* Network access to at least one model provider
* `curl` for downloading the a-Shell release tarball
* Git, if working from a development checkout

A desktop Python 3.13 environment is recommended for development and package testing.

## Install on a-Shell

Install the source tarball attached to the latest Tau Prime release. Do not clone the repository on a-Shell:

```sh
curl -fL https://github.com/rcarmo/tau-prime/releases/latest/download/tau-prime.tar.gz \
  -o tau-prime.tar.gz
python3.13 -m pip install --user ./tau-prime.tar.gz
tau --version
rm tau-prime.tar.gz
```

The stable `tau-prime.tar.gz` asset always belongs to the latest release. Each release also includes a versioned copy and `SHA256SUMS`. To upgrade, download the current tarball and repeat the install command with `--upgrade`.

Run `tau` from the directory the agent should work on:

```sh
cd ~/Documents/my-project
tau
```

Use `Ctrl+B` if you want the sidebar. `Ctrl+C` or `Cmd+.` cancels the active operation without discarding the session.

## Install for desktop development

```sh
git clone https://github.com/rcarmo/tau-prime.git
cd tau-prime
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install .
tau --version
```

Run against the checkout's source tree with:

```sh
PYTHONPATH=src tau
```

If you want the optional browser runtime from a checkout, install the web extra as well:

```sh
python -m pip install ".[web]"
```

## Web frontends

Tau Prime has two distinct browser-facing modes:

* `tau web` runs Tau Web's browser UI and HTTP API. It uses the same SQLite session store as the TUI and print mode.

```sh
tau web
tau web --host 0.0.0.0 --port 8080
tau web --database /path/to/tau.sqlite3
```

`tau web` requires the optional web dependencies from `tau-prime[web]` (or `".[web]"` from a checkout).

* `tau --web` runs the Textual TUI through Textual's separate web server command. It is not the same feature as `tau web`.

```sh
tau --web
tau --web --web-host 0.0.0.0 --web-port 8000
```

For `tau --web`, install Textual's optional web server package so that `textual-web` or `textual-serve` is available on your `PATH`.

## macOS sandbox

macOS runs are sandboxed by default. Tau Prime re-executes the `tau` command through the system `sandbox-exec` utility, and the restriction is inherited by shell commands, Python, tests and their child processes.

The sandbox permits reads and network access, but filesystem writes are limited to:

* The starting directory, or the directory selected with `--cwd`.
* Tau Prime's resolved configuration and log directories.
* The current `$TMPDIR`.
* Terminal devices required by the CLI.

Use `--no-sandbox` when unrestricted execution is intentional:

```sh
tau --no-sandbox
```

This behaviour is macOS-only. a-Shell and other platforms do not attempt to invoke `sandbox-exec`. See [macOS sandboxing](docs/sandboxing.md) for the generated policy, startup flow, failure semantics and security boundary.

## Configure a provider

Start the interface and use `/login` or `/model`:

```text
/login
/model
```

The built-in provider catalogue includes:

* GitHub Copilot subscription authentication with live model refresh
* OpenAI and OpenAI Codex subscription authentication
* Anthropic
* Kimi For Coding
* ZAI/GLM coding models with live model refresh
* OpenCode Zen and OpenCode Go with live model refresh
* OpenRouter
* Hugging Face
* DeepSeek
* Nebius
* LM Studio
* Custom OpenAI-compatible endpoints

Credentials are stored under `~/.tau/`. LM Studio does not request or store a credential and does not send an `Authorization` header.

### LM Studio over the LAN

LM Studio listens on `http://localhost:1234/v1` by default. For an iPhone or iPad, configure the provider with the address of the machine running LM Studio, for example:

```text
http://192.168.1.50:1234/v1
```

The URL is retained in `~/.tau/providers.json`. Selecting LM Studio discovers the currently loaded models; `/reload` repeats discovery. A failed connection or an empty model list leaves the application usable and reports that LM Studio is offline or has no loaded model.

### GitHub Copilot

Choose GitHub Copilot from `/login`, complete the device flow in a browser and return to the terminal. The fork refreshes the available model list from Copilot rather than relying only on a static catalogue.

## Commands and tools

Interactive sessions support file reads and writes, targeted edits, shell commands, Python, tests, session history, branching, compaction, provider switching and model switching.

Useful commands include:

```text
/login
/model
/reload
/sessions
/compact
/export
/theme
```

Live sessions are stored in SQLite by default at `~/.tau/tau.sqlite3`. The TUI, print mode, `tau sessions`, `tau --resume`, and `tau web` all use that shared durable store. The session tree is still append-only — messages, model changes, compaction entries, and leaf pointers are preserved — but it now lives in SQLite rather than per-project JSONL files.

The shared database opens in WAL mode, enables foreign keys, and uses `json_valid(...)` constraints for structured JSON columns. JSONL is now an interchange format rather than the live store: `/export` and `tau export` can write HTML or JSONL artefacts, `tau import-session` imports Tau JSONL into SQLite, `tau export-session` exports one SQLite-backed session as Tau JSONL, and `tau export <path-to-jsonl>` can still read an older JSONL transcript directly.

Project instructions can be supplied through `AGENTS.md`, `.tau/` and `.agents/` resources. See [context compaction](docs/compaction.md), [SQLite storage and migration](docs/storage.md), [Tau Web operations](docs/web.md), and [extensions](docs/extensions.md).

One-shot mode is available for scripts and short queries:

```sh
tau -p "summarise this repository"
tau --cwd /path/to/project -p "find the command-line entry point"
```

## Code layout

The separation between the reusable agent, the coding session, the extension contracts and the frontends is deliberate:

```text
tau_ai          provider clients, runtime model metadata and provider-neutral events
tau_agent       messages, tools, agent loop, harness and append-only session primitives
tau_coding      coding tools, shared session/runtime orchestration, provider configuration, CLI, print mode and TUI
tau_extensions  portable extension discovery, manifests, resolution and runtime contracts
tau_web         optional browser runtime, HTTP routes, and shared SQLite persistence/interchange
```

`AgentHarness` contains the reusable agent loop. `CodingSession` supplies the coding environment and durable state. The TUI, print mode and `tau web` all sit on that shared session machinery, while `tau_extensions` deliberately stays decoupled from the browser server and its dependencies.

## Test and package

The default packaging target runs the complete test suite before building and smoke-testing the source distribution:

```sh
make package
```

To supply explicit tools or use a pre-built virtual environment:

```sh
make PYTHON=/path/to/python UVX=/path/to/uvx package
```

The resulting versioned archive and SHA-256 checksum are written to `dist/`.

Individual checks can be run with:

```sh
python -m pytest -q
python -m compileall -q src tests
git diff --check
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the package boundaries and testing expectations inherited from the upstream project.

## Upstream and licence

Tau Prime is derived from [alejandro-ao/tau](https://github.com/alejandro-ao/tau). Upstream remains the appropriate place for questions about the original project, its hosted documentation and its roadmap; Tau Prime issues belong in [rcarmo/tau-prime](https://github.com/rcarmo/tau-prime/issues).

The code remains available under the [MIT License](LICENSE).
