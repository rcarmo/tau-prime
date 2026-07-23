# Tau Prime architecture

Tau Prime follows the same broad layering as Tau but the fork has mobile, provider, and packaging constraints that affect where changes belong.

## Packages

- `tau_ai` owns provider adapters, provider-neutral streaming events, model listing, retry helpers, HTTP helpers, observability, and provider-native capabilities such as remote compaction or runtime model limits.
- `tau_agent` owns portable agent primitives: messages, tools, tool results, the agent loop, harness state, event models, append-only session entries, JSONL storage, and branch replay.
- `tau_coding` owns the coding product: CLI, TUI, commands, resources, provider configuration, credentials/OAuth, session manager, compaction policy, extensions, rendering, packaging-facing behavior, and system prompt assembly.

## Placement rules

- Put provider transport details in `tau_ai`, not the TUI or CLI.
- Put portable event/message/tool semantics in `tau_agent`, not `tau_coding`.
- Put product policy, user settings, slash commands, and resource discovery in `tau_coding`.
- Keep a-Shell and macOS sandbox behavior out of provider adapters.
- Keep fork branding and release behavior out of portable layers.

## Event architecture

Tau Prime currently emits legacy Tau events and Pi-shaped `message_update` events. The TUI consumes `message_update` as the primary assistant stream while legacy events remain available for compatibility.

## Session architecture

Sessions are append-only JSONL trees. Compaction, branch summaries, model changes, labels, session info, and custom extension entries are durable entries. Do not rewrite old transcript entries to compact or repair; append repair/summary entries instead.
