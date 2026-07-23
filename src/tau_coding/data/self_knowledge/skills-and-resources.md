# Tau Prime skills and resources

Tau Prime loads user/project instructions and reusable resources into the coding session.

## Project context

`AGENTS.md` files are discovered from user roots and project roots. Project context is wrapped into the system prompt as project instructions.

## Skills

Skills are Markdown resources discovered from `.tau/skills`, `.agents/skills`, and compatible project-local locations. They are listed in the prompt when the read tool is available, but the agent should read the full skill file only when the task matches.

## Prompt templates

Prompt templates live under Tau and `.agents` prompt directories. Slash prompt expansion remains separate from ordinary slash commands.

## Bundled self-knowledge

Tau Prime self-knowledge is injected as built-in project context using `builtin://tau-prime/...` paths. It must not appear in the user skill list and must not shadow user skills.

## Resource diagnostics

Resource discovery should be best-effort. Bad resources produce diagnostics rather than preventing startup unless a caller explicitly requests strict behavior.
