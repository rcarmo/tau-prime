"""SQLite-backed plan-store adapter for the shared session plan tool."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

from tau_agent.types import JSONObject, JSONValue
from tau_coding.plan import (
    PlanConflictError,
    PlanItem,
    PlanSnapshot,
    PlanStatus,
    PlanStore,
    create_plan_tool,
    parse_plan_markdown,
    plan_turn_context,
    render_plan_markdown,
)
from tau_web.events import build_invalidation_envelope
from tau_web.sqlite.repositories import PlanRecord, PlanRepository, RevisionConflictError

if TYPE_CHECKING:
    from tau_agent.tools import AgentTool
    from tau_coding.coding_session_factory import (
        CodingSessionFactoryBinding,
        ExtraToolsFactory,
        TurnContextProvider,
        TurnContextProviderFactory,
    )
    from tau_web.sse import EventBroker

_PLAN_PAYLOAD_FORMAT = "tau.plan/v1"


def create_plan_factory_hooks(
    repository: PlanRepository,
    *,
    broker: EventBroker | None = None,
) -> tuple[ExtraToolsFactory, TurnContextProviderFactory]:
    """Create session-aware plan tool and fresh turn-context factory hooks."""
    store = SqlitePlanStore(repository)

    def extra_tools(binding: CodingSessionFactoryBinding) -> Sequence[AgentTool]:
        session_id = binding.session_id
        if session_id is None:
            return ()

        async def on_change(snapshot: PlanSnapshot) -> None:
            if broker is None:
                return
            await broker.publish(
                build_invalidation_envelope(
                    event_type="tau.plan.updated",
                    session_id=snapshot.session_id,
                    payload={"revision": snapshot.revision},
                )
            )

        return (create_plan_tool(store, session_id, on_change=on_change),)

    def context_provider(
        binding: CodingSessionFactoryBinding,
    ) -> TurnContextProvider | None:
        session_id = binding.session_id
        if session_id is None:
            return None

        async def current_context() -> str:
            snapshot = await store.get(session_id)
            return plan_turn_context(snapshot or PlanSnapshot(session_id=session_id))

        return current_context

    return extra_tools, context_provider


class SqlitePlanStore(PlanStore):
    """Persist shared session plans via the existing web plan repository."""

    def __init__(self, repository: PlanRepository) -> None:
        self._repository = repository

    async def get(self, session_id: str) -> PlanSnapshot | None:
        record = await self._repository.get(session_id)
        if record is None:
            return None
        items = _items_from_record(record)
        return PlanSnapshot(
            session_id=record.session_id,
            items=items,
            revision=record.revision,
            updated_at=record.updated_at,
            updated_by=record.updated_by,
        )

    async def save(
        self,
        snapshot: PlanSnapshot,
        *,
        expected_revision: int | None,
    ) -> PlanSnapshot:
        actor = snapshot.updated_by
        if actor is None:
            raise ValueError("updated_by must not be blank")
        try:
            record = await self._repository.save(
                snapshot.session_id,
                markdown=_encode_snapshot(snapshot),
                explanation=None,
                updated_by=actor,
                expected_revision=expected_revision,
            )
        except RevisionConflictError as exc:
            raise PlanConflictError(
                snapshot.session_id,
                expected_revision=exc.expected,
                actual_revision=exc.actual,
            ) from exc
        items = _items_from_record(record)
        return PlanSnapshot(
            session_id=record.session_id,
            items=items,
            revision=record.revision,
            updated_at=record.updated_at,
            updated_by=record.updated_by,
        )


def _encode_snapshot(snapshot: PlanSnapshot) -> str:
    payload: JSONObject = {
        "format": _PLAN_PAYLOAD_FORMAT,
        "items": [_item_payload(item) for item in snapshot.items],
        "markdown": render_plan_markdown(snapshot.items),
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _item_payload(item: PlanItem) -> JSONObject:
    return cast(JSONObject, {"step": item.step, "status": item.status})


def _items_from_record(record: PlanRecord) -> tuple[PlanItem, ...]:
    try:
        payload = json.loads(record.markdown)
    except json.JSONDecodeError:
        try:
            return parse_plan_markdown(record.markdown)
        except ValueError as exc:
            raise RuntimeError(
                f"Stored plan for session {record.session_id} is not valid markdown"
            ) from exc

    if isinstance(payload, dict):
        payload_format = payload.get("format")
        if payload_format is not None and payload_format != _PLAN_PAYLOAD_FORMAT:
            raise RuntimeError(
                f"Stored plan for session {record.session_id} has unsupported format "
                f"{payload_format!r}"
            )
        items_value = payload.get("items")
        if isinstance(items_value, list):
            return tuple(
                _item_from_value(item, index=index)
                for index, item in enumerate(items_value)
            )
        markdown_value = payload.get("markdown")
        if isinstance(markdown_value, str):
            return parse_plan_markdown(markdown_value)
    if isinstance(payload, str):
        return parse_plan_markdown(payload)
    raise RuntimeError(
        f"Stored plan for session {record.session_id} is not a valid plan payload"
    )


def _item_from_value(value: JSONValue, *, index: int) -> PlanItem:
    if not isinstance(value, dict):
        raise RuntimeError(f"Stored plan item {index} is not an object")
    step = value.get("step")
    status = value.get("status", "pending")
    if not isinstance(step, str):
        raise RuntimeError(f"Stored plan item {index} step is not a string")
    if not isinstance(status, str):
        raise RuntimeError(f"Stored plan item {index} status is not a string")
    return PlanItem(step=step, status=cast(PlanStatus, status))


__all__ = ["SqlitePlanStore", "create_plan_factory_hooks"]
