# Hugging Face Tau adoption inventory

Captured on 2026-08-07 from `origin/main` at `0d02472ba724e2662a9dc2e62db9a40869438e8b` against Tau Prime adoption base `5a2f915ed0320c1b89ffaf03de81a9742f60b7ea`.

## Scope and method

The histories have diverged by 220 upstream commits. The complete commit index is included below so future reviews do not silently omit upstream work. Detailed compatibility analysis is intentionally limited to behavior requested for this adoption; unrelated branding, installer, website, release, CLI-protocol, and upstream architecture changes remain visible in the index but are rejected as a group unless separately approved.

Direct cherry-picks are not the default. Tau Prime preserves its Python provider configuration, `CodingSession`, SQLite-only live store, TUI/print behavior, web APIs, sandboxing, a-Shell compatibility, extension seams, and custom packaging backend.

## Selected compatibility matrix

| Order | Upstream | Behavior | Classification | Tau Prime treatment |
| ---: | --- | --- | --- | --- |
| 1 | `809e0e6` | transient Anthropic stream retries | Manual port required | Adapt retry classification/backoff to Tau Prime's Anthropic provider; preserve cancellation and bounded delays. |
| 2 | `3583456` | tool history across provider switches | Manual port required | Normalize at provider adapters/session projection; do not replace `tau_agent/loop.py` or SQLite recovery. |
| 3 | `5bf70e5` | Anthropic one-hour cache-write billing | Manual port required | Extend Tau Prime usage/pricing records and backward-compatible SQLite projections. |
| 4 | `1401fcd` | OpenAI prompt-cache affinity | Manual port required | Carry stable per-session affinity through current provider config/runtime seams only. |
| 5 | `ee3d57f` | resolved Hugging Face response provider | Dependency for sticky routing | Add provider-neutral resolved metadata before persistence. |
| 6 | `ea84782` | per-session Hugging Face sticky routing | Manual port required; depends on `ee3d57f` | Persist through Tau Prime session metadata/SQLite; retain custom-provider behavior and fallback. |
| 7 | `a8b155a` | Kimi K3 reasoning levels | Manual port required | Map low/high/max through Tau Prime thinking normalization and catalog. |
| 8 | `135b4b0` | cache analytics in HTML exports | Manual port required | Adapt to the existing Tau Prime exporter; do not add obsolete upstream statistics modules. |
| 9 | `24a26e0` | export cache timestamps/CSS fixes | Manual port required; depends on `135b4b0` | Apply after cache records and analytics are represented by Tau Prime. |
| 10 | `0d02472` | light-theme Markdown accents | Manual port required | Apply compatible theme tokens to active TUI/web theme systems and verify contrast. |
| — | `4ffef3e` | clean explicit bad-model errors | Already present | Covered by Tau Prime CLI/TUI regression tests; no port. |
| — | remaining 209 commits | upstream product/history changes | Rejected for this adoption | Includes architecture, branding, installer/site, release, and unrelated feature work; reassess individually if requested. |

## Dependency and changed-path record

The parent shown for each commit records its immediate upstream dependency. Paths are the exact files touched upstream; test and documentation files are included rather than inferred.

## 1401fcd Improve OpenAI prompt-cache affinity (#549)
parent da0e9213e9572563f2a1afeeba27640c62cc78c6
- dev-notes/prompt-caching.md
- src/tau_agent/harness.py
- src/tau_agent/loop.py
- src/tau_agent/provider.py
- src/tau_ai/anthropic.py
- src/tau_ai/fake.py
- src/tau_ai/google.py
- src/tau_ai/mistral.py
- src/tau_ai/openai_cache.py
- src/tau_ai/openai_codex.py
- src/tau_ai/openai_compatible.py
- src/tau_coding/provider_config.py
- src/tau_coding/session.py
- src/tau_coding/tui/app.py
- tests/test_agent_harness.py
- tests/test_coding_session.py
- tests/test_provider_runtime.py
- tests/test_tau_ai.py
- website/content/guides/providers-and-models.md
- website/content/reference/configuration.md
## 5bf70e5 Bill Anthropic 1-hour cache writes at their own rate (#553)
parent cc5c4916b6a9de141ff390c5c367747bb1cef356
- src/tau_coding/catalog_loader.py
- src/tau_coding/data/catalog.toml
- src/tau_coding/provider_config.py
- src/tau_coding/session_stats.py
- tests/test_provider_catalog.py
- tests/test_provider_config.py
- tests/test_session_stats.py
- website/content/reference/configuration.md
## 809e0e6 Retry transient Anthropic stream errors (#556)
parent 5bf70e58e753bbc77f2561bc23d9d06918e4827e
- dev-notes/anthropic-stream-error-recovery.md
- dev-notes/architecture/provider-retries.md
- src/tau_ai/anthropic.py
- tests/test_tau_ai.py
- website/content/reference/configuration.md
## 3583456 Fix tool history across provider switches
parent a8b155a48a9494c27b635395fcdf9b4d69e79082
- dev-notes/portable-tool-call-ids.md
- src/tau_ai/anthropic.py
- src/tau_ai/google.py
- src/tau_ai/mistral.py
- src/tau_ai/openai_compatible.py
- src/tau_ai/tool_call_ids.py
- tests/test_cross_provider_history.py
- website/content/guides/providers-and-models.md
## ee3d57f Expose resolved Hugging Face response provider (#562)
parent 809e0e68ab9e1f7d54631420fcfbb3b35c69ed42
- dev-notes/hugging-face-response-provider-metadata.md
- src/tau_agent/messages.py
- src/tau_ai/_provider_events.py
- src/tau_ai/env.py
- src/tau_ai/openai_compatible.py
- src/tau_ai/stream.py
- src/tau_coding/provider_config.py
- tests/test_agent_types.py
- tests/test_provider_config.py
- tests/test_tau_ai.py
- website/content/internals/agent-loop.md
## ea84782 Pin Hugging Face provider routing per session (#561)
parent 3583456ef734f56f3a5b3e66761769380b81b700
- .gitignore
- dev-notes/hugging-face-sticky-routing.md
- src/tau_ai/env.py
- src/tau_ai/openai_compatible.py
- src/tau_coding/cli.py
- src/tau_coding/commands.py
- src/tau_coding/data/release-notes/releases.json
- src/tau_coding/provider_config.py
- src/tau_coding/provider_runtime.py
- src/tau_coding/session.py
- src/tau_coding/session_export.py
- src/tau_coding/session_manager.py
- src/tau_coding/session_usage.py
- src/tau_coding/tui/app.py
- tests/test_coding_session.py
- tests/test_commands.py
- tests/test_provider_config.py
- tests/test_provider_runtime.py
- tests/test_session_manager.py
- tests/test_tau_ai.py
- tests/test_tui_app.py
- website/content/guides/providers-and-models.md
- website/content/reference/configuration.md
- website/public/landing.js
## a8b155a feat: update Kimi K3 reasoning effort levels (low, high, max) (#560)
parent 135b4b0acdb419d95fd191900e4e74c60e4a4318
- src/tau_coding/data/catalog.toml
- tests/test_provider_catalog.py
- tests/test_provider_config.py
- tests/test_provider_runtime.py
- website/content/guides/context.md
- website/content/guides/providers-and-models.md
## 135b4b0 Add reactive cache analytics tab to session HTML exports (#558)
parent ee3d57f5550f525caf46ef613f9cda40cafa8357
- dev-notes/session-export-usage-tab.md
- src/tau_coding/session_export.py
- src/tau_coding/session_usage.py
- tests/test_session_export.py
- tests/test_session_usage.py
- website/content/guides/sessions.md
## 24a26e0 Add request timestamps to cache tab tooltip and table, fix CSS issues (#564)
parent ea84782b9d9e0026b2b9924749ba6821d23709cf
- .gitignore
- src/tau_coding/session_export.py
- src/tau_coding/session_usage.py
## 0d02472 Improve light theme markdown accents
parent 9e62cc0af72d088523f93a7c20b2388f533ece74
- src/tau_coding/tui/themes/tau-light.json
- tests/test_tui_app.py
- website/content/guides/tui.md

## Validation contract for manual ports

Each port is a separate commit with upstream attribution. Run focused deterministic tests, Ruff on touched Python, MyPy on touched modules, and `git diff --check`. Integration validation must cover SQLite migration/recovery, restored sessions, provider changes, TUI/print, Tau Web API/SSE projections, extensions, packaging, and sandbox-safe imports.

## Complete upstream-only commit index

| # | Commit | Date | Subject |
| ---: | --- | --- | --- |
| 1 | `c1b5246` | 2026-07-03 | Add CODEOWNERS |
| 2 | `d6c6d42` | 2026-07-03 | Add CI workflow |
| 3 | `14987b2` | 2026-07-03 | Validate conflicting session flags in CLI |
| 4 | `3167601` | 2026-07-03 | feat(openai): route gpt-5.5/5.4/codex to the /v1/responses API (#183) |
| 5 | `cfa7886` | 2026-07-03 | Stabilize CI checks (#224) |
| 6 | `33b3213` | 2026-07-03 | Lower Python requirement to 3.12 (#220) |
| 7 | `a76e601` | 2026-07-03 | Render transcript messages as full-height role blocks (#214) |
| 8 | `6212bef` | 2026-07-03 | chore: release 0.1.1 (#230) |
| 9 | `0cb2ee8` | 2026-07-03 | Fix autocomplete suggestion window shrinking (#232) |
| 10 | `84570cc` | 2026-07-03 | chore: add contributor issue and PR templates (#234) |
| 11 | `3d67e6f` | 2026-07-03 | Keep session state on the active branch when persisting messages (#223) |
| 12 | `fea20b8` | 2026-07-03 | feat(tui): show session name in header (#245) |
| 13 | `2a1f8cf` | 2026-07-03 | Keep pre-branch context when branching with a summary (#227) |
| 14 | `1b161ca` | 2026-07-03 | Apply role foreground to streaming transcript messages (#243) |
| 15 | `c2b263c` | 2026-07-03 | Render assistant and thinking messages without a role block (#228) |
| 16 | `ea521fb` | 2026-07-03 | Revert "chore: add contributor issue and PR templates (#234)" (#235) |
| 17 | `a838075` | 2026-07-03 | docs: clarify PyPI release process (#231) |
| 18 | `06e83cf` | 2026-07-03 | fix: preserve active model during tree navigation (#249) |
| 19 | `1bf76a4` | 2026-07-04 | feat: show release notes after upgrade (#250) |
| 20 | `07b5ecc` | 2026-07-06 | fix: hide streaming code block scrollbars (#255) |
| 21 | `ba13e0a` | 2026-07-06 | Migrate docs site from Astro/Starlight to Hugo (#259) |
| 22 | `5d6e59d` | 2026-07-06 | Add Open Graph/Twitter card meta and a full favicon set (#262) |
| 23 | `47ff544` | 2026-07-06 | Optimize TUI transcript thinking toggle and markdown streaming (#256) |
| 24 | `f82d184` | 2026-07-06 | fix: keep resume provider model pairs atomic (#261) |
| 25 | `d9f0f85` | 2026-07-06 | fix: harden provider model selection (#257) |
| 26 | `3a6bd12` | 2026-07-06 | Optimize scoped provider model switching (#264) |
| 27 | `0d94c2d` | 2026-07-06 | fix(tui): avoid transcript redraw when switching scoped models (#266) |
| 28 | `4ffef3e` | 2026-07-06 | fix(cli): surface bad `--model` as a clean error in TUI and print mode (#267) |
| 29 | `7710de4` | 2026-07-06 | fix: persist interrupted tool repairs on resume (#269) |
| 30 | `a15ce4a` | 2026-07-06 | feat(tui): copy selected session modal text (#270) |
| 31 | `d99185f` | 2026-07-06 | fix(provider): load provider preferences config |
| 32 | `20343ea` | 2026-07-06 | fix(provider): allow catalog providers without credentials |
| 33 | `65b0671` | 2026-07-03 | feat: add TOML provider catalog data file and loader |
| 34 | `a3bb97b` | 2026-07-03 | refactor: load builtin catalog from TOML, merge user catalog into settings |
| 35 | `4125965` | 2026-07-03 | docs: document config-driven provider catalog |
| 36 | `e3b9682` | 2026-07-03 | fix: tighten provider catalog validation and docs |
| 37 | `7af31e4` | 2026-07-06 | refactor: separate provider definitions from preferences |
| 38 | `01be62c` | 2026-07-06 | docs: explain catalog and provider preference split |
| 39 | `14bfc6a` | 2026-07-06 | feat: add custom provider login flow |
| 40 | `e9649bc` | 2026-07-06 | feat: remember thinking preferences per model |
| 41 | `0910204` | 2026-07-06 | feat: clarify custom provider login form |
| 42 | `1a101b2` | 2026-07-06 | style: compact login provider picker labels |
| 43 | `b22bead` | 2026-07-06 | fix: preserve session modal selection copy |
| 44 | `9d79fef` | 2026-07-06 | fix: optimistically render TUI prompt submits |
| 45 | `64f7f9a` | 2026-07-06 | style: format optimistic submit helper |
| 46 | `c180a08` | 2026-07-06 | feat: add Pi API provider catalog |
| 47 | `3d40d30` | 2026-07-07 | fix: map Hugging Face minimal reasoning to low |
| 48 | `3e8c602` | 2026-07-07 | fix: validate Pi API provider catalog |
| 49 | `c9dc845` | 2026-07-07 | docs: add provider catalog validation runbook |
| 50 | `1c9cee3` | 2026-07-07 | style: apply ruff formatting |
| 51 | `805a9ee` | 2026-07-07 | fix: skip optimistic render for slash prompts |
| 52 | `5b00d95` | 2026-07-07 | chore: prepare 0.1.3 release |
| 53 | `67c3406` | 2026-06-30 | chore: enable Dependabot weekly GitHub Actions bumps |
| 54 | `938aadf` | 2026-07-08 | fix(cli): force UTF-8 stdout/stderr to fix Windows crash on non-ASCII output |
| 55 | `ffbfc30` | 2026-07-08 | fix(cli): skip UTF-8 stream reconfiguration when already UTF-8 |
| 56 | `e695410` | 2026-07-07 | fix: stop scanning .agents root directories for skills, ignore bare .md files in .agents/skills/ |
| 57 | `62df872` | 2026-07-08 | fix(skills): unify skill discovery on the Agent Skills spec |
| 58 | `1b32145` | 2026-07-08 | style: apply ruff format |
| 59 | `a0b8cd6` | 2026-07-08 | fix(google): round-trip thoughtSignature on Gemini tool calls |
| 60 | `2315520` | 2026-07-08 | fix(google): strip unsupported JSON Schema keywords from tool params |
| 61 | `be86b36` | 2026-07-08 | fix(cli): read version from package metadata |
| 62 | `2ebe392` | 2026-07-07 | feat(tui): add sidebar_position setting to tui.json |
| 63 | `d41dc6f` | 2026-07-07 | fix: preserve sidebar_position when changing theme via TUI |
| 64 | `e6e55cd` | 2026-07-08 | chore(deps): bump the actions group with 4 updates |
| 65 | `dfcf738` | 2026-07-08 | fix(tui): keep completion height stable while typing |
| 66 | `3c9e1ed` | 2026-07-08 | fix(tui): compact large pasted prompts |
| 67 | `6ae772d` | 2026-07-08 | fix(tui): expand multiple pasted placeholders |
| 68 | `8469bd9` | 2026-07-03 | Implement auto session naming |
| 69 | `1f4d6bf` | 2026-07-08 | Fix deferred auto session naming indexing |
| 70 | `26e274f` | 2026-07-08 | Document auto session naming divergence |
| 71 | `a24593c` | 2026-07-08 | feat: add Claude Fable 5 and Sonnet 5 models |
| 72 | `5e3a7de` | 2026-07-08 | fix: support socks proxy environment URLs |
| 73 | `2f7cc56` | 2026-07-08 | docs: explain socks proxy support |
| 74 | `e3d50c1` | 2026-07-08 | docs: note socks proxy follow-up considerations |
| 75 | `b76cc95` | 2026-07-08 | fix: recall queued steering messages |
| 76 | `ddbebde` | 2026-07-08 | feat(tui): update terminal tab title |
| 77 | `eb9c48a` | 2026-07-08 | fix(tui): harden terminal title writes |
| 78 | `707be55` | 2026-07-08 | feat(tui): use tau mark in terminal title |
| 79 | `450eb4f` | 2026-07-08 | fix(tui): refresh tab title after auto naming |
| 80 | `6056923` | 2026-07-08 | chore: prepare 0.1.4 release |
| 81 | `79c8e56` | 2026-07-08 | docs: add llama.cpp quickstart |
| 82 | `3c13856` | 2026-07-08 | fix(session): walk session tree iteratively to prevent /tree crash on long sessions |
| 83 | `72d931e` | 2026-07-09 | fix(tui): block tree branching while agent runs |
| 84 | `db7e7b9` | 2026-07-09 | fix: unify TUI theme selection |
| 85 | `0290c55` | 2026-07-08 | fix: resolve release-notes crash by bundling releases.json inside the package |
| 86 | `bcf5e0b` | 2026-07-09 | feat: add NVIDIA NIM provider to catalog |
| 87 | `d80ba71` | 2026-07-09 | docs: document safe catalog model additions |
| 88 | `ff5e962` | 2026-07-09 | test: assert release notes are bundled in wheel |
| 89 | `87a43fe` | 2026-07-09 | feat(website): add GitHub stars, Hugging Face link, and icon-based navbar |
| 90 | `f8306b9` | 2026-07-09 | feat(website): handwritten section notes, move HF logo to brand lockup |
| 91 | `fd33c1f` | 2026-07-09 | feat(website): handwritten eyebrows, unlinked HF logo in navbar |
| 92 | `79003c7` | 2026-07-09 | feat(website): handwritten headings across the landing page |
| 93 | `51e30a5` | 2026-07-09 | style(website): lighten hero heading weight |
| 94 | `141a2c5` | 2026-07-09 | feat(website): add roadmap page, handwritten hero polish |
| 95 | `42e5ee6` | 2026-07-09 | copy(website): rename nav link to "Rant", clarify Why Tau eyebrow |
| 96 | `906af23` | 2026-07-09 | docs(website): link to pi.dev wherever Pi is mentioned |
| 97 | `358d40b` | 2026-07-09 | style(website): restore original serif font for homepage hero title |
| 98 | `cfc6ed1` | 2026-07-09 | fix: make test_coding_session pass on Windows and stop tests touching real ~/.tau (#326) |
| 99 | `1c9fdb1` | 2026-07-09 | feat(session-export): redesign session HTML export with minimal, icon-based UI |
| 100 | `d38a7a3` | 2026-07-09 | Add OpenAI GPT-5.6 models to catalog (#329) |
| 101 | `b344d3e` | 2026-07-09 | Prepare 0.1.5 release |
| 102 | `0cf037e` | 2026-07-13 | chore: update gitignore && update docs for version update |
| 103 | `0171982` | 2026-07-13 | fix(tui): require textual>=8.2.8 so CJK IME input works (#338) |
| 104 | `96f5c67` | 2026-07-13 | fix(anthropic): retry 5xx above 504 and 425 like other providers (#334) |
| 105 | `deb67f9` | 2026-07-13 | fix: never let a missing or malformed releases.json crash startup (#339) |
| 106 | `c99f51b` | 2026-07-13 | docs: add Google Analytics |
| 107 | `0be2da5` | 2026-07-13 | fix: pass unknown slash input through as prompts (#351) |
| 108 | `3b82fed` | 2026-07-13 | docs: fix stale docs URL and path in dev-notes README (#342) |
| 109 | `d6d0ea6` | 2026-07-13 | fix: ignore orphaned provider preferences (#353) |
| 110 | `ab5aa72` | 2026-07-15 | Add an extension system (#320) |
| 111 | `3fac2c5` | 2026-07-15 | Fix extension reload lifecycle ordering (#366) |
| 112 | `6d3b5ff` | 2026-07-15 | Add Kimi K2.7 coding models (#365) |
| 113 | `d0e7ccc` | 2026-07-15 | feat: add MiniMax-M3 to minimax and minimax-cn catalog (#363) |
| 114 | `c0b399c` | 2026-07-15 | feat: support tiered model pricing metadata (#367) |
| 115 | `8560771` | 2026-07-15 | docs: point stale repo references at huggingface/tau (#362) |
| 116 | `bc120db` | 2026-07-15 | chore: prepare 0.1.6 release (#369) |
| 117 | `de78746` | 2026-07-15 | feat: add OAuth provider parity and OpenCode login options (#372) |
| 118 | `6c14f83` | 2026-07-16 | fix: improve interactive login modal navigation |
| 119 | `fbe435e` | 2026-07-16 | style: format login navigation changes |
| 120 | `5f26666` | 2026-07-16 | feat: adopt Pi-compatible event and extension protocol (#375) |
| 121 | `c803a7b` | 2026-07-16 | fix: migrate null session usage costs |
| 122 | `5c2be1b` | 2026-07-16 | Add Pi-shaped extension turn metadata (#376) |
| 123 | `a2db487` | 2026-07-16 | docs: document the canonical event streams (#377) |
| 124 | `5a95074` | 2026-07-16 | feat: add Kimi K3 model support (#378) |
| 125 | `81de4f8` | 2026-07-16 | chore: prepare 0.2.0 release (#379) |
| 126 | `48afd91` | 2026-07-17 | feat: bundle Tau self-knowledge (#381) |
| 127 | `f7a6391` | 2026-07-17 | feat: persist thinking on Pi-compatible assistant event streams (#371) |
| 128 | `1b7db6f` | 2026-07-17 | Fix tests opening Anthropic OAuth browser (#384) |
| 129 | `6fe3cba` | 2026-07-18 | Coerce startup thinking level to a mode the model supports (#383) |
| 130 | `a4bebeb` | 2026-07-18 | fix: discover Codex context limits at runtime (#390) |
| 131 | `2027b8c` | 2026-07-18 | Fix tool-call labels in the session tree (#387) |
| 132 | `f025e1d` | 2026-07-18 | Fix light theme code block background (#392) |
| 133 | `fd327d0` | 2026-07-18 | Remove redundant tool-row spinner (#396) |
| 134 | `bbf3307` | 2026-07-18 | Fix provider error recovery and TUI reporting (#395) |
| 135 | `7b2793f` | 2026-07-18 | chore: prepare 0.2.1 release (#397) |
| 136 | `2ed4848` | 2026-07-18 | Add search field to the /resume session picker (#399) |
| 137 | `4d7c982` | 2026-07-18 | Optimize long TUI transcript rendering (#398) |
| 138 | `73f72f3` | 2026-07-18 | Improve TUI sidebar session insights (#400) |
| 139 | `ed0dde0` | 2026-07-18 | Make TUI themes data-driven with user and project discovery (#374) |
| 140 | `449c1e7` | 2026-07-18 | Release Tau 0.2.2 (#402) |
| 141 | `b2745d8` | 2026-07-18 | Fix picker highlight text contrast (#404) |
| 142 | `b74e0dd` | 2026-07-19 | Keep Tau self-knowledge out of user skills (#406) |
| 143 | `7f4be2c` | 2026-07-19 | Clarify TUI session and context token usage (#407) |
| 144 | `87dce35` | 2026-07-19 | fix: don't split session JSONL on Unicode line separators (#354) |
| 145 | `dd49d9d` | 2026-07-19 | Default the TUI sidebar to the right (#409) |
| 146 | `5d3fdbd` | 2026-07-20 | chore: prepare 0.2.3 release (#411) |
| 147 | `08e2bfd` | 2026-07-20 | Fix resume picker search to exclude workspace paths (#420) |
| 148 | `102482b` | 2026-07-20 | Fix custom prompt auto-naming order (#421) |
| 149 | `e3fc26d` | 2026-07-21 | Shorten home context paths in sidebar (#422) |
| 150 | `e5eb252` | 2026-07-21 | Style footer provider as metadata (#425) |
| 151 | `a21870a` | 2026-07-21 | chore(deps): bump the actions group across 1 directory with 2 updates (#419) |
| 152 | `0186d56` | 2026-07-21 | Add conda-forge install instructions (#418) |
| 153 | `77df01c` | 2026-07-21 | chore: align WireModel pydantic config and raise floor to >=2.11 (#412) |
| 154 | `6bf47e2` | 2026-07-21 | feat: expand Hugging Face model catalog (#428) |
| 155 | `1ca6348` | 2026-07-21 | feat: normalize file paths dropped into the TUI prompt (#408) |
| 156 | `1b74b23` | 2026-07-21 | fix(test_provider_config): isolate env and assert set equality for builtin providers (#414) |
| 157 | `e3b7d2d` | 2026-07-21 | test: resolve flaky login search focus assertion by separating concerns (#416) |
| 158 | `4cacca9` | 2026-07-22 | chore: prepare 0.2.4 release (#431) |
| 159 | `7b0acc1` | 2026-07-22 | fix(website): add solid reading surface to long-form pages (#437) |
| 160 | `27c5c56` | 2026-07-22 | feat: make Tau updates prominent and add update command (#430) |
| 161 | `1702ea9` | 2026-07-22 | feat: print resume hint after TUI exit (#441) |
| 162 | `15f659d` | 2026-07-22 | fix: surface and retry transient Codex in-stream errors (#442) |
| 163 | `88724a6` | 2026-07-22 | feat!: mirror Pi's non-interactive CLI flags (#440) |
| 164 | `3cd0032` | 2026-07-22 | Update website Open Graph image |
| 165 | `c057eb7` | 2026-07-22 | feat: add cross-platform Tau installers (#444) |
| 166 | `4f2aaea` | 2026-07-22 | feat: notify when background turns finish (#445) |
| 167 | `0c3ce72` | 2026-07-23 | fix: tolerate future user config options (#447) |
| 168 | `ae3d822` | 2026-07-23 | docs: update website roadmap |
| 169 | `0d751fb` | 2026-07-23 | feat: add searchable prompts picker (#455) |
| 170 | `b63bee5` | 2026-07-23 | Add searchable /skills picker (#456) |
| 171 | `b68de72` | 2026-07-23 | Add searchable tools reference modal (#457) |
| 172 | `199c961` | 2026-07-23 | Clear /skills input when picker is cancelled (#461) |
| 173 | `21d43c1` | 2026-07-23 | Limit dense content in the TUI sidebar (#450) |
| 174 | `edd4ccc` | 2026-07-23 | release: prepare 0.3.1 (#462) |
| 175 | `d20b853` | 2026-07-24 | Fix GPT-5.6 availability in Codex catalog (#469) |
| 176 | `6f3efe4` | 2026-07-24 | Release Tau 0.3.2 (#470) |
| 177 | `ff35f16` | 2026-07-24 | Color terminal-command prompt input like a running tool (#471) |
| 178 | `afbf2e9` | 2026-07-25 | Add Claude Opus 5 support (#475) |
| 179 | `d597a8a` | 2026-07-25 | Release Tau 0.3.3 (#476) |
| 180 | `ab30561` | 2026-07-27 | Send read-tool images to vision models (#479) |
| 181 | `4c24356` | 2026-07-27 | Fix multiline context for skill invocations (#485) |
| 182 | `7e1235a` | 2026-07-27 | Harden read-tool image processing (#483) |
| 183 | `b0eeeac` | 2026-07-27 | Release Tau 0.3.4 (#488) |
| 184 | `33dbea2` | 2026-07-27 | Improve HTML session export filters (#487) |
| 185 | `2e5dbe8` | 2026-07-28 | Expose print-mode session IDs to automation (#501) |
| 186 | `ada7090` | 2026-07-29 | Fix Windows uv tool update handoff (#490) |
| 187 | `b131083` | 2026-07-29 | Accept file drops while the terminal is unfocused (#505) |
| 188 | `b41e4b5` | 2026-07-29 | Show working state and finished notification for manual /compact (#504) |
| 189 | `bc4e27e` | 2026-07-31 | Fix Anthropic subscription login and OAuth token refresh (#498) |
| 190 | `54db34c` | 2026-07-31 | Update website version and Tau rant attribution |
| 191 | `6ce8416` | 2026-07-31 | Cache Anthropic prompts instead of re-billing every turn (#502) |
| 192 | `720a730` | 2026-07-31 | Release Tau 0.3.5 (#516) |
| 193 | `566ea9a` | 2026-08-03 | Fix shell commands cancelling active agent runs (#528) |
| 194 | `9528c81` | 2026-08-03 | Make provider catalog upgrades resilient (#521) |
| 195 | `e93f00e` | 2026-08-03 | fix: keep @ file references available in /skill argument text (#340) |
| 196 | `8e9ee4d` | 2026-08-03 | fix: enable @ file completion in custom prompts (#511) |
| 197 | `a5b8afa` | 2026-08-03 | Fix provider-anchored context recovery (#529) |
| 198 | `2d32996` | 2026-08-03 | Add system prompt CLI controls (#534) |
| 199 | `1d8567f` | 2026-08-03 | Load Tau-native system prompt files (#536) |
| 200 | `cc17943` | 2026-08-03 | Include live system prompt in HTML exports (#538) |
| 201 | `9fffc69` | 2026-08-03 | Release Tau 0.3.6 (#539) |
| 202 | `817d45a` | 2026-08-04 | Remove stale SYSTEM.md |
| 203 | `07ba493` | 2026-08-04 | docs: design project trust policy (#540) |
| 204 | `ebbf25c` | 2026-08-04 | Track OpenAI Responses cache writes (#543) |
| 205 | `53325d3` | 2026-08-04 | Show latest and session cache hit rates (#544) |
| 206 | `d1b9484` | 2026-08-04 | feat: enforce project input trust (#541) |
| 207 | `da0e921` | 2026-08-04 | fix: require explicit startup trust choice (#548) |
| 208 | `1401fcd` | 2026-08-05 | Improve OpenAI prompt-cache affinity (#549) |
| 209 | `cc5c491` | 2026-08-05 | Release Tau 0.3.7 (#551) |
| 210 | `5bf70e5` | 2026-08-05 | Bill Anthropic 1-hour cache writes at their own rate (#553) |
| 211 | `809e0e6` | 2026-08-06 | Retry transient Anthropic stream errors (#556) |
| 212 | `ee3d57f` | 2026-08-06 | Expose resolved Hugging Face response provider (#562) |
| 213 | `135b4b0` | 2026-08-06 | Add reactive cache analytics tab to session HTML exports (#558) |
| 214 | `a8b155a` | 2026-08-06 | feat: update Kimi K3 reasoning effort levels (low, high, max) (#560) |
| 215 | `3583456` | 2026-08-06 | Fix tool history across provider switches |
| 216 | `ea84782` | 2026-08-06 | Pin Hugging Face provider routing per session (#561) |
| 217 | `24a26e0` | 2026-08-06 | Add request timestamps to cache tab tooltip and table, fix CSS issues (#564) |
| 218 | `5970cba` | 2026-08-06 | Resolve .gitignore after stash pop |
| 219 | `9e62cc0` | 2026-08-06 | Prepare Tau 0.3.8 release (#565) |
| 220 | `0d02472` | 2026-08-07 | Improve light theme markdown accents |
