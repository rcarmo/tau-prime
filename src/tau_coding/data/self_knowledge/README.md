# Tau Prime bundled self-knowledge

This directory is Tau Prime's built-in reference layer for the agent. It is injected as system context with `builtin://tau-prime/...` paths and is not exposed as a user skill.

Use these notes when answering questions about Tau Prime itself or when modifying internals. They summarize fork invariants, subsystem boundaries, and feature decisions that should not be rediscovered from upstream Tau.

Topic map:

- `architecture.md` — package boundaries and where changes belong.
- `cli.md` — CLI, print/TUI/web modes, session flags, and sandbox startup.
- `tui.md` — mobile TUI behavior, transcript rendering, notifications, and prompt handling.
- `providers.md` — provider-specific behavior and model routing constraints.
- `models.md` — static/dynamic model metadata rules.
- `compaction.md` — adaptive and provider-native compaction design.
- `extensions.md` — supported extension API surface and deferred component hosting.
- `skills-and-resources.md` — AGENTS.md, skills, prompts, and resource discovery.
- `packaging-and-release.md` — tarball release flow and a-Shell install expectations.
- `fork-invariants.md` — concise list of behaviors to preserve.
