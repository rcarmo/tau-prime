"""Shared session-plan models, rendering, and tool support."""

from __future__ import annotations

import inspect
import logging
import re
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Literal, Protocol, cast
from xml.sax.saxutils import escape

from tau_agent.tools import AgentTool, AgentToolResult, ToolCancellationToken
from tau_agent.types import JSONValue

MAX_PLAN_ITEMS = 200
MAX_PLAN_STEP_CHARS = 280
MAX_PLAN_CONTEXT_CHARS = 4_000
MAX_PLAN_CONTEXT_ITEMS = 50

_MARKDOWN_ITEM_RE = re.compile(r"^\s*(?:[-*+])\s+\[\s*([ xX-])\s*\]\s*(.*?)\s*$")
_LOGGER = logging.getLogger(__name__)


type PlanStatus = Literal["pending", "in_progress", "completed"]


@dataclass(frozen=True, slots=True)
class PlanItem:
    """One checklist step in the shared session plan."""

    step: str
    status: PlanStatus = "pending"

    def __post_init__(self) -> None:
        step = self.step.strip()
        if not step:
            raise ValueError("Plan step must not be blank")
        if len(step) > MAX_PLAN_STEP_CHARS:
            raise ValueError(f"Plan step must be at most {MAX_PLAN_STEP_CHARS} characters")
        object.__setattr__(self, "step", step)
        object.__setattr__(self, "status", _normalize_status(self.status))


@dataclass(frozen=True, slots=True)
class PlanSnapshot:
    """Immutable snapshot of a session's shared plan state."""

    session_id: str
    items: tuple[PlanItem, ...] = ()
    revision: int = 0
    updated_at: str | None = None
    updated_by: str | None = None

    def __post_init__(self) -> None:
        session_id = self.session_id.strip()
        if not session_id:
            raise ValueError("Session id must not be blank")
        items = tuple(self.items)
        if len(items) > MAX_PLAN_ITEMS:
            raise ValueError(f"Plan must contain at most {MAX_PLAN_ITEMS} items")
        if not all(isinstance(item, PlanItem) for item in items):
            raise ValueError("Plan items must all be PlanItem instances")
        in_progress = sum(1 for item in items if item.status == "in_progress")
        if in_progress > 1:
            raise ValueError("Plan must contain at most one in-progress item")
        if self.revision < 0:
            raise ValueError("Plan revision must be at least 0")
        updated_by = self.updated_by.strip() if self.updated_by is not None else None
        object.__setattr__(self, "session_id", session_id)
        object.__setattr__(self, "items", items)
        object.__setattr__(self, "updated_by", updated_by or None)


type PlanChangeCallback = Callable[[PlanSnapshot], Awaitable[None] | None]


class PlanStore(Protocol):
    """Async persistence boundary for shared session plans."""

    async def get(self, session_id: str) -> PlanSnapshot | None:
        """Return the latest snapshot for ``session_id`` when one exists."""
        ...

    async def save(
        self,
        snapshot: PlanSnapshot,
        *,
        expected_revision: int | None,
    ) -> PlanSnapshot:
        """Persist ``snapshot`` when the expected revision is still current."""
        ...


class PlanConflictError(RuntimeError):
    """Raised when a plan update loses an optimistic-concurrency race."""

    def __init__(
        self,
        session_id: str,
        *,
        expected_revision: int | None,
        actual_revision: int | None,
    ) -> None:
        self.session_id = session_id
        self.expected_revision = expected_revision
        self.actual_revision = actual_revision
        super().__init__(
            f"Plan revision conflict for {session_id!r}: expected "
            f"{expected_revision!r}, actual {actual_revision!r}"
        )


def render_plan_markdown(items: Sequence[PlanItem]) -> str:
    """Render plan items as canonical markdown checklist lines."""

    return "\n".join(f"- [{_status_marker(item.status)}] {item.step}" for item in items)


def parse_plan_markdown(markdown: str) -> tuple[PlanItem, ...]:
    """Parse markdown checklist lines into canonical plan items."""

    if not isinstance(markdown, str):
        raise ValueError("markdown must be a string")
    items: list[PlanItem] = []
    for line_number, line in enumerate(markdown.splitlines(), start=1):
        if not line.strip():
            continue
        match = _MARKDOWN_ITEM_RE.match(line)
        if match is None:
            raise ValueError(
                "Invalid plan markdown at line "
                f"{line_number}: expected '- [ ] step', '- [-] step', or '- [x] step'"
            )
        items.append(PlanItem(step=match.group(2), status=_marker_status(match.group(1))))
    return tuple(items)


def plan_turn_context(snapshot: PlanSnapshot) -> str:
    """Return a bounded XML-like context block for the current shared plan."""

    intro = (
        f'<tau-session-plan revision="{snapshot.revision}">\n'
        "This session plan is shared mutable state across turns. Read the latest plan "
        "before mutating it, and keep it updated as progress changes.\n"
    )
    footer = "\n</tau-session-plan>"
    budget = MAX_PLAN_CONTEXT_CHARS - len(intro) - len(footer)
    if budget <= 0:
        return intro.rstrip("\n") + footer

    body_lines: list[str] = []
    if not snapshot.items:
        body_lines.append("(no plan items)")
    else:
        omitted = 0
        for index, item in enumerate(snapshot.items):
            if index >= MAX_PLAN_CONTEXT_ITEMS:
                omitted = len(snapshot.items) - index
                break
            line = f"- [{_status_marker(item.status)}] {escape(item.step)}"
            candidate = "\n".join([*body_lines, line]) if body_lines else line
            if len(candidate) > budget:
                omitted = len(snapshot.items) - index
                break
            body_lines.append(line)
        if omitted > 0:
            notice = f"[{omitted} more plan item(s) omitted]"
            candidate = "\n".join([*body_lines, notice]) if body_lines else notice
            while body_lines and len(candidate) > budget:
                body_lines.pop()
                candidate = "\n".join([*body_lines, notice]) if body_lines else notice
            if len(candidate) <= budget:
                body_lines.append(notice)
    body = "\n".join(body_lines)
    return intro + body + footer


def create_plan_tool(
    store: PlanStore,
    session_id: str,
    *,
    updated_by: str = "agent",
    on_change: PlanChangeCallback | None = None,
) -> AgentTool:
    """Create the core shared-plan tool for one session."""

    session_key = _require_non_empty_string(session_id, field="session_id")
    actor = _require_non_empty_string(updated_by, field="updated_by")

    async def execute(
        arguments: Mapping[str, JSONValue],
        signal: ToolCancellationToken | None = None,
    ) -> AgentToolResult:
        del signal
        action = _require_action(arguments)
        current = await store.get(session_key)
        snapshot = current or PlanSnapshot(session_id=session_key)

        if action == "read":
            return _result(snapshot)

        provided_expected_revision = _optional_revision(arguments, "expected_revision")
        if (
            provided_expected_revision is not None
            and provided_expected_revision != snapshot.revision
        ):
            raise PlanConflictError(
                session_key,
                expected_revision=provided_expected_revision,
                actual_revision=snapshot.revision,
            )
        expected_revision = (
            snapshot.revision
            if provided_expected_revision is None
            else provided_expected_revision
        )

        match action:
            case "update":
                items = _structured_plan_items(arguments)
            case "write":
                items = parse_plan_markdown(_require_string(arguments, "markdown"))
            case "patch":
                items = _apply_patches(
                    snapshot.items,
                    _require_object_list(arguments, "patches"),
                )
            case "edit":
                items = _apply_markdown_edits(
                    render_plan_markdown(snapshot.items),
                    _require_object_list(arguments, "edits"),
                )
            case _:
                raise ValueError(f"Unsupported plan action: {action}")

        candidate = PlanSnapshot(
            session_id=session_key,
            items=items,
            revision=snapshot.revision,
            updated_at=snapshot.updated_at,
            updated_by=actor,
        )
        saved = await store.save(candidate, expected_revision=expected_revision)
        if on_change is not None:
            try:
                callback_result = on_change(saved)
                if inspect.isawaitable(callback_result):
                    await cast(Awaitable[object], callback_result)
            except Exception:
                _LOGGER.exception(
                    "Plan change callback failed after revision %s was saved",
                    saved.revision,
                )
        return _result(saved)

    return AgentTool(
        name="plan",
        description=(
            "Read or update the shared session plan using structured items, canonical "
            "markdown checklists, batch patches, or exact markdown edits."
        ),
        input_schema=_plan_input_schema(),
        executor=execute,
        prompt_snippet="Read or update the shared session plan",
        prompt_guidelines=(
            "Treat the plan as shared mutable state; read it before relying on it and "
            "update it after meaningful progress.",
            "Keep plan steps concise and concrete, and maintain at most one "
            "in-progress item.",
        ),
    )


def _plan_input_schema() -> dict[str, JSONValue]:
    return {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["read", "update", "write", "patch", "edit"],
                "description": "Plan action to perform",
            },
            "expected_revision": {
                "anyOf": [{"type": "integer"}, {"type": "null"}],
                "description": (
                    "Optional optimistic-concurrency revision; omit or null to use "
                    "the latest revision read by the tool"
                ),
            },
            "plan": {
                "description": (
                    "Structured plan for action=update; either {items:[...]} or a "
                    "list of {step,status} objects"
                ),
            },
            "markdown": {
                "type": "string",
                "description": "Markdown checklist for action=write",
            },
            "patches": {
                "type": "array",
                "description": "Patch operations for action=patch",
                "items": {"type": "object"},
            },
            "edits": {
                "type": "array",
                "description": "Exact markdown edit operations for action=edit",
                "items": {"type": "object"},
            },
        },
        "required": ["action"],
        "additionalProperties": False,
    }


def _result(snapshot: PlanSnapshot) -> AgentToolResult:
    return AgentToolResult(
        tool_call_id="",
        name="plan",
        ok=True,
        content=render_plan_markdown(snapshot.items),
        data={
            "session_id": snapshot.session_id,
            "revision": snapshot.revision,
            "plan": {
                "items": [_item_data(item) for item in snapshot.items],
                "updated_at": snapshot.updated_at,
                "updated_by": snapshot.updated_by,
            },
        },
    )


def _item_data(item: PlanItem) -> dict[str, JSONValue]:
    return {"step": item.step, "status": item.status}


def _require_action(arguments: Mapping[str, JSONValue]) -> str:
    action = _require_string(arguments, "action").strip().lower()
    if action not in {"read", "update", "write", "patch", "edit"}:
        raise ValueError("action must be one of: read, update, write, patch, edit")
    return action


def _require_string(arguments: Mapping[str, JSONValue], name: str) -> str:
    value = arguments.get(name)
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    return value


def _require_non_empty_string(value: str, *, field: str) -> str:
    selected = value.strip()
    if not selected:
        raise ValueError(f"{field} must not be blank")
    return selected


def _optional_revision(arguments: Mapping[str, JSONValue], name: str) -> int | None:
    value = arguments.get(name)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer or null")
    if value < 0:
        raise ValueError(f"{name} must be at least 0")
    return value


def _structured_plan_items(arguments: Mapping[str, JSONValue]) -> tuple[PlanItem, ...]:
    raw_plan = arguments.get("plan")
    item_field_prefix = "plan"
    raw_items: list[JSONValue]
    if isinstance(raw_plan, list):
        raw_items = raw_plan
    elif isinstance(raw_plan, dict):
        items_value = raw_plan.get("items")
        if not isinstance(items_value, list):
            raise ValueError("plan.items must be a list")
        raw_items = items_value
        item_field_prefix = "plan.items"
    else:
        raise ValueError("plan must be a list or an object with an items list")
    return tuple(
        _plan_item_from_value(item, field=f"{item_field_prefix}[{index}]")
        for index, item in enumerate(raw_items)
    )


def _plan_item_from_value(value: JSONValue, *, field: str) -> PlanItem:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    step = value.get("step")
    if not isinstance(step, str):
        raise ValueError(f"{field}.step must be a string")
    raw_status = value.get("status", "pending")
    if not isinstance(raw_status, str):
        raise ValueError(f"{field}.status must be a string")
    return PlanItem(step=step, status=_normalize_status(raw_status))


def _require_object_list(
    arguments: Mapping[str, JSONValue],
    name: str,
) -> list[Mapping[str, JSONValue]]:
    value = arguments.get(name)
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    objects: list[Mapping[str, JSONValue]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"{name}[{index}] must be an object")
        objects.append(item)
    return objects


def _apply_patches(
    items: Sequence[PlanItem],
    patches: Sequence[Mapping[str, JSONValue]],
) -> tuple[PlanItem, ...]:
    mutable = list(items)
    for index, patch in enumerate(patches):
        normalized = _operation(patch, field=f"patches[{index}]")
        match normalized:
            case "add":
                step = _mapping_string(patch, "step", field=f"patches[{index}].step")
                raw_status = patch.get("status", "pending")
                if not isinstance(raw_status, str):
                    raise ValueError(f"patches[{index}].status must be a string")
                item = PlanItem(step=step, status=_normalize_status(raw_status))
                position, target_patch = _add_position(patch, patch_index=index)
                mutable = _patch_add(
                    mutable,
                    item,
                    position,
                    target_patch,
                    patch_index=index,
                )
            case "update":
                target = _resolve_target(mutable, patch, patch_index=index)
                current = mutable[target]
                step_value = patch.get("step", current.step)
                if not isinstance(step_value, str):
                    raise ValueError(f"patches[{index}].step must be a string")
                raw_status = patch.get("status", current.status)
                if not isinstance(raw_status, str):
                    raise ValueError(f"patches[{index}].status must be a string")
                mutable[target] = PlanItem(
                    step=step_value,
                    status=_normalize_status(raw_status),
                )
            case "remove":
                target = _resolve_target(mutable, patch, patch_index=index)
                del mutable[target]
            case _:
                raise ValueError(
                    f"patches[{index}].operation must be add, update, or remove"
                )
    return tuple(mutable)


def _add_position(
    patch: Mapping[str, JSONValue],
    *,
    patch_index: int,
) -> tuple[str, Mapping[str, JSONValue]]:
    before = patch.get("before")
    after = patch.get("after")
    if before is not None and after is not None:
        raise ValueError(f"patches[{patch_index}] cannot specify both before and after")
    if before is not None or after is not None:
        anchor = before if before is not None else after
        if not isinstance(anchor, str):
            field = "before" if before is not None else "after"
            raise ValueError(f"patches[{patch_index}].{field} must be a string")
        target = dict(patch)
        target["match"] = anchor
        return ("before" if before is not None else "after"), target
    position = patch.get("position", "end")
    if not isinstance(position, str):
        raise ValueError(f"patches[{patch_index}].position must be a string")
    return position.strip().lower(), patch


def _patch_add(
    items: list[PlanItem],
    item: PlanItem,
    position: str,
    patch: Mapping[str, JSONValue],
    *,
    patch_index: int,
) -> list[PlanItem]:
    match position:
        case "start":
            return [item, *items]
        case "end":
            return [*items, item]
        case "before":
            target = _resolve_target(items, patch, patch_index=patch_index)
            return [*items[:target], item, *items[target:]]
        case "after":
            target = _resolve_target(items, patch, patch_index=patch_index)
            return [*items[: target + 1], item, *items[target + 1 :]]
        case _:
            raise ValueError(
                f"patches[{patch_index}].position must be start, end, before, or after"
            )


def _resolve_target(
    items: Sequence[PlanItem],
    patch: Mapping[str, JSONValue],
    *,
    patch_index: int,
) -> int:
    raw_index = patch.get("index")
    raw_match = patch.get("match")
    has_index = raw_index is not None
    has_match = raw_match is not None
    if has_index == has_match:
        raise ValueError(
            f"patches[{patch_index}] must specify exactly one of index or match"
        )
    if has_index:
        if isinstance(raw_index, bool) or not isinstance(raw_index, int):
            raise ValueError(f"patches[{patch_index}].index must be a 1-based integer")
        if raw_index < 1 or raw_index > len(items):
            raise ValueError(
                f"patches[{patch_index}].index must be between 1 and {len(items)}"
            )
        return raw_index - 1
    if not isinstance(raw_match, str):
        raise ValueError(f"patches[{patch_index}].match must be a string")
    needle = raw_match.strip()
    if not needle:
        raise ValueError(f"patches[{patch_index}].match must not be blank")
    matches = [index for index, item in enumerate(items) if needle in item.step]
    if not matches:
        raise ValueError(f"patches[{patch_index}].match did not match any plan item")
    if len(matches) > 1:
        raise ValueError(
            f"patches[{patch_index}].match must identify exactly one plan item"
        )
    return matches[0]


def _apply_markdown_edits(
    markdown: str,
    edits: Sequence[Mapping[str, JSONValue]],
) -> tuple[PlanItem, ...]:
    current = markdown
    for index, edit in enumerate(edits):
        normalized = _operation(
            edit,
            field=f"edits[{index}]",
            default="replace" if "oldText" in edit and "newText" in edit else None,
        )
        match normalized:
            case "replace":
                old_text = _mapping_string(
                    edit,
                    "oldText",
                    field=f"edits[{index}].oldText",
                )
                new_text = _mapping_string(
                    edit,
                    "newText",
                    field=f"edits[{index}].newText",
                )
                current = _replace_unique(
                    current,
                    old_text,
                    new_text,
                    label=f"edits[{index}]",
                )
            case "delete":
                old_text = _mapping_string(
                    edit,
                    "oldText",
                    field=f"edits[{index}].oldText",
                )
                current = _replace_unique(current, old_text, "", label=f"edits[{index}]")
            case "insert_before":
                old_text = _mapping_string_alias(
                    edit,
                    ("anchorText", "oldText"),
                    field=f"edits[{index}].anchorText",
                )
                new_text = _mapping_string_alias(
                    edit,
                    ("text", "newText"),
                    field=f"edits[{index}].text",
                )
                current = _insert_relative(
                    current,
                    old_text,
                    new_text,
                    before=True,
                    label=f"edits[{index}]",
                )
            case "insert_after":
                old_text = _mapping_string_alias(
                    edit,
                    ("anchorText", "oldText"),
                    field=f"edits[{index}].anchorText",
                )
                new_text = _mapping_string_alias(
                    edit,
                    ("text", "newText"),
                    field=f"edits[{index}].text",
                )
                current = _insert_relative(
                    current,
                    old_text,
                    new_text,
                    before=False,
                    label=f"edits[{index}]",
                )
            case "append":
                new_text = _mapping_string_alias(
                    edit,
                    ("text", "newText"),
                    field=f"edits[{index}].text",
                )
                current = current + new_text
            case "prepend":
                new_text = _mapping_string_alias(
                    edit,
                    ("text", "newText"),
                    field=f"edits[{index}].text",
                )
                current = new_text + current
            case _:
                raise ValueError(
                    f"edits[{index}].operation must be replace, delete, insert_before, "
                    "insert_after, append, or prepend"
                )
    return parse_plan_markdown(current)


def _replace_unique(text: str, old: str, new: str, *, label: str) -> str:
    start = _unique_span(text, old, label=label)
    return text[: start[0]] + new + text[start[1] :]


def _insert_relative(
    text: str,
    anchor: str,
    insertion: str,
    *,
    before: bool,
    label: str,
) -> str:
    start, end = _unique_span(text, anchor, label=label)
    offset = start if before else end
    return text[:offset] + insertion + text[offset:]


def _unique_span(text: str, needle: str, *, label: str) -> tuple[int, int]:
    if not needle:
        raise ValueError(f"{label} text must not be blank")
    first = text.find(needle)
    if first < 0:
        raise ValueError(f"{label} text was not found exactly once")
    second = text.find(needle, first + 1)
    if second >= 0:
        raise ValueError(f"{label} text must occur exactly once")
    return first, first + len(needle)


def _operation(
    mapping: Mapping[str, JSONValue],
    *,
    field: str,
    default: str | None = None,
) -> str:
    value = mapping.get("operation", mapping.get("op", default))
    if not isinstance(value, str):
        raise ValueError(f"{field}.operation must be a string")
    return value.strip().lower()


def _mapping_string_alias(
    mapping: Mapping[str, JSONValue],
    names: Sequence[str],
    *,
    field: str,
) -> str:
    for name in names:
        value = mapping.get(name)
        if isinstance(value, str):
            return value
    raise ValueError(f"{field} must be a string")


def _mapping_string(mapping: Mapping[str, JSONValue], name: str, *, field: str) -> str:
    value = mapping.get(name)
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def _normalize_status(value: str) -> PlanStatus:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized == "pending":
        return "pending"
    if normalized == "in_progress":
        return "in_progress"
    if normalized == "completed":
        return "completed"
    raise ValueError("Plan status must be pending, in_progress, or completed")


def _status_marker(status: PlanStatus) -> str:
    if status == "pending":
        return " "
    if status == "in_progress":
        return "-"
    return "x"


def _marker_status(marker: str) -> PlanStatus:
    if marker == " ":
        return "pending"
    if marker == "-":
        return "in_progress"
    return "completed"


__all__ = [
    "MAX_PLAN_CONTEXT_CHARS",
    "MAX_PLAN_ITEMS",
    "MAX_PLAN_STEP_CHARS",
    "PlanConflictError",
    "PlanItem",
    "PlanSnapshot",
    "PlanStatus",
    "PlanStore",
    "create_plan_tool",
    "parse_plan_markdown",
    "plan_turn_context",
    "render_plan_markdown",
]
