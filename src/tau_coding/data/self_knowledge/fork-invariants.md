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
- SQLite is the sole live durable session store; do not reintroduce per-project JSONL as authoritative runtime state.
- Session history remains an append-only entry tree; repairs, summaries, compactions, labels, and branch updates append durable entries instead of rewriting transcript history.
- Preserve the current SQLite invariants: WAL mode, foreign keys, and `json_valid(...)`-style constraints on structured JSON columns.
- JSONL remains import/export and legacy interchange only.
- Adaptive/provider-native compaction must fail closed for opaque native state.
- Release tarballs are the supported a-Shell install artifact.
