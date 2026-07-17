# Context compaction

Tau Prime uses two compaction paths. Both preserve the append-only session tree: old entries remain in JSONL history while the active branch receives a `CompactionEntry` that replaces selected context during replay.

Use `/compaction` in the TUI to choose whether provider-native compaction is enabled and whether the local strategy is `summary` or `pipelined`. The choice is stored in `~/.tau/tui.json`. Provider compaction is enabled by default and the default local strategy is `pipelined`.

## Provider-native compaction

Verified OpenAI Responses endpoints are attempted first:

* OpenAI API: `https://api.openai.com/v1/responses/compact`
* OpenAI Codex subscription: `https://chatgpt.com/backend-api/codex/responses/compact`

Support is explicit. Tau does not infer it from a model name and does not send native-compaction requests to proxies, Copilot, LM Studio, or generic OpenAI-compatible servers.

A successful endpoint response contains opaque canonical provider items, including encrypted compaction state. Tau persists those items in `CompactionEntry.details`; the visible summary is only a sentinel. On later requests the matching provider adapter removes that sentinel and prepends the canonical items to the provider payload.

Canonical state is bound to provider, model, API family, and base URL. A model or endpoint mismatch fails closed instead of exposing the sentinel or silently treating encrypted state as prose. If native compaction is unavailable or fails, Tau uses local compaction.

## Local smart compaction

The `summary` strategy creates a bounded structured checkpoint directly from source messages. The `pipelined` strategy first builds a complete ordered event ledger that preserves request/outcome provenance, corrections, failures and tool evidence before asking the model for the final checkpoint.

Both local strategies are provider-neutral and follow these rules:

* Context-window-aware reserve and recent-message budgets replace unconditional fixed budgets.
* System and tool-schema costs reduce the available retained-message budget.
* Source text and previous summaries are explicitly marked as untrusted data.
* Structural delimiters are escaped to prevent transcript text from closing prompt sections.
* Tool results and individual messages are bounded.
* Oversized source retains the beginning and recent tail with an explicit omission marker.
* Failed or empty model summaries fall back to a deterministic checkpoint.
* Automatic compaction rechecks context size and may make multiple bounded passes when one pass is insufficient.
* Manual compaction is rejected while an agent turn is active.

## Provider and model catalogue

The built-in catalogue is bootstrap metadata, not the sole source of truth. Providers marked for dynamic discovery may refresh model IDs and context metadata at runtime. Endpoint capabilities remain explicit because model IDs alone cannot establish that a proxy supports a provider-native API.

OpenAI and OpenAI Codex are now dynamic catalogue entries. GitHub Copilot and LM Studio retain their existing runtime discovery. LM Studio remains credential-free and forced onto chat completions; it cannot accidentally enter the OpenAI native-compaction path.

## Recovery and limitations

Provider-native state is intentionally opaque and cannot be converted into a trustworthy human-readable summary. Switching away from the exact provider/model after native compaction therefore requires returning to an earlier branch point or performing a supported migration; Tau will not guess.

Local deterministic fallback is deliberately lossy but keeps a session usable when summarization itself exceeds a provider limit or fails. Very large tool output is represented by bounded evidence rather than copied wholesale.
