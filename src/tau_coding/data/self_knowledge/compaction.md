# Tau Prime compaction

Tau Prime has adaptive local compaction and explicit provider-native compaction.

## Local strategies

- `summary`: bounded structured checkpoint generation.
- `pipelined`: ordered event ledger that preserves provenance, tool outcomes, paths, corrections, and failures before final checkpoint generation.

Both strategies escape untrusted source text, bound tool output, use adaptive budgets, and fall back to deterministic summaries if model summarization fails.

## Provider-native compaction

Verified OpenAI/Codex native compaction stores opaque canonical provider state in `CompactionEntry.details`. The visible summary is a sentinel. Replaying this state is allowed only for a compatible provider/model/base URL.

Rules:

- Do not show encrypted canonical state as a human-readable summary.
- Do not summarize a provider-native sentinel locally.
- Fail closed on incompatible model/provider switches.
- Keep native compaction disabled for proxies, Copilot, LM Studio, and generic OpenAI-compatible endpoints unless explicitly verified.

## TUI settings

`/compaction` controls whether provider-native compaction is enabled and whether local fallback uses `summary` or `pipelined`.

## Session model

Compaction is append-only. It adds `CompactionEntry` and a leaf pointer; it does not delete old entries. Replay materializes a synthetic user summary on the active branch.
