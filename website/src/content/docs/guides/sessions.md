---
title: Sessions
description: Resume past conversations, branch from any point in history, rename sessions, and export them.
---

Every Tau conversation is a **session**, saved durably so you can come back to
it. Live sessions are stored in SQLite by default at `~/.tau/tau.sqlite3`.
Resume flows still focus on the project you're in by recording each session's
working directory and surfacing it in lists and pickers.

## Listing sessions

```bash
tau sessions
```

Each row shows the session id, title, model, and working directory.

## Resuming

From the shell:

```bash
tau --resume <session-id>
```

From inside the TUI:

```text
/resume            # open a picker of past sessions
/resume <id>       # resume a specific session
```

To deliberately start fresh instead of resuming, use `tau --new-session` (or
`/new` in the TUI).

## Branching from history (`/tree`)

A session is a *tree*, not just a line — so you can go back and try a different
path without losing what you had.

Run `/tree` to open the session tree, then select an earlier entry:

- **Enter** — continue from that point, preserving the existing branch.
- **S** — ask the active model for a structured summary of the messages you're
  leaving behind before moving the active point.
- **C** — provide custom focus instructions for that one summary.

If a summary request fails, Tau falls back to a deterministic summary.

## Renaming

```text
/name My refactor session
```

The new name appears in the `/resume` picker and id completions.

## Exporting

Export a session to a shareable file:

```text
/export                              # HTML, default file: tau-session.html
/export --format jsonl               # JSONL interchange: tau-session.jsonl
/export --format html report.html    # explicit destination
```

Or from the shell:

```bash
tau export <session-id>                     # HTML (default)
tau export <session-id> session.html
tau export <session-id> --format jsonl
tau export ./older-session.jsonl report.html
```

For live sessions, `/export` and `tau export` read from SQLite. The shell
command also accepts an existing Tau JSONL transcript or export path for
compatibility. HTML exports are self-contained and include the preserved
session tree plus the transcript in storage order.

If you specifically want JSONL interchange with the live store, use the
explicit import/export commands:

```bash
tau export-session <session-id> --output session.jsonl
tau import-session session.jsonl --workspace /path/to/project
```

`tau export-session` writes Tau JSONL from one SQLite-backed session.
`tau import-session` validates a Tau JSONL file and records it in SQLite with
workspace, provider, model, and optional title metadata.

## Where sessions live

```text
~/.tau/tau.sqlite3
```

Tau stores live sessions, workspaces, aliases, and session metadata in this
single database by default. The session tree is still append-only at the entry
level -- compaction and branching change the *active* view, not the recorded
history.

Older `~/.tau/sessions/` JSONL trees may still exist from earlier releases. Tau
does not use them as the live durable store any more, but `tau export
<path-to-jsonl>` and `tau import-session` let you keep moving data in and out.
See [Configuration](../reference/configuration.md#sessions) for the exact
layout.
