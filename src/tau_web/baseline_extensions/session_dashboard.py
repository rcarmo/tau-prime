"""Public-service aggregation for Tau Web's bundled session dashboard."""

from __future__ import annotations

import asyncio
import math
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from tau_agent.session import SessionState
from tau_coding.agent_pool import AsyncAgentPool, PoolSessionSnapshot, PoolSessionState
from tau_coding.context_window import DEFAULT_CONTEXT_WINDOW_TOKENS, estimate_message_tokens
from tau_web.events import WebEventEnvelope
from tau_web.sqlite.repositories import (
    QueueRepository,
    RunRecord,
    RunRepository,
    TimelineMessageRecord,
    TimelineMessageRepository,
)
from tau_web.sqlite.session_storage import SqliteSessionStorage
from tau_web.sqlite.sessions import SessionRecord, SessionRepository

DASHBOARD_EVENT_TYPE = "tau.dashboard.updated"
DashboardActivityState = Literal["active", "working", "streaming", "idle"]
DashboardPreviewKind = Literal["draft", "thinking", "tool", "summary", "none"]
_MAX_PREVIEW_CHARS = 2_000
_MAX_SUMMARY_CHARS = 280
_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class DashboardSession:
    """One durable session enriched with live runtime state."""

    session_id: str
    agent_name: str
    title: str | None
    workspace: Path
    activity_state: DashboardActivityState
    pool_state: str | None
    last_activity: str
    latest_assistant_summary: str
    preview_kind: DashboardPreviewKind
    preview: str
    context_used_tokens: int
    context_window_tokens: int
    context_percent: float
    queue_count: int
    model: str
    has_error: bool


@dataclass(frozen=True, slots=True)
class DashboardSnapshot:
    """One page of dashboard tiles."""

    sessions: tuple[DashboardSession, ...]
    page: int
    page_size: int
    total: int
    total_pages: int
    generated_at: str


@dataclass(slots=True)
class _LivePreview:
    draft: str = ""
    thinking: str = ""
    current_tool: str = ""
    updated_at: str = ""


class SessionDashboard:
    """Aggregate dashboard state from the pool and durable public repositories."""

    def __init__(
        self,
        *,
        sessions: SessionRepository,
        runs: RunRepository,
        queues: QueueRepository,
        timeline: TimelineMessageRepository,
        pool: AsyncAgentPool,
        storage_for: Callable[[str], SqliteSessionStorage],
    ) -> None:
        self._sessions = sessions
        self._runs = runs
        self._queues = queues
        self._timeline = timeline
        self._pool = pool
        self._storage_for = storage_for
        self._previews: dict[str, _LivePreview] = {}

    async def observe(self, envelope: WebEventEnvelope) -> bool:
        """Update transient preview state and report whether a tile changed."""
        preview = self._previews.setdefault(envelope.session_id, _LivePreview())
        event_type = envelope.type
        payload = envelope.payload
        changed = False

        if event_type == "tau.agent.message_start":
            if payload.get("message_role") == "assistant":
                preview.draft = ""
                preview.thinking = ""
                preview.current_tool = ""
                changed = True
        elif event_type == "tau.agent.message_delta":
            delta = payload.get("delta")
            if isinstance(delta, str) and delta:
                preview.draft = _append_preview(preview.draft, delta)
                changed = True
        elif event_type == "tau.agent.thinking_delta":
            delta = payload.get("delta")
            if isinstance(delta, str) and delta:
                preview.thinking = _append_preview(preview.thinking, delta)
                changed = True
        elif event_type == "tau.agent.tool_execution_start":
            tool_call = payload.get("tool_call")
            if isinstance(tool_call, dict):
                name = tool_call.get("name")
                if isinstance(name, str) and name:
                    preview.current_tool = name
                    changed = True
        elif event_type == "tau.agent.tool_execution_update":
            message = payload.get("message")
            if isinstance(message, str) and message:
                preview.current_tool = message
                changed = True
        elif event_type == "tau.agent.tool_execution_end":
            if preview.current_tool:
                preview.current_tool = ""
                changed = True
        elif event_type in {
            "tau.agent.message_end",
            "tau.agent.agent_end",
            "tau.agent.error",
        }:
            changed = bool(preview.draft or preview.thinking or preview.current_tool)
            preview.draft = ""
            preview.thinking = ""
            preview.current_tool = ""

        if changed:
            preview.updated_at = envelope.created_at
        return changed

    async def snapshot(self, *, page: int, page_size: int) -> DashboardSnapshot:
        """Return one bounded page, enriching only the visible sessions."""
        records = await self._sessions.list(include_archived=False)
        total = len(records)
        total_pages = max(1, math.ceil(total / page_size))
        selected_page = min(page, total_pages)
        start = (selected_page - 1) * page_size
        visible = records[start : start + page_size]
        run_map = _latest_runs(await self._runs.list())
        pool_map = {item.session_id: item for item in self._pool.snapshots()}
        sessions = await asyncio.gather(
            *(
                self._session_resource(
                    record,
                    run=run_map.get(record.session_id),
                    pool_snapshot=pool_map.get(record.session_id),
                )
                for record in visible
            )
        )
        return DashboardSnapshot(
            sessions=tuple(sessions),
            page=selected_page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            generated_at=_timestamp(),
        )

    async def _session_resource(
        self,
        record: SessionRecord,
        *,
        run: RunRecord | None,
        pool_snapshot: PoolSessionSnapshot | None,
    ) -> DashboardSession:
        workspace, queue, summary, context = await asyncio.gather(
            self._sessions.get_workspace(record.workspace_id),
            self._queues.list(session_id=record.session_id),
            self._timeline.latest_assistant(session_id=record.session_id),
            self._context_usage(record),
        )
        if workspace is None:
            raise RuntimeError(f"Unknown workspace for session {record.session_id}")
        preview = self._previews.get(record.session_id)
        preview_kind, preview_text = _select_preview(preview, summary)
        last_activity = _latest_timestamp(
            record.updated_at,
            run.updated_at if run is not None else None,
            preview.updated_at if preview is not None else None,
        )
        used_tokens, window_tokens = context
        return DashboardSession(
            session_id=record.session_id,
            agent_name=record.agent_name,
            title=record.title,
            workspace=workspace.root_path,
            activity_state=_activity_state(pool_snapshot, preview),
            pool_state=pool_snapshot.state.value if pool_snapshot is not None else None,
            last_activity=last_activity,
            latest_assistant_summary=_summary_text(summary),
            preview_kind=preview_kind,
            preview=preview_text,
            context_used_tokens=used_tokens,
            context_window_tokens=window_tokens,
            context_percent=min(100.0, (used_tokens / window_tokens) * 100.0),
            queue_count=len(queue),
            model=record.model,
            has_error=bool(
                pool_snapshot is not None
                and (
                    pool_snapshot.last_error is not None
                    or pool_snapshot.last_exception is not None
                )
            ),
        )

    async def _context_usage(self, record: SessionRecord) -> tuple[int, int]:
        window = _context_window(record)
        if record.active_leaf_entry_id is None:
            return 0, window
        entries = await self._storage_for(record.session_id).read_all()
        state = SessionState.from_entries(entries, leaf_id=record.active_leaf_entry_id)
        used = sum(estimate_message_tokens(message) for message in state.messages)
        return used, window


def _activity_state(
    snapshot: PoolSessionSnapshot | None,
    preview: _LivePreview | None,
) -> DashboardActivityState:
    if snapshot is None:
        return "idle"
    if snapshot.state in {PoolSessionState.RUNNING, PoolSessionState.CANCELLING}:
        if preview is not None and preview.draft:
            return "streaming"
        return "working"
    if snapshot.state in {PoolSessionState.IDLE, PoolSessionState.QUEUED}:
        return "active"
    return "idle"


def _select_preview(
    preview: _LivePreview | None,
    summary: TimelineMessageRecord | None,
) -> tuple[DashboardPreviewKind, str]:
    if preview is not None:
        if preview.draft:
            return "draft", _compact_text(preview.draft, _MAX_SUMMARY_CHARS)
        if preview.thinking:
            return "thinking", _compact_text(preview.thinking, _MAX_SUMMARY_CHARS)
        if preview.current_tool:
            return "tool", _compact_text(preview.current_tool, _MAX_SUMMARY_CHARS)
    summary_text = _summary_text(summary)
    if summary_text:
        return "summary", summary_text
    return "none", "No assistant summary yet."


def _summary_text(summary: TimelineMessageRecord | None) -> str:
    if summary is None:
        return ""
    return _compact_text(summary.content, _MAX_SUMMARY_CHARS)


def _compact_text(value: str, limit: int) -> str:
    compact = _WHITESPACE.sub(" ", value).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def _append_preview(existing: str, delta: str) -> str:
    combined = existing + delta
    return combined[-_MAX_PREVIEW_CHARS:]


def _latest_runs(runs: list[RunRecord]) -> dict[str, RunRecord]:
    latest: dict[str, RunRecord] = {}
    for run in runs:
        latest.setdefault(run.session_id, run)
    return latest


def _context_window(record: SessionRecord) -> int:
    configured = record.metadata.get("context_window_tokens")
    if isinstance(configured, int) and not isinstance(configured, bool) and configured > 0:
        return configured
    return DEFAULT_CONTEXT_WINDOW_TOKENS


def _latest_timestamp(*values: str | None) -> str:
    return max(value for value in values if value is not None)


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


__all__ = [
    "DASHBOARD_EVENT_TYPE",
    "DashboardSession",
    "DashboardSnapshot",
    "SessionDashboard",
]
