---
title: Design principles
description: The handful of rules that keep Tau small, portable, and readable.
---

Tau follows a few principles consistently. They're why the codebase stays
approachable as it grows.

## Small layers beat magic

Each package has one job: `tau_ai` streams models, `tau_agent` runs the loop,
`tau_coding` is the application. You can read and test any layer on its own
without understanding the others. → [Architecture](./architecture.md)

## Events are the contract

The agent communicates progress through a stream of provider-neutral events.
Frontends render from those events, never from provider-specific chunks or
internal control flow. This is what lets print mode, the TUI, and custom
frontends share one core. → [The agent loop & events](./agent-loop.md)

## The core stays portable

`tau_agent` must not depend on Textual, Rich, the CLI, config directories, slash
commands, or app-specific resources. Those live in `tau_coding` and wrap the
core from outside. The reusable brain never reaches up into a UI.

## Tools are ordinary typed functions

A tool is a name, a description, a JSON input schema, and an async executor that
returns a structured result. There's no framework magic — which makes tools easy
to read, test, and add. → [Built-in tools](../reference/tools.md)

## Sessions are durable and inspectable

Every conversation is durably stored in SQLite. History is still an append-only
tree you can resume and branch; compaction changes the *active* context without
rewriting earlier entries. JSONL remains Tau's import/export interchange
format, and the live store stays inspectable with ordinary SQLite tools.
→ [Sessions](../guides/sessions.md)

## Documentation follows implementation

Tau was built in small, documented phases so a reader can trace how the system
grew. Those phase notes live in the repo under `dev-notes/` (see
[Contributing](../contributing.md)); these pages distill the result.
