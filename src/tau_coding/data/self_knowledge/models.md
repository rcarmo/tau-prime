# Tau Prime model metadata

Tau Prime uses static bootstrap catalog entries plus best-effort runtime model discovery.

## Static vs dynamic metadata

Static catalog entries provide default model IDs, context windows, thinking support, headers, endpoint URLs, and credential names. Dynamic refresh may replace model IDs and overlay context windows, but it must not discard known static context windows when the live provider omits them.

## Capability rules

Endpoint capabilities are explicit. Do not infer provider-native compaction, Responses support, or transport family from a model ID alone when the endpoint/provider is not verified.

## Context windows

Context windows drive auto-compaction thresholds. For dynamic providers, merge context metadata as:

1. built-in catalog context windows,
2. saved provider settings,
3. live `/models?verbose=true` context windows.

Live data wins when present; static data remains when live data is incomplete.

## Thinking modes

Thinking/reasoning support may be provider-wide, model-specific, always-on, or unavailable. Keep provider/model thinking defaults coherent when switching or resuming sessions.

## Current sensitive cases

- GitHub Copilot `gpt-5.6-*` must use Responses routing.
- Codex runtime model limits can override static context windows.
- LM Studio model metadata is local and transient; discovery failure must not break the UI.
- OpenCode, Kimi, ZAI/GLM, OpenRouter, and Hugging Face entries may be refreshed or routed differently by upstream; preserve Tau Prime endpoint behavior when syncing catalogs.
