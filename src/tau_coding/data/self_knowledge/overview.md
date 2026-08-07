# Tau Prime self-knowledge

Tau Prime is Rui Carmo's fork of Tau for constrained mobile and sandboxed desktop use. The executable remains `tau`, but the package and documentation use `tau-prime`.

## Core fork boundaries

- Preserve a-Shell/iOS behavior: POSIX `sh` assumptions, lightweight terminal handling, resize polling, and interrupt handling suitable for mobile terminals.
- Preserve default-on macOS sandboxing through `/usr/bin/sandbox-exec`; only `--no-sandbox` intentionally bypasses it.
- Preserve Tau Prime release packaging: GitHub release source tarballs, including `tau-prime.tar.gz` for a-Shell installation.
- Do not assume upstream Tau branding, hosted docs, website, PyPI workflow, or installer strategy applies unchanged.

## Startup and frontend state

- Bare `tau` must reach the TUI when no provider/model is configured; `/login` and `/model` are the onboarding path, and startup must not fabricate configuration.
- Tau Web is an optional aiohttp runtime with a committed TypeScript/Preact bundle over the shared SQLite store.
- Browser credential onboarding is not implemented yet; Tau Web currently uses credentials configured through the TUI/CLI.

## Validation expectations

When changing code, run focused tests for the touched subsystem and prefer the full suite before claiming completion. Do not claim actual macOS Seatbelt enforcement was tested unless a macOS host was used.
