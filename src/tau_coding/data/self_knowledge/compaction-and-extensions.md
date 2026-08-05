# Tau Prime compaction and extensions

## Compaction

Tau Prime has adaptive local compaction plus verified provider-native compaction.

- Local strategies: `summary` and `pipelined`.
- Provider-native compaction is explicit and fail-closed for verified OpenAI/Codex endpoints.
- Opaque provider-native state is stored in `CompactionEntry.details` and replayed only for compatible provider/model/base URL.
- Do not summarize or expose opaque provider-native sentinels as human-readable context.
- `/compaction` controls provider-native enablement and local strategy in the TUI.

## Extension runtimes

Tau Prime retains the Python `setup(tau)` compatibility seam from `.tau/extensions` and `.agents/extensions`. It supports tools, slash commands, prompt guidelines, input hooks, agent/lifecycle/tool listeners, and custom message/tool renderers.

The separate portable `tau_extensions` runtime provides manifests, trust resolution, lifecycle ownership, scoped services, declarative views/actions, file renderers, annotations, sandboxed widgets, and administrator-trusted frontend modules. Tau Web ships HTTP and browser adapters for those services, but its stock server does not discover or import portable extensions automatically; an embedding host registers approved service bundles.

## Event protocol

Tau Prime emits Pi-shaped `message_update` events with assistant sub-events while retaining legacy Tau events for compatibility. The TUI adapter consumes `message_update` as the primary assistant stream.
