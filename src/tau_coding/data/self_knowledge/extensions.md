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

## Portable web runtime

`tau_extensions` also provides manifest discovery and resolution plus typed services for storage, background tasks, assets, commands, tools, routes, events, declarative views/actions, file renderers, annotations, sandboxed widgets, and trusted frontend modules. Tau Web exposes their HTTP and browser adapters.

The stock web server starts with an empty extension directory. An embedding host must choose discovery roots, resolve policy and approvals, load code, and register service bundles. Workspace extensions cannot request trusted frontend access.

## Safety boundaries

- Extension failures must not crash session startup or rendering.
- Tool and renderer hooks are isolation boundaries.
- Sandboxed widgets use an opaque-origin iframe and a narrow bridge.
- Trusted frontend modules are limited to built-in and administrator-installed extensions and run with same-origin page privileges.
- Do not let extension APIs bypass macOS sandbox assumptions.

## Documentation

Repository docs live in `docs/extensions.md`; this bundled self-knowledge is only the compact in-prompt reference.
