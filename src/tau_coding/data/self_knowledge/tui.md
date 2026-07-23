# Tau Prime TUI

Tau Prime's TUI is tuned for a-Shell/mobile and narrow terminals.

## Mobile-oriented behavior

- Sidebar starts hidden by default and can be toggled with `Ctrl+B`.
- Terminal size is polled as a fallback when resize events are unreliable.
- Prompt focus and scrollback keybindings must remain usable on external keyboards and a-Shell.
- Avoid large remounts or layout churn during prompt edits and streaming.

## Transcript rendering

- The TUI consumes Pi-shaped `message_update` events as the primary assistant stream.
- Legacy Tau delta/end events are still emitted and used as fallback.
- Mounted transcript widgets are bounded for responsiveness; the full session history remains in state/storage.
- Thinking blocks are bounded/hidden unless the user toggles them.
- Tool result visibility is toggled with `Ctrl+O`.

## Notifications

Turn-finished notifications can be `off`, `bell`, or `desktop`. Desktop notifications use terminal OSC sequences where supported and are disabled in CI/dumb terminals.

## Prompt handling

Large pasted text is summarized as a placeholder in the prompt while preserving the full content for submission. Dropped/pasted existing file paths are normalized into prompt-friendly path text.

## Picker behavior

The resume picker supports search by title/model/session metadata but should avoid matching long workspace paths. Picker behavior must be checked on narrow screens before adopting upstream visual changes.
