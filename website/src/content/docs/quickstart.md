---
title: Quickstart
description: Install Tau, connect a model, and run your first coding session.
---

This page takes you from nothing to your first Tau session. It should take a few
minutes.

## 1. Install Tau

Tau is a Python 3.13+ tool. The fastest install path is
[`uv`](https://docs.astral.sh/uv/):

```bash
uv tool install tau-prime
```

You can also install with standard `pip`:

```bash
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install tau-prime
```

Run Tau without installing it:

```bash
uvx --from tau-prime tau --version
uvx --from tau-prime tau -p "summarize this repository"
```

From a source checkout:

```bash
python -m pip install -r requirements.txt
python -m pip install .
```

A local source tarball also works directly with `uvx`:

```bash
uvx --from ./tau_prime-42.3.0.tar.gz tau --version
```

Check it worked:

```bash
tau --version
```

## 2. Connect a model

Tau needs an AI model to talk to. A **provider** is the service that hosts the
model (OpenAI, Anthropic, …). Start Tau and use `/login` to connect one:

```bash
tau
```

Then run one of these inside Tau:

```text
/login              # choose a provider
/login openai       # save an OpenAI API key
/login openai-codex # authenticate a Codex/ChatGPT subscription
```

Tau ships with built-in entries for OpenAI, Anthropic, OpenAI Codex,
OpenRouter, and Hugging Face. See [Providers & models](./guides/providers-and-models.md)
for switching models or adding a custom/local OpenAI-compatible endpoint.

## 3. Start a session

Run Tau from inside the project you want to work on:

```bash
cd my-project
tau
```

This opens the interactive terminal UI. Type a request and press **Enter**:

```text
explain what this project does
```

Tau streams its response, and when it needs to, it reads files and runs commands
to answer you. Try something that changes code:

```text
add a docstring to every function in src/utils.py
```

You'll see each tool call (read, edit, bash) as it happens.

:::tip[Useful first keys]
**Enter** submits · **Esc** cancels the current run · **Ctrl+K** opens the
command palette · **Ctrl+D** quits. Full list in
[Keyboard shortcuts](./reference/keybindings.md).
:::

## 4. Come back later

Tau saves every session. List them:

```bash
tau sessions
```

Resume the most recent one for this directory, or pick from a list:

```bash
tau --resume <session-id>
```

…or open the picker inside the TUI with `/resume`. See
[Sessions](./guides/sessions.md) for resuming, branching, and exporting.

## Browser mode

Tau Web uses the same SQLite sessions as the TUI and print mode. Install the optional web dependencies, then start its loopback server:

```bash
uv tool install "tau-prime[web]"
tau web
```

For an ephemeral run:

```bash
uvx --from "tau-prime[web]" tau web
```

Open <http://127.0.0.1:8080/>. Binding to a non-loopback address needs deliberate authentication and origin configuration; see the repository's `docs/web.md` operations guide.

## One-shot mode

Don't need the UI? Run a single prompt and get the result on stdout — handy for
scripts and pipes:

```bash
tau -p "summarize the changes in the last commit"
```

More in [Print mode & scripting](./guides/print-mode.md).

## Where to go next

- **[Core concepts](./concepts.md)** — understand what's actually happening.
- **[The interactive session](./guides/tui.md)** — get fluent in the TUI.
- **[Providers & models](./guides/providers-and-models.md)** — switch models,
  add providers, use local models.
