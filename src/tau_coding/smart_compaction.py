"""Bounded, injection-resistant source preparation for context compaction."""

from __future__ import annotations

from dataclasses import dataclass

from tau_agent.messages import AgentMessage, AssistantMessage, ToolResultMessage, UserMessage

DEFAULT_TOOL_RESULT_CHARS = 1_500
DEFAULT_MESSAGE_CHARS = 8_000
DEFAULT_PROMPT_CHARS = 60_000
MIN_KEEP_RECENT_TOKENS = 512
MAX_KEEP_RECENT_FRACTION = 0.50


@dataclass(frozen=True, slots=True)
class CompactionBudget:
    """Window-aware budgets for one local compaction pass."""

    threshold_tokens: int
    keep_recent_tokens: int
    summary_input_tokens: int


def compaction_budget(
    *,
    context_window_tokens: int,
    fixed_tokens: int,
    requested_keep_recent_tokens: int,
) -> CompactionBudget:
    """Return safe adaptive budgets that leave room for summary generation."""
    window = max(1, context_window_tokens)
    reserve = min(16_384, max(512, window // 5))
    threshold = max(1, window - reserve)
    available = max(1, threshold - max(0, fixed_tokens) - 1_024)
    keep_cap = max(MIN_KEEP_RECENT_TOKENS, int(window * MAX_KEEP_RECENT_FRACTION))
    keep_recent = min(max(1, requested_keep_recent_tokens), keep_cap, available)
    summary_input = max(512, min(int(window * 0.42), threshold - 512))
    return CompactionBudget(threshold, keep_recent, summary_input)


def serialize_compaction_source(
    messages: tuple[AgentMessage, ...],
    *,
    max_chars: int = DEFAULT_PROMPT_CHARS,
    tool_result_chars: int = DEFAULT_TOOL_RESULT_CHARS,
    message_chars: int = DEFAULT_MESSAGE_CHARS,
) -> str:
    """Serialize untrusted history within a hard budget and preserve both ends.

    Contents are XML-escaped so transcript text cannot close structural prompt
    sections. Oversized histories retain the beginning, recent tail, and an
    explicit omission marker; individual tool results are tightly bounded.
    """
    rendered = [
        _render_message(
            message,
            index=index,
            tool_result_chars=tool_result_chars,
            message_chars=message_chars,
        )
        for index, message in enumerate(messages, start=1)
    ]
    if not rendered:
        return "(no new messages)"
    joined = "\n".join(rendered)
    if len(joined) <= max_chars:
        return joined

    marker = "\n<omitted_source_events reason=prompt_budget />\n"
    available = max(0, max_chars - len(marker))
    head_budget = available // 3
    tail_budget = available - head_budget
    head = _whole_blocks_from_start(rendered, head_budget)
    tail = _whole_blocks_from_end(rendered[len(head) :], tail_budget)
    if not head and rendered:
        head = [rendered[0][:head_budget]] if head_budget else []
    if not tail and len(rendered) > len(head):
        tail = [rendered[-1][-tail_budget:]] if tail_budget else []
    return "\n".join([*head, marker.strip(), *tail])[:max_chars]


def _render_message(
    message: AgentMessage,
    *,
    index: int,
    tool_result_chars: int,
    message_chars: int,
) -> str:
    if isinstance(message, UserMessage):
        body = _bounded(message.content, message_chars)
        return f'<event index="{index}" role="user">\n{_escape(body)}\n</event>'
    if isinstance(message, AssistantMessage):
        lines = [_escape(_bounded(message.content, message_chars))] if message.content else []
        for call in message.tool_calls:
            arguments = {
                key: value
                for key, value in call.arguments.items()
                if key != "_raw_arguments"
            }
            rendered_arguments = _escape(_bounded(str(arguments), message_chars))
            lines.append(
                f'<tool_call name="{_escape(call.name)}">'
                f"{rendered_arguments}</tool_call>"
            )
        return f'<event index="{index}" role="assistant">\n' + "\n".join(lines) + "\n</event>"
    if isinstance(message, ToolResultMessage):
        body = _bounded(message.content, tool_result_chars)
        return (
            f'<event index="{index}" role="tool" name="{_escape(message.name)}" '
            f'ok="{str(message.ok).lower()}">\n{_escape(body)}\n</event>'
        )
    body = _escape(_bounded(str(message), message_chars))
    return f'<event index="{index}" role="unknown">{body}</event>'


def _whole_blocks_from_start(blocks: list[str], budget: int) -> list[str]:
    selected: list[str] = []
    used = 0
    for block in blocks:
        cost = len(block) + (1 if selected else 0)
        if used + cost > budget:
            break
        selected.append(block)
        used += cost
    return selected


def _whole_blocks_from_end(blocks: list[str], budget: int) -> list[str]:
    selected: list[str] = []
    used = 0
    for block in reversed(blocks):
        cost = len(block) + (1 if selected else 0)
        if used + cost > budget:
            break
        selected.append(block)
        used += cost
    selected.reverse()
    return selected


def _bounded(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    omitted = len(value) - limit
    return f"{value[: max(0, limit - 40)]}\n… [{omitted} source characters omitted]"


def _escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
