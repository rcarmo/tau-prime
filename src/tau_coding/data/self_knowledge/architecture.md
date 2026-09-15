# Tau Prime architecture

Tau Prime follows the same broad layering as Tau but the fork has mobile, provider, and packaging constraints that affect where changes belong.

## Packages

- `tau_ai` owns provider adapters, provider-neutral streaming events, model listing, retry helpers, HTTP helpers, observability, and provider-native capabilities such as remote compaction or runtime model limits.
- `tau_agent` owns portable agent primitives: messages, tools, tool results, the agent loop, harness state, event models, append-only session entries/tree semantics, storage interfaces, and branch replay.
- `tau_coding` owns the coding product: CLI, TUI, commands, resources, provider configuration, credentials/OAuth, session manager integration, compaction policy, rendering, packaging-facing behavior, and system prompt assembly.
- `tau_extensions` owns portable extension discovery, manifests, resolution, and runtime contracts.
- `tau_web` owns the optional browser runtime, HTTP routes, static shell assets, the shared SQLite runtime store, and JSONL import/export interchange.

## Placement rules

- Put provider transport details in `tau_ai`, not the TUI or CLI.
- Put portable event/message/tool semantics in `tau_agent`, not `tau_coding`.
- Put product policy, user settings, slash commands, and resource discovery in `tau_coding`.
- Keep a-Shell and macOS sandbox behavior out of provider adapters.
- Keep fork branding and release behavior out of portable layers.

## Event architecture

Tau Prime currently emits legacy Tau events and Pi-shaped `message_update` events. The TUI consumes `message_update` as the primary assistant stream while legacy events remain available for compatibility.

## Session architecture

SQLite is the sole live durable session store. The durable session model is still an append-only entry tree: compaction, branch summaries, model changes, labels, session info, and custom extension entries append durable entries and leaf updates instead of rewriting transcript history in place. Preserve the current SQLite invariants: WAL mode, foreign keys, and `json_valid(...)`-style constraints on structured JSON columns. JSONL remains import/export and legacy interchange only; it is not the authoritative live store.
