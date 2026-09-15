from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from tau_coding.plan import (
    MAX_PLAN_CONTEXT_CHARS,
    MAX_PLAN_CONTEXT_ITEMS,
    MAX_PLAN_ITEMS,
    PlanConflictError,
    PlanItem,
    PlanSnapshot,
    create_plan_tool,
    parse_plan_markdown,
    plan_turn_context,
    render_plan_markdown,
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@dataclass(slots=True)
class MemoryPlanStore:
    snapshots: dict[str, PlanSnapshot] = field(default_factory=dict)
    counter: int = 0

    async def get(self, session_id: str) -> PlanSnapshot | None:
        return self.snapshots.get(session_id)

    async def save(
        self,
        snapshot: PlanSnapshot,
        *,
        expected_revision: int | None,
    ) -> PlanSnapshot:
        current = self.snapshots.get(snapshot.session_id)
        actual_revision = current.revision if current is not None else None
        if actual_revision is None:
            if expected_revision not in (None, 0):
                raise PlanConflictError(
                    snapshot.session_id,
                    expected_revision=expected_revision,
                    actual_revision=None,
                )
            revision = 1
        else:
            if expected_revision != actual_revision:
                raise PlanConflictError(
                    snapshot.session_id,
                    expected_revision=expected_revision,
                    actual_revision=actual_revision,
                )
            revision = actual_revision + 1
        self.counter += 1
        saved = PlanSnapshot(
            session_id=snapshot.session_id,
            items=snapshot.items,
            revision=revision,
            updated_at=f"t{self.counter}",
            updated_by=snapshot.updated_by,
        )
        self.snapshots[snapshot.session_id] = saved
        return saved


def test_parse_and_render_plan_markdown_round_trip() -> None:
    markdown = "\n- [ ] first\n- [-] second\n- [X] third\n"

    parsed = parse_plan_markdown(markdown)

    assert parsed == (
        PlanItem(step="first", status="pending"),
        PlanItem(step="second", status="in_progress"),
        PlanItem(step="third", status="completed"),
    )
    assert render_plan_markdown(parsed) == "\n".join(
        ("- [ ] first", "- [-] second", "- [x] third")
    )


def test_plan_turn_context_escapes_and_truncates() -> None:
    items = (
        PlanItem(step="escape <tag> & text"),
        *tuple(PlanItem(step=f"step {index}") for index in range(MAX_PLAN_CONTEXT_ITEMS + 3)),
    )
    snapshot = PlanSnapshot(session_id="session", items=items, revision=7)

    context = plan_turn_context(snapshot)

    assert context.startswith('<tau-session-plan revision="7">\n')
    assert "- [ ] escape &lt;tag&gt; &amp; text" in context
    assert "- [ ] escape <tag> & text" not in context
    assert "[4 more plan item(s) omitted]" in context
    assert context.endswith("\n</tau-session-plan>")
    assert len(context) <= MAX_PLAN_CONTEXT_CHARS


@pytest.mark.anyio
async def test_plan_tool_read_update_write_and_callback_only_for_mutations() -> None:
    store = MemoryPlanStore()
    observed: list[PlanSnapshot] = []

    async def on_change(snapshot: PlanSnapshot) -> None:
        observed.append(snapshot)

    tool = create_plan_tool(store, "session-1", updated_by="assistant", on_change=on_change)

    empty = await tool.execute({"action": "read"})
    assert empty.content == ""
    assert empty.data == {
        "session_id": "session-1",
        "revision": 0,
        "plan": {"items": [], "updated_at": None, "updated_by": None},
    }
    assert observed == []

    updated = await tool.execute(
        {
            "action": "update",
            "plan": {
                "items": [
                    {"step": "inspect workspace", "status": "in progress"},
                    {"step": "ship tests", "status": "pending"},
                ]
            },
        }
    )
    assert updated.content == "- [-] inspect workspace\n- [ ] ship tests"
    assert updated.data is not None
    assert updated.data["revision"] == 1
    assert len(observed) == 1
    assert observed[0].items == parse_plan_markdown(updated.content)

    written = await tool.execute(
        {
            "action": "write",
            "expected_revision": 1,
            "markdown": "- [x] inspect workspace\n- [ ] ship tests",
        }
    )
    assert written.content == "- [x] inspect workspace\n- [ ] ship tests"
    assert written.data is not None
    assert written.data["revision"] == 2
    assert [snapshot.revision for snapshot in observed] == [1, 2]


@pytest.mark.anyio
async def test_plan_tool_keeps_saved_result_when_change_callback_fails() -> None:
    store = MemoryPlanStore()

    async def on_change(snapshot: PlanSnapshot) -> None:
        del snapshot
        raise RuntimeError("subscriber unavailable")

    tool = create_plan_tool(store, "session-callback", on_change=on_change)
    result = await tool.execute(
        {"action": "update", "plan": [{"step": "saved", "status": "pending"}]}
    )

    assert result.data is not None
    assert result.data["revision"] == 1
    assert (await store.get("session-callback")) is not None


@pytest.mark.anyio
async def test_plan_tool_patch_supports_positions_targets_update_and_remove() -> None:
    store = MemoryPlanStore()
    tool = create_plan_tool(store, "session-2")
    await tool.execute(
        {
            "action": "update",
            "plan": [
                {"step": "beta", "status": "pending"},
                {"step": "delta", "status": "pending"},
            ],
        }
    )

    patched = await tool.execute(
        {
            "action": "patch",
            "expected_revision": 1,
            "patches": [
                {"operation": "add", "step": "alpha", "position": "start"},
                {"op": "add", "step": "epsilon", "position": "end"},
                {"operation": "add", "step": "gamma", "before": "delta"},
                {"operation": "add", "step": "beta-2", "after": "beta"},
                {"op": "update", "match": "delta", "step": "omega", "status": "completed"},
                {"op": "remove", "index": 3},
            ],
        }
    )

    assert patched.content == "\n".join(
        (
            "- [ ] alpha",
            "- [ ] beta",
            "- [ ] gamma",
            "- [x] omega",
            "- [ ] epsilon",
        )
    )
    assert patched.data is not None
    assert patched.data["revision"] == 2


@pytest.mark.anyio
async def test_plan_tool_rejects_ambiguous_match_stale_revision_and_plan_limits() -> None:
    store = MemoryPlanStore()
    tool = create_plan_tool(store, "session-3")
    await tool.execute(
        {
            "action": "update",
            "plan": [
                {"step": "ship docs", "status": "pending"},
                {"step": "ship code", "status": "pending"},
            ],
        }
    )

    with pytest.raises(ValueError, match="must identify exactly one plan item"):
        await tool.execute(
            {
                "action": "patch",
                "patches": [{"op": "remove", "match": "ship"}],
            }
        )

    with pytest.raises(PlanConflictError, match="expected 0, actual 1"):
        await tool.execute(
            {
                "action": "write",
                "expected_revision": 0,
                "markdown": "- [ ] stale",
            }
        )

    with pytest.raises(ValueError, match="at most one in-progress item"):
        await tool.execute(
            {
                "action": "write",
                "expected_revision": 1,
                "markdown": "- [-] first\n- [-] second",
            }
        )

    with pytest.raises(ValueError, match=f"at most {MAX_PLAN_ITEMS} items"):
        await tool.execute(
            {
                "action": "update",
                "expected_revision": 1,
                "plan": [
                    {"step": f"step {index}", "status": "pending"}
                    for index in range(MAX_PLAN_ITEMS + 1)
                ],
            }
        )


@pytest.mark.anyio
async def test_plan_tool_edit_supports_all_edit_operations() -> None:
    store = MemoryPlanStore()
    tool = create_plan_tool(store, "session-4")
    await tool.execute(
        {
            "action": "write",
            "markdown": "- [ ] beta\n- [ ] drop\n- [x] delta",
        }
    )

    edited = await tool.execute(
        {
            "action": "edit",
            "expected_revision": 1,
            "edits": [
                {"operation": "prepend", "text": "- [ ] alpha\n"},
                {
                    "operation": "insert_after",
                    "anchorText": "- [ ] beta",
                    "text": "\n- [-] gamma",
                },
                {
                    "operation": "insert_before",
                    "anchorText": "- [x] delta",
                    "text": "- [ ] before-delta\n",
                },
                {"oldText": "- [x] delta", "newText": "- [ ] epsilon"},
                {"operation": "delete", "oldText": "- [ ] drop\n"},
                {"operation": "append", "text": "\n- [x] zeta"},
            ],
        }
    )

    assert edited.content == "\n".join(
        (
            "- [ ] alpha",
            "- [ ] beta",
            "- [-] gamma",
            "- [ ] before-delta",
            "- [ ] epsilon",
            "- [x] zeta",
        )
    )
    assert parse_plan_markdown(edited.content) == (
        PlanItem(step="alpha"),
        PlanItem(step="beta"),
        PlanItem(step="gamma", status="in_progress"),
        PlanItem(step="before-delta"),
        PlanItem(step="epsilon"),
        PlanItem(step="zeta", status="completed"),
    )
