# Tau Prime extensions

Tau Prime supports a local Python extension seam inspired by upstream Tau/Pi but constrained for mobile safety.

## Discovery

Extensions are Python files with `setup(tau)` loaded from user and project `.tau/extensions` / `.agents/extensions` directories. Loading is best-effort; failures become diagnostics.

## Supported API

Current API includes:

- `register_tool`
- `register_command`
- `register_prompt_guideline`
- `register_input_hook`
- `on_agent_event`
- `on_lifecycle`
- `on_tool_call`
- `on_tool_result`
- `register_message_renderer`
- `register_tool_call_renderer`
- `register_tool_result_renderer`

## Event protocol

Extensions receive legacy Tau agent events plus Pi-shaped `message_update` events. Assistant sub-events include text/thinking start/delta/end, tool-call start/delta/end, done, and error.

## Safety boundaries

- Extension failures must not crash session startup or rendering.
- Tool and renderer hooks are isolation boundaries.
- Extension UI component hosting, main views, and pre-dispatch key interceptors are deferred until mobile/a-Shell review.
- Do not let extension APIs bypass macOS sandbox assumptions.

## Documentation

Repository docs live in `docs/extensions.md`; this bundled self-knowledge is only the compact in-prompt reference.
