# Tau Prime fork invariants

Preserve these unless Rui explicitly decides otherwise.

- Executable name remains `tau`.
- Distribution/project name remains `tau-prime`.
- a-Shell/iOS remains a first-class target.
- Shell behavior assumes POSIX `sh`, not Bash.
- The `sh` tool is the canonical shell tool; older `bash` naming may remain compatibility-only where present.
- LM Studio remains credential-free, forces chat completions, and sends no Authorization header.
- GitHub Copilot provider/model routing must remain provider-aware and preserve required headers.
- Copilot GPT 5.6 models use Responses routing.
- Codex's reserved `python` function name is mapped at the provider boundary.
- macOS sandboxing is default-on and fail-closed; `--no-sandbox` is the explicit bypass.
- Provider/model pairs must remain atomic on resume, scoped switching, and branch operations.
- Session storage is append-only JSONL; repairs/compactions append entries instead of rewriting history.
- Adaptive/provider-native compaction must fail closed for opaque native state.
- Release tarballs are the supported a-Shell install artifact.
