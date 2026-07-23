# Tau Prime CLI

The executable remains `tau` even though the package is `tau-prime`.

## Main modes

- Interactive TUI: default when no print prompt is supplied.
- Print mode: `tau -p "prompt"` for one-shot output.
- Basic REPL: used on constrained iOS/a-Shell terminals when the Textual TUI is unsuitable.
- Textual web mode: development/debug path for browser-hosted TUI.

## Important flags

- `--cwd PATH` selects the working directory and, on macOS, the writable sandbox project root.
- `--resume SESSION_ID` resumes a durable session.
- `--new-session` forces a fresh indexed session.
- `--provider` and `--model` select provider/model pairs; provider/model compatibility must stay atomic.
- `--auto-compact-threshold` overrides automatic context compaction threshold.
- `--no-sandbox` is the explicit macOS override for default sandboxing.

## Exit/resume behavior

After a normal TUI exit, Tau Prime prints a `tau --resume <session-id>` hint when the session is persisted.

## Unknown slash input

Unknown slash-prefixed input is treated as an ordinary prompt. This preserves absolute paths and prompt text that happen to begin with `/`.

## macOS sandbox

On macOS, Tau Prime re-execs through `/usr/bin/sandbox-exec` by default and fails closed if it cannot establish the sandbox. The sandbox constrains writes, not reads or network access. See `docs/sandboxing.md` in the repository for details.
