# Provider catalog adoption analysis

Date: 2026-07-28

## Scope

Analyze upstream Tau's TOML-backed provider catalog architecture against Tau Prime's current in-code catalog and propose a safe adoption path that preserves Tau Prime's fork invariants:

- Keep package name `tau-prime` and executable `tau`.
- Preserve first-class LM Studio support: credential-free, dynamic model discovery, forced chat-completions, no authorization header.
- Preserve mobile/a-Shell behavior and source-tarball install flow.
- Preserve macOS sandbox default-on behavior.
- Preserve provider/model atomicity for resume, branch, scoped switching, and provider-native compaction state.
- Do not resurrect removed Google/Mistral providers without an explicit product decision.

## Current Tau Prime catalog model

Tau Prime currently defines provider metadata directly in `src/tau_coding/provider_catalog.py` as `ProviderCatalogEntry` instances. Runtime settings are represented by dataclasses in `provider_config.py`:

- `OpenAICompatibleProviderConfig`
- `AnthropicProviderConfig`
- `OpenAICodexProviderConfig`

The in-code catalog currently covers Tau Prime-specific providers and behavior, including:

- OpenAI, OpenAI Codex subscription, Anthropic, GitHub Copilot
- LM Studio as credential-free dynamic OpenAI-compatible provider
- Kimi/ZAI/OpenRouter/Hugging Face/DeepSeek/OpenCode/Nebius/NVIDIA
- static context windows and thinking metadata
- model overrides for provider-specific thinking semantics
- dynamic `/models` discovery for providers that need it

Provider settings are stored in `providers.json`. Built-ins are converted into runtime configs and merged with user settings. The existing approach is simple and deterministic but makes catalog-only changes require Python code edits and releases.

## Upstream main catalog architecture

Upstream Tau now has a TOML-backed catalog architecture:

- `src/tau_coding/data/catalog.toml` contains packaged built-in provider/model data.
- `src/tau_coding/catalog_loader.py` loads packaged and user catalog data.
- User overrides live in `~/.tau/catalog.toml`.
- `effective_catalog()` overlays user entries on built-ins by provider name.
- `save_user_catalog_entries()` persists user catalog entries.
- `ProviderCatalogEntry` is richer than Tau Prime's current entry:
  - provider API kind separate from provider kind
  - auth methods (`api_key`, `oauth`)
  - model metadata maps
  - pricing/cost tiers
  - multimodal input capability metadata
  - compatibility flags
- `provider_config.py` consumes the effective catalog rather than only a hard-coded tuple.

This architecture decouples catalog data from Python logic and enables user-editable catalogs, but it also introduces more surface area and upstream assumptions.

## Benefits of adopting some form of TOML catalog

1. **Faster catalog updates**
   - New models/providers can be added by editing TOML instead of Python dataclasses.

2. **User-extensible provider definitions**
   - Users can add OpenAI-compatible providers without changing `providers.json` internals or waiting for a release.

3. **Better metadata model**
   - Pricing, context windows, multimodal capabilities, and compatibility flags can be represented uniformly.

4. **Clearer separation of provider definitions from preferences**
   - Static catalog: what providers/models exist.
   - Settings: which provider/model is default, credentials, scoped models, remembered preferences.

5. **Potential alignment with Pi-style provider data**
   - Useful if Tau Prime wants closer ecosystem compatibility.

## Risks and incompatibilities

### 1. LM Studio must not regress

Tau Prime's LM Studio behavior is not a standard API-key provider:

- no credential required
- no Authorization header
- dynamic model discovery
- short timeout
- forced chat-completions path, never `/responses`

Any TOML architecture must represent these facts explicitly. A naive upstream catalog loader may assume credential-driven providers and could break LM Studio setup or runtime requests.

### 2. Provider kind/API separation can conflict with local routing

Upstream distinguishes provider `kind` and `api`; Tau Prime currently encodes most behavior through provider config class + runtime helpers. Migrating wholesale risks changing routing for:

- OpenAI GPT-5.6/5.5/5.4 responses API
- OpenAI Codex subscription responses API
- GitHub Copilot dynamic model discovery and URL handling
- Anthropic adaptive/disabled thinking
- OpenCode/OpenRouter provider-specific thinking overrides

### 3. Google/Mistral resurrection risk

Upstream's catalog includes provider kinds and API paths for Google and Mistral. Tau Prime intentionally removed those providers. Importing upstream files wholesale could reintroduce code paths, tests, dependencies, and user-visible options that the fork has not validated.

### 4. Packaging/a-Shell risk

The source tarball is Tau Prime's supported install artifact. Catalog resources must be included in the sdist and accessible under a-Shell/iOS path constraints. `importlib.resources` usage must be tested from installed tarballs, not only editable source trees.

### 5. User override migration risk

Existing `providers.json` users may already have custom OpenAI-compatible providers. A TOML catalog must not silently override, duplicate, or invalidate their preferences.

### 6. Validation complexity

A data-driven catalog needs strict validation to avoid runtime crashes from malformed user TOML. Tau Prime should fail safely:

- built-in catalog invalid: test/release failure
- user catalog invalid: warning/diagnostic, ignore invalid entries or keep previous settings
- provider selected from invalid user catalog: clear error with recovery path

## Recommended Tau Prime adoption path

### Phase 0: Analysis-only baseline

Keep the current in-code catalog as source of truth while documenting the desired TOML shape. Do not change runtime behavior.

Deliverables:

- this document
- test inventory for provider catalog invariants
- list of upstream fields to adopt or reject

### Phase 1: Add read-only TOML loader behind tests

Add a Tau Prime-specific loader module, but do not switch runtime defaults yet.

Suggested module:

- `src/tau_coding/catalog_loader.py`

Suggested functions:

- `builtin_catalog_resource_text() -> str`
- `load_catalog_toml(text: str) -> tuple[ProviderCatalogEntry, ...]`
- `catalog_to_toml(entries: Sequence[ProviderCatalogEntry]) -> str` only if needed later
- `validate_catalog(entries) -> list[ResourceDiagnostic]`

Initial goal: prove Tau Prime's existing in-code catalog can be represented in TOML without semantic loss.

Tests:

- packaged TOML loads in source tree
- packaged TOML is included in sdist
- loaded TOML entries equal or intentionally differ from in-code entries
- LM Studio entry round-trips with credential-free flags
- no Google/Mistral providers appear unless explicitly enabled

### Phase 2: Introduce packaged `data/catalog.toml` as a mirror

Generate or manually maintain a TOML mirror of Tau Prime's in-code catalog. Runtime still uses in-code catalog.

Purpose:

- exercise packaging and validation
- provide reviewable data format
- avoid runtime migration risk

Tests:

- `provider_catalog.py` entries and `data/catalog.toml` entries match important fields
- `make package` verifies TOML is included
- invalid TOML fixtures produce clear diagnostics

### Phase 3: Switch built-ins to load from packaged TOML with fallback

Runtime can use TOML built-ins if all invariants are covered. Keep the in-code catalog as fallback for one release series.

Suggested behavior:

```text
try load packaged TOML -> validate -> use entries
except error -> use in-code fallback and emit diagnostic
```

This preserves startup on broken packages and makes rollback trivial.

Tests:

- all existing provider_config tests pass unchanged
- LM Studio tests prove no Authorization header and forced chat-completions
- dynamic model discovery tests still pass
- scoped model/provider-model atomicity tests still pass
- installed sdist smoke test can access catalog resource

### Phase 4: Add user `~/.tau/catalog.toml` overlays

Only after packaged TOML is proven should Tau Prime accept user catalog overlays.

Recommended overlay semantics:

- match provider by `name`
- user entry fully replaces built-in provider definition by name, except credentials remain in `providers.json`
- invalid user entry is skipped with diagnostic, not fatal at global startup
- adding new provider requires explicit `kind`, `base_url`, `api_key_env`, `models`, `default_model`, and `docs_url`
- deleting built-ins via user catalog should not be supported initially

Important: `providers.json` remains the preference/credential/default/scoped-model store. `catalog.toml` defines provider capabilities.

### Phase 5: Rich metadata adoption

Adopt selected upstream rich metadata only after basic data loading is stable.

Candidate fields:

- `context_windows`
- `thinking_levels`, `thinking_models`, `thinking_default`, `thinking_parameter`
- `model_overrides`
- `input` capabilities for future vision/multimodal work
- `cost` metadata for UI/reporting only

Fields to defer:

- Google/Mistral API kinds
- auth-method abstractions beyond current API key/OAuth support
- multimodal provider payload semantics until the vision feature is intentionally ported

## Proposed Tau Prime TOML schema subset

A safe initial subset should mirror the current in-code dataclasses:

```toml
schema_version = 1

[[providers]]
name = "lmstudio"
display_name = "LM Studio"
kind = "openai-compatible"
base_url = "http://localhost:1234/v1"
api_key_env = "LM_STUDIO_API_KEY"
credential_name = ""
models = []
default_model = ""
docs_url = "https://lmstudio.ai/docs/developer/openai-compat"
dynamic_models = true
timeout_seconds = 3.0
force_chat_completions = true
omit_authorization_header = true
```

Tau Prime will need explicit fields not currently in upstream's generic schema:

- `force_chat_completions`
- `omit_authorization_header`
- possibly `requires_credentials = false`

Alternatively those can remain hard-coded overrides for `lmstudio`, but explicit data is safer and easier to validate.

## Migration strategy

1. Keep reading existing `providers.json` exactly as today.
2. Add TOML catalog read path for built-in definitions only.
3. Treat `providers.json` as user preference state, not catalog state.
4. If a provider exists in `providers.json` but no longer exists in catalog:
   - preserve it if it is a user-defined OpenAI-compatible config
   - ignore orphaned built-in preferences with a diagnostic
5. Never rewrite `providers.json` solely because catalog data changed.
6. Provide a `tau providers` diagnostic section showing:
   - source: built-in TOML / user TOML / providers.json preference
   - credential source
   - dynamic model status

## Validation rules

Provider-level validation:

- unique provider names
- supported provider kind
- non-empty display name
- valid base URL
- valid env var name unless `requires_credentials=false`
- `default_model in models`, except dynamic providers may have empty model/default
- context windows are positive integers
- timeout is positive
- retries are non-negative

Thinking validation:

- levels must be normalized Tau levels
- default must be in levels
- thinking models must be listed in models unless dynamic
- model override levels must be normalized

LM Studio-specific validation:

- `credential_name` empty/null
- dynamic models true
- timeout small enough for local discovery
- force chat completions true
- omit authorization header true

Packaging validation:

- `data/catalog.toml` included in sdist
- `uvx --from dist/tau_prime-<version>.tar.gz tau --version` still works
- `tau providers` can load catalog from installed artifact

## Rollback plan

If TOML catalog loading causes regressions:

1. Environment variable or feature flag disables TOML loader.
2. Runtime falls back to in-code `BUILTIN_PROVIDER_CATALOG`.
3. User `catalog.toml` is ignored with warning.
4. No migration should mutate `providers.json`, so rollback is non-destructive.

## What not to adopt yet

- Wholesale upstream `catalog.toml` replacement.
- Google and Mistral provider kinds/API implementations.
- Upstream provider auth abstraction unless it is mapped cleanly to Tau Prime's credential store.
- Full multimodal model capability routing until vision/read-image support is separately designed.
- Cost/pricing UI until there is a user-facing feature that consumes it.
- Data-driven theme/sidebar changes as part of catalog work.

## Recommended next implementation after current simple fixes

1. Add `catalog_loader.py` with TOML parsing and validation for a Tau Prime schema subset.
2. Add `data/catalog.toml` mirroring the current Tau Prime in-code catalog.
3. Add tests proving mirror parity for critical fields:
   - OpenAI GPT-5.6
   - OpenAI Codex no bare GPT-5.6
   - Anthropic Claude Opus 5 adaptive/disabled thinking
   - LM Studio credential-free dynamic config
   - NVIDIA NIM entry
4. Keep runtime on in-code catalog for one release.
5. In a later release, switch runtime to TOML with in-code fallback.

## Status

This document is analysis/proposal only. It intentionally does not change catalog runtime architecture.
