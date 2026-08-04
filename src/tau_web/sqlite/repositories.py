"""Repository boundaries and durable SQLite runtime records for Tau Web."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Literal, Protocol, cast
from uuid import uuid4

from aiosqlite import Row

from tau_agent.types import JSONObject, JSONValue
from tau_web.sqlite.connection import SqliteDatabase, SqliteReader
from tau_web.sqlite.writer import SqliteTransaction

type RunStatus = Literal[
    "pending",
    "running",
    "completed",
    "cancelled",
    "failed",
    "interrupted",
]
type QueueKind = Literal["steer", "follow_up"]
type DeliveryMode = Literal["auto", "queue", "steer"]
type DeliveryStatus = Literal[
    "pending",
    "accepted",
    "dispatched",
    "completed",
    "failed",
    "rejected",
]
type ExtensionScope = Literal["global", "workspace", "session", "connection"]

_RUN_STATUSES = frozenset({"pending", "running", "completed", "cancelled", "failed", "interrupted"})
_TERMINAL_RUN_STATUSES = frozenset({"completed", "cancelled", "failed", "interrupted"})
_QUEUE_KINDS = frozenset({"steer", "follow_up"})
_DELIVERY_MODES = frozenset({"auto", "queue", "steer"})
_DELIVERY_STATUSES = frozenset(
    {"pending", "accepted", "dispatched", "completed", "failed", "rejected"}
)
_ACCEPTED_DELIVERY_STATUSES = frozenset({"accepted", "dispatched", "completed"})
_TERMINAL_DELIVERY_STATUSES = frozenset({"completed", "failed", "rejected"})
_EXTENSION_SCOPES = frozenset({"global", "workspace", "session", "connection"})


class Repository(Protocol):
    """Common boundary implemented by SQLite-backed runtime repositories."""

    @property
    def database(self) -> SqliteDatabase: ...


class RepositoryError(RuntimeError):
    """Base error for durable runtime repositories."""


class RecordNotFoundError(RepositoryError):
    """Raised when a requested durable entity does not exist."""


class RevisionConflictError(RepositoryError):
    """Raised when an optimistic update uses a stale or missing revision."""

    def __init__(self, entity: str, *, expected: int | None, actual: int | None) -> None:
        self.entity = entity
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Revision conflict for {entity}: expected {expected!r}, actual {actual!r}"
        )


class SqliteRepository:
    """Base class that keeps repositories behind the database service."""

    def __init__(self, database: SqliteDatabase) -> None:
        self._database = database

    @property
    def database(self) -> SqliteDatabase:
        return self._database


@dataclass(frozen=True, slots=True)
class PlanRecord:
    session_id: str
    markdown: str
    explanation: str | None
    revision: int
    updated_at: str
    updated_by: str


@dataclass(frozen=True, slots=True)
class RunRecord:
    run_id: str
    session_id: str
    status: RunStatus
    started_at: str
    updated_at: str
    ended_at: str | None
    last_event_type: str | None
    last_status: JSONValue | None
    error: JSONObject | None


@dataclass(frozen=True, slots=True)
class QueueMessageRecord:
    queue_id: str
    session_id: str
    queue_kind: QueueKind
    position: int
    content: JSONValue
    source_session_id: str | None
    created_at: str
    consumed_at: str | None


@dataclass(frozen=True, slots=True)
class DeliveryRecord:
    delivery_id: str
    transport: str
    source_session_id: str
    target_session_id: str | None
    target_address: str | None
    mode: DeliveryMode
    content: str
    idempotency_key: str | None
    in_reply_to: str | None
    ancestry: tuple[str, ...]
    hop_count: int
    status: DeliveryStatus
    created_at: str
    accepted_at: str | None
    completed_at: str | None
    error: JSONObject | None


@dataclass(frozen=True, slots=True)
class UsageRecord:
    usage_id: int
    session_id: str
    run_id: str | None
    provider_name: str
    model: str
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int
    cost_microunits: int | None
    details: JSONObject
    recorded_at: str


@dataclass(frozen=True, slots=True)
class MediaBlobRecord:
    blob_id: str
    sha256: str
    content: bytes
    byte_length: int
    created_at: str


@dataclass(frozen=True, slots=True)
class MediaItemRecord:
    media_id: str
    session_id: str | None
    blob_id: str
    thumbnail_blob_id: str | None
    filename: str
    media_type: str
    width: int | None
    height: int | None
    metadata: JSONObject
    created_at: str
    deleted_at: str | None


@dataclass(frozen=True, slots=True)
class MediaReferenceRecord:
    media_id: str
    reference_type: str
    reference_id: str
    created_at: str


@dataclass(frozen=True, slots=True)
class MediaCleanupResult:
    items_deleted: int
    blobs_deleted: int


@dataclass(frozen=True, slots=True)
class ExtensionStateRecord:
    extension_id: str
    scope: ExtensionScope
    scope_id: str
    key: str
    value: JSONValue
    revision: int
    updated_at: str


@dataclass(frozen=True, slots=True)
class AuditRecord:
    audit_id: int
    event_type: str
    actor_type: str
    actor_id: str | None
    workspace_id: str | None
    session_id: str | None
    extension_id: str | None
    request_id: str | None
    details: JSONObject
    created_at: str


@dataclass(frozen=True, slots=True)
class SearchResult:
    entity_type: str
    entity_id: str
    session_id: str | None
    text: str
    rank: float


class PlanRepository(SqliteRepository):
    """Store canonical session plans with optimistic revision checks."""

    async def get(self, session_id: str) -> PlanRecord | None:
        async def read(reader: SqliteReader) -> PlanRecord | None:
            row = await reader.fetch_one(
                """
                SELECT session_id, markdown, explanation, revision, updated_at, updated_by
                FROM session_plans
                WHERE session_id = ?
                """,
                (session_id,),
            )
            return _plan_from_row(row) if row is not None else None

        return await self.database.read(read)

    async def save(
        self,
        session_id: str,
        *,
        markdown: str,
        explanation: str | None,
        updated_by: str,
        expected_revision: int | None,
    ) -> PlanRecord:
        """Create a plan or replace it when ``expected_revision`` is current.

        A missing plan accepts ``None`` or zero. Existing plans always require an
        exact revision, preventing a stale browser or tool update from winning.
        """
        session_key = _require_identifier(session_id, field="Session id")
        actor = _require_non_empty_text(updated_by, field="Updated by")
        timestamp = _timestamp()

        async def write(transaction: SqliteTransaction) -> PlanRecord:
            row = await transaction.fetch_one(
                "SELECT revision FROM session_plans WHERE session_id = ?",
                (session_key,),
            )
            actual_revision = int(row["revision"]) if row is not None else None
            if actual_revision is None:
                if expected_revision not in (None, 0):
                    raise RevisionConflictError(
                        f"session_plan:{session_key}",
                        expected=expected_revision,
                        actual=None,
                    )
                revision = 1
                await transaction.execute(
                    """
                    INSERT INTO session_plans(
                        session_id, markdown, explanation, revision, updated_at, updated_by
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (session_key, markdown, explanation, revision, timestamp, actor),
                )
            else:
                if expected_revision != actual_revision:
                    raise RevisionConflictError(
                        f"session_plan:{session_key}",
                        expected=expected_revision,
                        actual=actual_revision,
                    )
                revision = actual_revision + 1
                changed = await transaction.execute(
                    """
                    UPDATE session_plans
                    SET markdown = ?, explanation = ?, revision = ?,
                        updated_at = ?, updated_by = ?
                    WHERE session_id = ? AND revision = ?
                    """,
                    (
                        markdown,
                        explanation,
                        revision,
                        timestamp,
                        actor,
                        session_key,
                        actual_revision,
                    ),
                )
                if changed != 1:
                    raise RevisionConflictError(
                        f"session_plan:{session_key}",
                        expected=expected_revision,
                        actual=None,
                    )
            return PlanRecord(
                session_id=session_key,
                markdown=markdown,
                explanation=explanation,
                revision=revision,
                updated_at=timestamp,
                updated_by=actor,
            )

        return await self.database.write(write)


class RunRepository(SqliteRepository):
    """Persist durable run lifecycle state for one or many sessions."""

    async def create(
        self,
        session_id: str,
        *,
        run_id: str | None = None,
        status: RunStatus = "pending",
        last_event_type: str | None = None,
        last_status: JSONValue | None = None,
        error: JSONObject | None = None,
    ) -> RunRecord:
        session_key = _require_identifier(session_id, field="Session id")
        record_id = run_id or uuid4().hex
        selected_status = _validate_run_status(status)
        timestamp = _timestamp()
        ended_at = timestamp if selected_status in _TERMINAL_RUN_STATUSES else None
        last_status_json = _dump_optional_json(last_status)
        error_json = _dump_optional_object(error)

        async def write(transaction: SqliteTransaction) -> RunRecord:
            await transaction.execute(
                """
                INSERT INTO session_runs(
                    run_id, session_id, status, started_at, updated_at,
                    ended_at, last_event_type, last_status_json, error_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    session_key,
                    selected_status,
                    timestamp,
                    timestamp,
                    ended_at,
                    last_event_type,
                    last_status_json,
                    error_json,
                ),
            )
            row = await transaction.fetch_one(
                "SELECT * FROM session_runs WHERE run_id = ?",
                (record_id,),
            )
            if row is None:
                raise RuntimeError("Run insert did not return a record")
            return _run_from_row(row)

        return await self.database.write(write)

    async def get(self, run_id: str) -> RunRecord | None:
        async def read(reader: SqliteReader) -> RunRecord | None:
            row = await reader.fetch_one(
                "SELECT * FROM session_runs WHERE run_id = ?",
                (run_id,),
            )
            return _run_from_row(row) if row is not None else None

        return await self.database.read(read)

    async def list(
        self,
        *,
        session_id: str | None = None,
        statuses: Sequence[RunStatus] | None = None,
    ) -> list[RunRecord]:
        clauses: list[str] = []
        parameters: list[object] = []
        if session_id is not None:
            clauses.append("session_id = ?")
            parameters.append(session_id)
        if statuses is not None:
            selected_statuses = tuple(_validate_run_status(status) for status in statuses)
            if not selected_statuses:
                return []
            _append_in_clause(clauses, parameters, "status", selected_statuses)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        async def read(reader: SqliteReader) -> list[RunRecord]:
            rows = await reader.fetch_all(
                f"SELECT * FROM session_runs {where} ORDER BY started_at DESC, run_id",
                parameters,
            )
            return [_run_from_row(row) for row in rows]

        return await self.database.read(read)

    async def update_status(
        self,
        run_id: str,
        *,
        status: RunStatus,
        last_event_type: str | None = None,
        last_status: JSONValue | None = None,
        error: JSONObject | None = None,
    ) -> RunRecord:
        record_id = _require_identifier(run_id, field="Run id")
        selected_status = _validate_run_status(status)
        timestamp = _timestamp()
        last_status_json = _dump_optional_json(last_status)
        error_json = _dump_optional_object(error)

        async def write(transaction: SqliteTransaction) -> RunRecord:
            current_row = await transaction.fetch_one(
                "SELECT * FROM session_runs WHERE run_id = ?",
                (record_id,),
            )
            if current_row is None:
                raise RecordNotFoundError(f"Unknown run: {record_id}")
            current = _run_from_row(current_row)
            if current.ended_at is not None and selected_status not in _TERMINAL_RUN_STATUSES:
                raise RepositoryError("Terminal runs cannot become active again")
            ended_at = current.ended_at
            if selected_status in _TERMINAL_RUN_STATUSES and ended_at is None:
                ended_at = timestamp
            await transaction.execute(
                """
                UPDATE session_runs
                SET status = ?, updated_at = ?, ended_at = ?,
                    last_event_type = ?, last_status_json = ?, error_json = ?
                WHERE run_id = ?
                """,
                (
                    selected_status,
                    timestamp,
                    ended_at,
                    last_event_type,
                    last_status_json,
                    error_json,
                    record_id,
                ),
            )
            updated_row = await transaction.fetch_one(
                "SELECT * FROM session_runs WHERE run_id = ?",
                (record_id,),
            )
            if updated_row is None:
                raise RuntimeError("Run update did not return a record")
            return _run_from_row(updated_row)

        return await self.database.write(write)

    async def purge_terminal_before(self, cutoff: str) -> int:
        async def write(transaction: SqliteTransaction) -> int:
            count = await _count_rows(
                transaction,
                """
                SELECT COUNT(*) FROM session_runs
                WHERE status IN ('completed', 'cancelled', 'failed', 'interrupted')
                  AND ended_at IS NOT NULL
                  AND ended_at <= ?
                """,
                (cutoff,),
            )
            if count:
                await transaction.execute(
                    """
                    DELETE FROM session_runs
                    WHERE status IN ('completed', 'cancelled', 'failed', 'interrupted')
                      AND ended_at IS NOT NULL
                      AND ended_at <= ?
                    """,
                    (cutoff,),
                )
            return count

        return await self.database.write(write)


class QueueRepository(SqliteRepository):
    """Persist steering and follow-up queues through the shared writer."""

    async def enqueue(
        self,
        session_id: str,
        *,
        queue_kind: QueueKind,
        content: JSONValue,
        source_session_id: str | None = None,
        queue_id: str | None = None,
    ) -> QueueMessageRecord:
        session_key = _require_identifier(session_id, field="Session id")
        selected_kind = _validate_queue_kind(queue_kind)
        record_id = queue_id or uuid4().hex
        timestamp = _timestamp()
        content_json = _dump_json(content)

        async def write(transaction: SqliteTransaction) -> QueueMessageRecord:
            row = await transaction.fetch_one(
                """
                SELECT COALESCE(MAX(position), -1) + 1 AS next_position
                FROM queued_messages
                WHERE session_id = ? AND queue_kind = ?
                """,
                (session_key, selected_kind),
            )
            if row is None:
                raise RuntimeError("Queue position allocation failed")
            next_position = int(row["next_position"])
            await transaction.execute(
                """
                INSERT INTO queued_messages(
                    queue_id, session_id, queue_kind, position,
                    content_json, source_session_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    session_key,
                    selected_kind,
                    next_position,
                    content_json,
                    source_session_id,
                    timestamp,
                ),
            )
            row = await transaction.fetch_one(
                "SELECT * FROM queued_messages WHERE queue_id = ?",
                (record_id,),
            )
            if row is None:
                raise RuntimeError("Queue insert did not return a record")
            return _queue_from_row(row)

        return await self.database.write(write)

    async def get(self, queue_id: str) -> QueueMessageRecord | None:
        async def read(reader: SqliteReader) -> QueueMessageRecord | None:
            row = await reader.fetch_one(
                "SELECT * FROM queued_messages WHERE queue_id = ?",
                (queue_id,),
            )
            return _queue_from_row(row) if row is not None else None

        return await self.database.read(read)

    async def list(
        self,
        *,
        session_id: str,
        queue_kind: QueueKind | None = None,
        include_consumed: bool = False,
    ) -> list[QueueMessageRecord]:
        session_key = _require_identifier(session_id, field="Session id")
        clauses = ["session_id = ?"]
        parameters: list[object] = [session_key]
        if queue_kind is not None:
            clauses.append("queue_kind = ?")
            parameters.append(_validate_queue_kind(queue_kind))
        if not include_consumed:
            clauses.append("consumed_at IS NULL")
        where = f"WHERE {' AND '.join(clauses)}"

        async def read(reader: SqliteReader) -> list[QueueMessageRecord]:
            rows = await reader.fetch_all(
                f"SELECT * FROM queued_messages {where} ORDER BY queue_kind, position",
                parameters,
            )
            return [_queue_from_row(row) for row in rows]

        return await self.database.read(read)

    async def consume_next(
        self,
        session_id: str,
        queue_kind: QueueKind,
    ) -> QueueMessageRecord | None:
        session_key = _require_identifier(session_id, field="Session id")
        selected_kind = _validate_queue_kind(queue_kind)
        timestamp = _timestamp()

        async def write(transaction: SqliteTransaction) -> QueueMessageRecord | None:
            row = await transaction.fetch_one(
                """
                SELECT * FROM queued_messages
                WHERE session_id = ? AND queue_kind = ? AND consumed_at IS NULL
                ORDER BY position
                LIMIT 1
                """,
                (session_key, selected_kind),
            )
            if row is None:
                return None
            queue_id = str(row["queue_id"])
            await transaction.execute(
                "UPDATE queued_messages SET consumed_at = ? WHERE queue_id = ?",
                (timestamp, queue_id),
            )
            updated = await transaction.fetch_one(
                "SELECT * FROM queued_messages WHERE queue_id = ?",
                (queue_id,),
            )
            if updated is None:
                raise RuntimeError("Queue update did not return a record")
            return _queue_from_row(updated)

        return await self.database.write(write)

    async def consume_exact(
        self,
        queue_id: str,
        *,
        session_id: str,
        queue_kind: QueueKind,
    ) -> QueueMessageRecord:
        record_id = _require_identifier(queue_id, field="Queue id")
        session_key = _require_identifier(session_id, field="Session id")
        selected_kind = _validate_queue_kind(queue_kind)
        timestamp = _timestamp()

        async def write(transaction: SqliteTransaction) -> QueueMessageRecord:
            current_row = await transaction.fetch_one(
                "SELECT * FROM queued_messages WHERE queue_id = ?",
                (record_id,),
            )
            if current_row is None:
                raise RecordNotFoundError(f"Unknown queued message: {record_id}")
            current = _queue_from_row(current_row)
            if current.session_id != session_key or current.queue_kind != selected_kind:
                raise RepositoryError("Queued message does not belong to the requested session")
            if current.consumed_at is not None:
                raise RepositoryError("Queued message has already been consumed")

            head_row = await transaction.fetch_one(
                """
                SELECT * FROM queued_messages
                WHERE session_id = ? AND queue_kind = ? AND consumed_at IS NULL
                ORDER BY position
                LIMIT 1
                """,
                (session_key, selected_kind),
            )
            if head_row is None:
                raise RepositoryError("No pending queued messages exist for the requested session")
            if str(head_row["queue_id"]) != record_id:
                raise RepositoryError("Queued message is not the next FIFO row")

            await transaction.execute(
                "UPDATE queued_messages SET consumed_at = ? WHERE queue_id = ?",
                (timestamp, record_id),
            )
            updated = await transaction.fetch_one(
                "SELECT * FROM queued_messages WHERE queue_id = ?",
                (record_id,),
            )
            if updated is None:
                raise RuntimeError("Queue update did not return a record")
            return _queue_from_row(updated)

        return await self.database.write(write)

    async def purge_consumed_before(self, cutoff: str) -> int:
        async def write(transaction: SqliteTransaction) -> int:
            count = await _count_rows(
                transaction,
                """
                SELECT COUNT(*) FROM queued_messages
                WHERE consumed_at IS NOT NULL AND consumed_at <= ?
                """,
                (cutoff,),
            )
            if count:
                await transaction.execute(
                    """
                    DELETE FROM queued_messages
                    WHERE consumed_at IS NOT NULL AND consumed_at <= ?
                    """,
                    (cutoff,),
                )
            return count

        return await self.database.write(write)


class DeliveryRepository(SqliteRepository):
    """Persist inter-session chat deliveries with idempotent creation."""

    async def create(
        self,
        *,
        source_session_id: str,
        mode: DeliveryMode,
        content: str,
        target_session_id: str | None = None,
        target_address: str | None = None,
        delivery_id: str | None = None,
        transport: str = "local",
        idempotency_key: str | None = None,
        in_reply_to: str | None = None,
        ancestry: Sequence[str] = (),
        hop_count: int | None = None,
        status: DeliveryStatus = "pending",
        error: JSONObject | None = None,
    ) -> DeliveryRecord:
        source_key = _require_identifier(source_session_id, field="Source session id")
        if target_session_id is None and target_address is None:
            raise ValueError("Target session id or target address is required")
        selected_mode = _validate_delivery_mode(mode)
        selected_status = _validate_delivery_status(status)
        delivery_key = delivery_id or uuid4().hex
        transport_name = _require_non_empty_text(transport, field="Transport")
        message = _require_non_empty_text(content, field="Content")
        lineage = tuple(_require_identifier(item, field="Ancestry entry") for item in ancestry)
        hops = len(lineage) if hop_count is None else hop_count
        if hops < 0:
            raise ValueError("Hop count must not be negative")
        timestamp = _timestamp()
        accepted_at = timestamp if selected_status in _ACCEPTED_DELIVERY_STATUSES else None
        completed_at = timestamp if selected_status in _TERMINAL_DELIVERY_STATUSES else None
        error_json = _dump_optional_object(error)

        async def write(transaction: SqliteTransaction) -> DeliveryRecord:
            if idempotency_key is not None:
                existing = await transaction.fetch_one(
                    """
                    SELECT * FROM chat_deliveries
                    WHERE transport = ? AND idempotency_key = ?
                    """,
                    (transport_name, idempotency_key),
                )
                if existing is not None:
                    return _delivery_from_row(existing)
            await transaction.execute(
                """
                INSERT INTO chat_deliveries(
                    delivery_id, transport, source_session_id, target_session_id,
                    target_address, mode, content, idempotency_key, in_reply_to,
                    ancestry_json, hop_count, status, created_at,
                    accepted_at, completed_at, error_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    delivery_key,
                    transport_name,
                    source_key,
                    target_session_id,
                    target_address,
                    selected_mode,
                    message,
                    idempotency_key,
                    in_reply_to,
                    _dump_json(list(lineage)),
                    hops,
                    selected_status,
                    timestamp,
                    accepted_at,
                    completed_at,
                    error_json,
                ),
            )
            row = await transaction.fetch_one(
                "SELECT * FROM chat_deliveries WHERE delivery_id = ?",
                (delivery_key,),
            )
            if row is None:
                raise RuntimeError("Delivery insert did not return a record")
            return _delivery_from_row(row)

        return await self.database.write(write)

    async def get(self, delivery_id: str) -> DeliveryRecord | None:
        async def read(reader: SqliteReader) -> DeliveryRecord | None:
            row = await reader.fetch_one(
                "SELECT * FROM chat_deliveries WHERE delivery_id = ?",
                (delivery_id,),
            )
            return _delivery_from_row(row) if row is not None else None

        return await self.database.read(read)

    async def list(
        self,
        *,
        source_session_id: str | None = None,
        target_session_id: str | None = None,
        statuses: Sequence[DeliveryStatus] | None = None,
    ) -> list[DeliveryRecord]:
        clauses: list[str] = []
        parameters: list[object] = []
        if source_session_id is not None:
            clauses.append("source_session_id = ?")
            parameters.append(source_session_id)
        if target_session_id is not None:
            clauses.append("target_session_id = ?")
            parameters.append(target_session_id)
        if statuses is not None:
            selected_statuses = tuple(_validate_delivery_status(status) for status in statuses)
            if not selected_statuses:
                return []
            _append_in_clause(clauses, parameters, "status", selected_statuses)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        async def read(reader: SqliteReader) -> list[DeliveryRecord]:
            rows = await reader.fetch_all(
                f"SELECT * FROM chat_deliveries {where} ORDER BY created_at DESC, delivery_id",
                parameters,
            )
            return [_delivery_from_row(row) for row in rows]

        return await self.database.read(read)

    async def resolve_target(
        self,
        delivery_id: str,
        target_session_id: str,
    ) -> DeliveryRecord:
        delivery_key = _require_identifier(delivery_id, field="Delivery id")
        target_key = _require_identifier(target_session_id, field="Target session id")

        async def write(transaction: SqliteTransaction) -> DeliveryRecord:
            current_row = await transaction.fetch_one(
                "SELECT * FROM chat_deliveries WHERE delivery_id = ?",
                (delivery_key,),
            )
            if current_row is None:
                raise RecordNotFoundError(f"Unknown delivery: {delivery_key}")
            current = _delivery_from_row(current_row)
            if current.completed_at is not None and current.target_session_id is None:
                raise RepositoryError(
                    "Terminal deliveries without a resolved target cannot be resolved"
                )
            if current.target_session_id is not None and current.target_session_id != target_key:
                raise RepositoryError("Delivery target session has already been resolved")
            await transaction.execute(
                "UPDATE chat_deliveries SET target_session_id = ? WHERE delivery_id = ?",
                (target_key, delivery_key),
            )
            updated_row = await transaction.fetch_one(
                "SELECT * FROM chat_deliveries WHERE delivery_id = ?",
                (delivery_key,),
            )
            if updated_row is None:
                raise RuntimeError("Delivery target resolution did not return a record")
            return _delivery_from_row(updated_row)

        return await self.database.write(write)

    async def update_status(
        self,
        delivery_id: str,
        *,
        status: DeliveryStatus,
        error: JSONObject | None = None,
    ) -> DeliveryRecord:
        delivery_key = _require_identifier(delivery_id, field="Delivery id")
        selected_status = _validate_delivery_status(status)
        timestamp = _timestamp()
        error_json = _dump_optional_object(error)

        async def write(transaction: SqliteTransaction) -> DeliveryRecord:
            current_row = await transaction.fetch_one(
                "SELECT * FROM chat_deliveries WHERE delivery_id = ?",
                (delivery_key,),
            )
            if current_row is None:
                raise RecordNotFoundError(f"Unknown delivery: {delivery_key}")
            current = _delivery_from_row(current_row)
            if (
                current.completed_at is not None
                and selected_status not in _TERMINAL_DELIVERY_STATUSES
            ):
                raise RepositoryError("Terminal deliveries cannot become active again")
            accepted_at = current.accepted_at
            completed_at = current.completed_at
            if selected_status in _ACCEPTED_DELIVERY_STATUSES and accepted_at is None:
                accepted_at = timestamp
            if selected_status in _TERMINAL_DELIVERY_STATUSES and completed_at is None:
                completed_at = timestamp
            await transaction.execute(
                """
                UPDATE chat_deliveries
                SET status = ?, accepted_at = ?, completed_at = ?, error_json = ?
                WHERE delivery_id = ?
                """,
                (selected_status, accepted_at, completed_at, error_json, delivery_key),
            )
            updated_row = await transaction.fetch_one(
                "SELECT * FROM chat_deliveries WHERE delivery_id = ?",
                (delivery_key,),
            )
            if updated_row is None:
                raise RuntimeError("Delivery update did not return a record")
            return _delivery_from_row(updated_row)

        return await self.database.write(write)

    async def purge_terminal_before(self, cutoff: str) -> int:
        async def write(transaction: SqliteTransaction) -> int:
            count = await _count_rows(
                transaction,
                """
                SELECT COUNT(*) FROM chat_deliveries
                WHERE status IN ('completed', 'failed', 'rejected')
                  AND completed_at IS NOT NULL
                  AND completed_at <= ?
                """,
                (cutoff,),
            )
            if count:
                await transaction.execute(
                    """
                    DELETE FROM chat_deliveries
                    WHERE status IN ('completed', 'failed', 'rejected')
                      AND completed_at IS NOT NULL
                      AND completed_at <= ?
                    """,
                    (cutoff,),
                )
            return count

        return await self.database.write(write)


class UsageRepository(SqliteRepository):
    """Persist provider token and cost accounting for durable session history."""

    async def record(
        self,
        session_id: str,
        *,
        provider_name: str,
        model: str,
        run_id: str | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cached_input_tokens: int = 0,
        cost_microunits: int | None = None,
        details: JSONObject | None = None,
    ) -> UsageRecord:
        session_key = _require_identifier(session_id, field="Session id")
        provider = _require_non_empty_text(provider_name, field="Provider name")
        selected_model = _require_non_empty_text(model, field="Model")
        _require_non_negative(input_tokens, field="Input tokens")
        _require_non_negative(output_tokens, field="Output tokens")
        _require_non_negative(cached_input_tokens, field="Cached input tokens")
        if cost_microunits is not None:
            _require_non_negative(cost_microunits, field="Cost microunits")
        timestamp = _timestamp()
        details_json = _dump_json(details or {})

        async def write(transaction: SqliteTransaction) -> UsageRecord:
            usage_id = await transaction.execute_insert(
                """
                INSERT INTO usage_records(
                    session_id, run_id, provider_name, model, input_tokens,
                    output_tokens, cached_input_tokens, cost_microunits,
                    details_json, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_key,
                    run_id,
                    provider,
                    selected_model,
                    input_tokens,
                    output_tokens,
                    cached_input_tokens,
                    cost_microunits,
                    details_json,
                    timestamp,
                ),
            )
            row = await transaction.fetch_one(
                "SELECT * FROM usage_records WHERE usage_id = ?",
                (usage_id,),
            )
            if row is None:
                raise RuntimeError("Usage insert did not return a record")
            return _usage_from_row(row)

        return await self.database.write(write)

    async def list(
        self,
        *,
        session_id: str | None = None,
        run_id: str | None = None,
    ) -> list[UsageRecord]:
        clauses: list[str] = []
        parameters: list[object] = []
        if session_id is not None:
            clauses.append("session_id = ?")
            parameters.append(session_id)
        if run_id is not None:
            clauses.append("run_id = ?")
            parameters.append(run_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        async def read(reader: SqliteReader) -> list[UsageRecord]:
            rows = await reader.fetch_all(
                f"SELECT * FROM usage_records {where} ORDER BY recorded_at DESC, usage_id DESC",
                parameters,
            )
            return [_usage_from_row(row) for row in rows]

        return await self.database.read(read)

    async def purge_before(self, cutoff: str) -> int:
        async def write(transaction: SqliteTransaction) -> int:
            count = await _count_rows(
                transaction,
                "SELECT COUNT(*) FROM usage_records WHERE recorded_at <= ?",
                (cutoff,),
            )
            if count:
                await transaction.execute(
                    "DELETE FROM usage_records WHERE recorded_at <= ?",
                    (cutoff,),
                )
            return count

        return await self.database.write(write)


class MediaRepository(SqliteRepository):
    """Persist media blobs, logical items, and their references."""

    async def store_blob(
        self,
        content: bytes,
        *,
        blob_id: str | None = None,
    ) -> MediaBlobRecord:
        if not content:
            raise ValueError("Media blob content must not be empty")
        digest = sha256(content).hexdigest()
        record_id = blob_id or uuid4().hex
        timestamp = _timestamp()

        async def write(transaction: SqliteTransaction) -> MediaBlobRecord:
            existing = await transaction.fetch_one(
                "SELECT * FROM media_blobs WHERE sha256 = ?",
                (digest,),
            )
            if existing is not None:
                return _media_blob_from_row(existing)
            await transaction.execute(
                """
                INSERT INTO media_blobs(blob_id, sha256, content, byte_length, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (record_id, digest, content, len(content), timestamp),
            )
            row = await transaction.fetch_one(
                "SELECT * FROM media_blobs WHERE blob_id = ?",
                (record_id,),
            )
            if row is None:
                raise RuntimeError("Media blob insert did not return a record")
            return _media_blob_from_row(row)

        return await self.database.write(write)

    async def get_blob(self, blob_id: str) -> MediaBlobRecord | None:
        async def read(reader: SqliteReader) -> MediaBlobRecord | None:
            row = await reader.fetch_one(
                "SELECT * FROM media_blobs WHERE blob_id = ?",
                (blob_id,),
            )
            return _media_blob_from_row(row) if row is not None else None

        return await self.database.read(read)

    async def create_item(
        self,
        *,
        blob_id: str,
        filename: str,
        media_type: str,
        media_id: str | None = None,
        session_id: str | None = None,
        thumbnail_blob_id: str | None = None,
        width: int | None = None,
        height: int | None = None,
        metadata: JSONObject | None = None,
    ) -> MediaItemRecord:
        blob_key = _require_identifier(blob_id, field="Blob id")
        item_id = media_id or uuid4().hex
        selected_filename = _require_non_empty_text(filename, field="Filename")
        selected_media_type = _require_non_empty_text(media_type, field="Media type")
        if width is not None and width <= 0:
            raise ValueError("Width must be positive")
        if height is not None and height <= 0:
            raise ValueError("Height must be positive")
        timestamp = _timestamp()
        metadata_json = _dump_json(metadata or {})

        async def write(transaction: SqliteTransaction) -> MediaItemRecord:
            await transaction.execute(
                """
                INSERT INTO media_items(
                    media_id, session_id, blob_id, thumbnail_blob_id,
                    filename, media_type, width, height, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    session_id,
                    blob_key,
                    thumbnail_blob_id,
                    selected_filename,
                    selected_media_type,
                    width,
                    height,
                    metadata_json,
                    timestamp,
                ),
            )
            row = await transaction.fetch_one(
                "SELECT * FROM media_items WHERE media_id = ?",
                (item_id,),
            )
            if row is None:
                raise RuntimeError("Media item insert did not return a record")
            return _media_item_from_row(row)

        return await self.database.write(write)

    async def get_item(self, media_id: str) -> MediaItemRecord | None:
        async def read(reader: SqliteReader) -> MediaItemRecord | None:
            row = await reader.fetch_one(
                "SELECT * FROM media_items WHERE media_id = ?",
                (media_id,),
            )
            return _media_item_from_row(row) if row is not None else None

        return await self.database.read(read)

    async def add_reference(
        self,
        media_id: str,
        reference_type: str,
        reference_id: str,
    ) -> MediaReferenceRecord:
        media_key = _require_identifier(media_id, field="Media id")
        selected_type = _require_non_empty_text(reference_type, field="Reference type")
        selected_id = _require_non_empty_text(reference_id, field="Reference id")
        timestamp = _timestamp()

        async def write(transaction: SqliteTransaction) -> MediaReferenceRecord:
            await transaction.execute(
                """
                INSERT OR IGNORE INTO media_references(
                    media_id, reference_type, reference_id, created_at
                ) VALUES (?, ?, ?, ?)
                """,
                (media_key, selected_type, selected_id, timestamp),
            )
            row = await transaction.fetch_one(
                """
                SELECT * FROM media_references
                WHERE media_id = ? AND reference_type = ? AND reference_id = ?
                """,
                (media_key, selected_type, selected_id),
            )
            if row is None:
                raise RuntimeError("Media reference insert did not return a record")
            return _media_reference_from_row(row)

        return await self.database.write(write)

    async def list_references(self, media_id: str) -> list[MediaReferenceRecord]:
        media_key = _require_identifier(media_id, field="Media id")

        async def read(reader: SqliteReader) -> list[MediaReferenceRecord]:
            rows = await reader.fetch_all(
                """
                SELECT * FROM media_references
                WHERE media_id = ?
                ORDER BY reference_type, reference_id
                """,
                (media_key,),
            )
            return [_media_reference_from_row(row) for row in rows]

        return await self.database.read(read)

    async def mark_deleted(self, media_id: str) -> MediaItemRecord:
        media_key = _require_identifier(media_id, field="Media id")
        timestamp = _timestamp()

        async def write(transaction: SqliteTransaction) -> MediaItemRecord:
            row = await transaction.fetch_one(
                "SELECT * FROM media_items WHERE media_id = ?",
                (media_key,),
            )
            if row is None:
                raise RecordNotFoundError(f"Unknown media item: {media_key}")
            if row["deleted_at"] is None:
                await transaction.execute(
                    "UPDATE media_items SET deleted_at = ? WHERE media_id = ?",
                    (timestamp, media_key),
                )
            updated = await transaction.fetch_one(
                "SELECT * FROM media_items WHERE media_id = ?",
                (media_key,),
            )
            if updated is None:
                raise RuntimeError("Media item update did not return a record")
            return _media_item_from_row(updated)

        return await self.database.write(write)

    async def purge_deleted_before(self, cutoff: str) -> MediaCleanupResult:
        async def write(transaction: SqliteTransaction) -> MediaCleanupResult:
            items_deleted = await _count_rows(
                transaction,
                """
                SELECT COUNT(*) FROM media_items
                WHERE deleted_at IS NOT NULL AND deleted_at <= ?
                """,
                (cutoff,),
            )
            if items_deleted:
                await transaction.execute(
                    "DELETE FROM media_items WHERE deleted_at IS NOT NULL AND deleted_at <= ?",
                    (cutoff,),
                )
            blobs_deleted = await _count_rows(
                transaction,
                """
                SELECT COUNT(*) FROM media_blobs
                WHERE created_at <= ?
                  AND NOT EXISTS(
                    SELECT 1 FROM media_items
                    WHERE media_items.blob_id = media_blobs.blob_id
                       OR media_items.thumbnail_blob_id = media_blobs.blob_id
                  )
                """,
                (cutoff,),
            )
            if blobs_deleted:
                await transaction.execute(
                    """
                    DELETE FROM media_blobs
                    WHERE created_at <= ?
                      AND NOT EXISTS(
                        SELECT 1 FROM media_items
                        WHERE media_items.blob_id = media_blobs.blob_id
                           OR media_items.thumbnail_blob_id = media_blobs.blob_id
                      )
                    """,
                    (cutoff,),
                )
            return MediaCleanupResult(
                items_deleted=items_deleted,
                blobs_deleted=blobs_deleted,
            )

        return await self.database.write(write)


class ExtensionStateRepository(SqliteRepository):
    """Persist revisioned extension state by scope and stable key."""

    def __init__(
        self,
        database: SqliteDatabase,
        *,
        allow_persisted_connection_scope: bool = False,
    ) -> None:
        super().__init__(database)
        self._allow_persisted_connection_scope = allow_persisted_connection_scope

    async def get(
        self,
        extension_id: str,
        scope: ExtensionScope,
        scope_id: str,
        key: str,
    ) -> ExtensionStateRecord | None:
        extension_key, selected_scope, scope_key, state_key = self._validate_identity(
            extension_id,
            scope,
            scope_id,
            key,
        )

        async def read(reader: SqliteReader) -> ExtensionStateRecord | None:
            row = await reader.fetch_one(
                """
                SELECT * FROM extension_state
                WHERE extension_id = ? AND scope = ? AND scope_id = ? AND key = ?
                """,
                (extension_key, selected_scope, scope_key, state_key),
            )
            return _extension_state_from_row(row) if row is not None else None

        return await self.database.read(read)

    async def list_scope(
        self,
        scope: ExtensionScope,
        scope_id: str,
        *,
        extension_id: str | None = None,
    ) -> list[ExtensionStateRecord]:
        selected_scope = self._validate_scope(scope)
        scope_key = _require_identifier(scope_id, field="Scope id")
        clauses = ["scope = ?", "scope_id = ?"]
        parameters: list[object] = [selected_scope, scope_key]
        if extension_id is not None:
            clauses.append("extension_id = ?")
            parameters.append(_require_non_empty_text(extension_id, field="Extension id"))
        where = f"WHERE {' AND '.join(clauses)}"

        async def read(reader: SqliteReader) -> list[ExtensionStateRecord]:
            rows = await reader.fetch_all(
                f"SELECT * FROM extension_state {where} ORDER BY extension_id, key",
                parameters,
            )
            return [_extension_state_from_row(row) for row in rows]

        return await self.database.read(read)

    async def save(
        self,
        extension_id: str,
        *,
        scope: ExtensionScope,
        scope_id: str,
        key: str,
        value: JSONValue,
        expected_revision: int | None,
    ) -> ExtensionStateRecord:
        extension_key, selected_scope, scope_key, state_key = self._validate_identity(
            extension_id,
            scope,
            scope_id,
            key,
        )
        timestamp = _timestamp()
        value_json = _dump_json(value)

        async def write(transaction: SqliteTransaction) -> ExtensionStateRecord:
            row = await transaction.fetch_one(
                """
                SELECT revision FROM extension_state
                WHERE extension_id = ? AND scope = ? AND scope_id = ? AND key = ?
                """,
                (extension_key, selected_scope, scope_key, state_key),
            )
            actual_revision = int(row["revision"]) if row is not None else None
            if actual_revision is None:
                if expected_revision not in (None, 0):
                    raise RevisionConflictError(
                        f"extension_state:{extension_key}:{selected_scope}:{scope_key}:{state_key}",
                        expected=expected_revision,
                        actual=None,
                    )
                revision = 1
                await transaction.execute(
                    """
                    INSERT INTO extension_state(
                        extension_id, scope, scope_id, key,
                        value_json, revision, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        extension_key,
                        selected_scope,
                        scope_key,
                        state_key,
                        value_json,
                        revision,
                        timestamp,
                    ),
                )
            else:
                if expected_revision != actual_revision:
                    raise RevisionConflictError(
                        f"extension_state:{extension_key}:{selected_scope}:{scope_key}:{state_key}",
                        expected=expected_revision,
                        actual=actual_revision,
                    )
                revision = actual_revision + 1
                changed = await transaction.execute(
                    """
                    UPDATE extension_state
                    SET value_json = ?, revision = ?, updated_at = ?
                    WHERE extension_id = ? AND scope = ? AND scope_id = ? AND key = ?
                      AND revision = ?
                    """,
                    (
                        value_json,
                        revision,
                        timestamp,
                        extension_key,
                        selected_scope,
                        scope_key,
                        state_key,
                        actual_revision,
                    ),
                )
                if changed != 1:
                    raise RevisionConflictError(
                        f"extension_state:{extension_key}:{selected_scope}:{scope_key}:{state_key}",
                        expected=expected_revision,
                        actual=None,
                    )
            return ExtensionStateRecord(
                extension_id=extension_key,
                scope=selected_scope,
                scope_id=scope_key,
                key=state_key,
                value=value,
                revision=revision,
                updated_at=timestamp,
            )

        return await self.database.write(write)

    async def delete(
        self,
        extension_id: str,
        *,
        scope: ExtensionScope,
        scope_id: str,
        key: str,
        expected_revision: int,
    ) -> ExtensionStateRecord:
        extension_key, selected_scope, scope_key, state_key = self._validate_identity(
            extension_id,
            scope,
            scope_id,
            key,
        )

        async def write(transaction: SqliteTransaction) -> ExtensionStateRecord:
            row = await transaction.fetch_one(
                """
                SELECT * FROM extension_state
                WHERE extension_id = ? AND scope = ? AND scope_id = ? AND key = ?
                """,
                (extension_key, selected_scope, scope_key, state_key),
            )
            if row is None:
                identity = f"{extension_key}:{selected_scope}:{scope_key}:{state_key}"
                raise RecordNotFoundError(f"Unknown extension state: {identity}")
            record = _extension_state_from_row(row)
            if record.revision != expected_revision:
                raise RevisionConflictError(
                    f"extension_state:{extension_key}:{selected_scope}:{scope_key}:{state_key}",
                    expected=expected_revision,
                    actual=record.revision,
                )
            await transaction.execute(
                """
                DELETE FROM extension_state
                WHERE extension_id = ? AND scope = ? AND scope_id = ? AND key = ?
                """,
                (extension_key, selected_scope, scope_key, state_key),
            )
            return record

        return await self.database.write(write)

    async def clear_scope(
        self,
        scope: ExtensionScope,
        scope_id: str,
        *,
        extension_id: str | None = None,
    ) -> int:
        selected_scope = self._validate_scope(scope)
        scope_key = _require_identifier(scope_id, field="Scope id")
        clauses = ["scope = ?", "scope_id = ?"]
        parameters: list[object] = [selected_scope, scope_key]
        if extension_id is not None:
            clauses.append("extension_id = ?")
            parameters.append(_require_non_empty_text(extension_id, field="Extension id"))
        where = " AND ".join(clauses)

        async def write(transaction: SqliteTransaction) -> int:
            count = await _count_rows(
                transaction,
                f"SELECT COUNT(*) FROM extension_state WHERE {where}",
                parameters,
            )
            if count:
                await transaction.execute(
                    f"DELETE FROM extension_state WHERE {where}",
                    parameters,
                )
            return count

        return await self.database.write(write)

    async def purge_connection_scope_before(self, cutoff: str) -> int:
        async def write(transaction: SqliteTransaction) -> int:
            count = await _count_rows(
                transaction,
                """
                SELECT COUNT(*) FROM extension_state
                WHERE scope = 'connection' AND updated_at <= ?
                """,
                (cutoff,),
            )
            if count:
                await transaction.execute(
                    "DELETE FROM extension_state WHERE scope = 'connection' AND updated_at <= ?",
                    (cutoff,),
                )
            return count

        return await self.database.write(write)

    def _validate_identity(
        self,
        extension_id: str,
        scope: ExtensionScope,
        scope_id: str,
        key: str,
    ) -> tuple[str, ExtensionScope, str, str]:
        return (
            _require_non_empty_text(extension_id, field="Extension id"),
            self._validate_scope(scope),
            _require_identifier(scope_id, field="Scope id"),
            _require_non_empty_text(key, field="State key"),
        )

    def _validate_scope(self, scope: ExtensionScope) -> ExtensionScope:
        selected_scope = _validate_extension_scope(scope)
        if selected_scope == "connection" and not self._allow_persisted_connection_scope:
            raise RepositoryError("Persisted connection-scope state is disabled")
        return selected_scope


class AuditRepository(SqliteRepository):
    """Append immutable audit records and prune them by retention policy."""

    async def append(
        self,
        *,
        event_type: str,
        actor_type: str,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        session_id: str | None = None,
        extension_id: str | None = None,
        request_id: str | None = None,
        details: JSONObject | None = None,
    ) -> AuditRecord:
        selected_event_type = _require_non_empty_text(event_type, field="Event type")
        selected_actor_type = _require_non_empty_text(actor_type, field="Actor type")
        timestamp = _timestamp()
        details_json = _dump_json(details or {})

        async def write(transaction: SqliteTransaction) -> AuditRecord:
            audit_id = await transaction.execute_insert(
                """
                INSERT INTO audit_records(
                    event_type, actor_type, actor_id, workspace_id,
                    session_id, extension_id, request_id, details_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    selected_event_type,
                    selected_actor_type,
                    actor_id,
                    workspace_id,
                    session_id,
                    extension_id,
                    request_id,
                    details_json,
                    timestamp,
                ),
            )
            row = await transaction.fetch_one(
                "SELECT * FROM audit_records WHERE audit_id = ?",
                (audit_id,),
            )
            if row is None:
                raise RuntimeError("Audit insert did not return a record")
            return _audit_from_row(row)

        return await self.database.write(write)

    async def list(
        self,
        *,
        workspace_id: str | None = None,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[AuditRecord]:
        if limit <= 0:
            raise ValueError("Limit must be positive")
        clauses: list[str] = []
        parameters: list[object] = []
        if workspace_id is not None:
            clauses.append("workspace_id = ?")
            parameters.append(workspace_id)
        if session_id is not None:
            clauses.append("session_id = ?")
            parameters.append(session_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        parameters.append(limit)

        async def read(reader: SqliteReader) -> list[AuditRecord]:
            rows = await reader.fetch_all(
                f"""
                SELECT * FROM audit_records {where}
                ORDER BY created_at DESC, audit_id DESC
                LIMIT ?
                """,
                parameters,
            )
            return [_audit_from_row(row) for row in rows]

        return await self.database.read(read)

    async def purge_before(self, cutoff: str) -> int:
        async def write(transaction: SqliteTransaction) -> int:
            count = await _count_rows(
                transaction,
                "SELECT COUNT(*) FROM audit_records WHERE created_at <= ?",
                (cutoff,),
            )
            if count:
                await transaction.execute(
                    "DELETE FROM audit_records WHERE created_at <= ?",
                    (cutoff,),
                )
            return count

        return await self.database.write(write)


class SearchRepository(SqliteRepository):
    """Maintain explicit FTS rows for sessions, messages, and extension content."""

    async def upsert(
        self,
        *,
        entity_type: str,
        entity_id: str,
        text: str,
        session_id: str | None = None,
    ) -> None:
        selected_entity_type = _require_non_empty_text(entity_type, field="Entity type")
        selected_entity_id = _require_identifier(entity_id, field="Entity id")
        indexed_text = _require_non_empty_text(text, field="Search text")

        async def write(transaction: SqliteTransaction) -> None:
            await transaction.execute(
                "DELETE FROM search_fts WHERE entity_type = ? AND entity_id = ?",
                (selected_entity_type, selected_entity_id),
            )
            await transaction.execute(
                """
                INSERT INTO search_fts(entity_type, entity_id, session_id, text)
                VALUES (?, ?, ?, ?)
                """,
                (selected_entity_type, selected_entity_id, session_id, indexed_text),
            )

        await self.database.write(write)

    async def remove(self, entity_type: str, entity_id: str) -> int:
        selected_entity_type = _require_non_empty_text(entity_type, field="Entity type")
        selected_entity_id = _require_identifier(entity_id, field="Entity id")

        async def write(transaction: SqliteTransaction) -> int:
            count = await _count_rows(
                transaction,
                "SELECT COUNT(*) FROM search_fts WHERE entity_type = ? AND entity_id = ?",
                (selected_entity_type, selected_entity_id),
            )
            if count:
                await transaction.execute(
                    "DELETE FROM search_fts WHERE entity_type = ? AND entity_id = ?",
                    (selected_entity_type, selected_entity_id),
                )
            return count

        return await self.database.write(write)

    async def search(
        self,
        query: str,
        *,
        session_id: str | None = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        if limit <= 0:
            raise ValueError("Limit must be positive")
        normalized_query = query.strip()
        if not normalized_query:
            return []
        clauses = ["search_fts MATCH ?"]
        parameters: list[object] = [normalized_query]
        if session_id is not None:
            clauses.append("session_id = ?")
            parameters.append(session_id)
        where = " AND ".join(clauses)
        parameters.append(limit)

        async def read(reader: SqliteReader) -> list[SearchResult]:
            rows = await reader.fetch_all(
                f"""
                SELECT entity_type, entity_id, session_id, text, bm25(search_fts) AS rank
                FROM search_fts
                WHERE {where}
                ORDER BY rank, rowid
                LIMIT ?
                """,
                parameters,
            )
            return [_search_result_from_row(row) for row in rows]

        return await self.database.read(read)

    async def purge_missing_sessions(self) -> int:
        async def write(transaction: SqliteTransaction) -> int:
            count = await _count_rows(
                transaction,
                """
                SELECT COUNT(*) FROM search_fts
                WHERE session_id IS NOT NULL
                  AND NOT EXISTS(
                    SELECT 1 FROM sessions WHERE sessions.session_id = search_fts.session_id
                  )
                """,
                (),
            )
            if count:
                await transaction.execute(
                    """
                    DELETE FROM search_fts
                    WHERE session_id IS NOT NULL
                      AND NOT EXISTS(
                        SELECT 1 FROM sessions
                        WHERE sessions.session_id = search_fts.session_id
                      )
                    """,
                    (),
                )
            return count

        return await self.database.write(write)


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


async def _count_rows(
    transaction: SqliteTransaction,
    sql: str,
    parameters: Sequence[object],
) -> int:
    row = await transaction.fetch_one(sql, parameters)
    if row is None:
        raise RuntimeError("SQLite count query did not return a row")
    return int(row[0])


def _append_in_clause(
    clauses: list[str],
    parameters: list[object],
    column: str,
    values: Sequence[str],
) -> None:
    placeholders = ", ".join("?" for _ in values)
    clauses.append(f"{column} IN ({placeholders})")
    parameters.extend(values)


def _require_identifier(value: str, *, field: str) -> str:
    if not value:
        raise ValueError(f"{field} must not be empty")
    return value


def _require_non_empty_text(value: str, *, field: str) -> str:
    selected = value.strip()
    if not selected:
        raise ValueError(f"{field} must not be empty")
    return selected


def _require_non_negative(value: int, *, field: str) -> None:
    if value < 0:
        raise ValueError(f"{field} must not be negative")


def _validate_run_status(value: str) -> RunStatus:
    if value not in _RUN_STATUSES:
        raise ValueError(f"Unsupported run status: {value}")
    return cast(RunStatus, value)


def _validate_queue_kind(value: str) -> QueueKind:
    if value not in _QUEUE_KINDS:
        raise ValueError(f"Unsupported queue kind: {value}")
    return cast(QueueKind, value)


def _validate_delivery_mode(value: str) -> DeliveryMode:
    if value not in _DELIVERY_MODES:
        raise ValueError(f"Unsupported delivery mode: {value}")
    return cast(DeliveryMode, value)


def _validate_delivery_status(value: str) -> DeliveryStatus:
    if value not in _DELIVERY_STATUSES:
        raise ValueError(f"Unsupported delivery status: {value}")
    return cast(DeliveryStatus, value)


def _validate_extension_scope(value: str) -> ExtensionScope:
    if value not in _EXTENSION_SCOPES:
        raise ValueError(f"Unsupported extension scope: {value}")
    return cast(ExtensionScope, value)


def _dump_json(value: JSONValue) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _dump_optional_json(value: JSONValue | None) -> str | None:
    return None if value is None else _dump_json(value)


def _dump_optional_object(value: JSONObject | None) -> str | None:
    return None if value is None else _dump_json(value)


def _load_json_value(raw: object) -> JSONValue:
    return cast(JSONValue, json.loads(str(raw)))


def _load_json_object(raw: object) -> JSONObject:
    value = _load_json_value(raw)
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise RuntimeError("SQLite JSON value is not an object")
    return value


def _load_string_tuple(raw: object) -> tuple[str, ...]:
    value = _load_json_value(raw)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RuntimeError("SQLite JSON value is not a string list")
    return tuple(cast(list[str], value))


def _plan_from_row(row: Row) -> PlanRecord:
    return PlanRecord(
        session_id=str(row["session_id"]),
        markdown=str(row["markdown"]),
        explanation=str(row["explanation"]) if row["explanation"] is not None else None,
        revision=int(row["revision"]),
        updated_at=str(row["updated_at"]),
        updated_by=str(row["updated_by"]),
    )


def _run_from_row(row: Row) -> RunRecord:
    return RunRecord(
        run_id=str(row["run_id"]),
        session_id=str(row["session_id"]),
        status=_validate_run_status(str(row["status"])),
        started_at=str(row["started_at"]),
        updated_at=str(row["updated_at"]),
        ended_at=str(row["ended_at"]) if row["ended_at"] is not None else None,
        last_event_type=(
            str(row["last_event_type"]) if row["last_event_type"] is not None else None
        ),
        last_status=(
            _load_json_value(row["last_status_json"])
            if row["last_status_json"] is not None
            else None
        ),
        error=_load_json_object(row["error_json"]) if row["error_json"] is not None else None,
    )


def _queue_from_row(row: Row) -> QueueMessageRecord:
    return QueueMessageRecord(
        queue_id=str(row["queue_id"]),
        session_id=str(row["session_id"]),
        queue_kind=_validate_queue_kind(str(row["queue_kind"])),
        position=int(row["position"]),
        content=_load_json_value(row["content_json"]),
        source_session_id=(
            str(row["source_session_id"]) if row["source_session_id"] is not None else None
        ),
        created_at=str(row["created_at"]),
        consumed_at=str(row["consumed_at"]) if row["consumed_at"] is not None else None,
    )


def _delivery_from_row(row: Row) -> DeliveryRecord:
    return DeliveryRecord(
        delivery_id=str(row["delivery_id"]),
        transport=str(row["transport"]),
        source_session_id=str(row["source_session_id"]),
        target_session_id=(
            str(row["target_session_id"]) if row["target_session_id"] is not None else None
        ),
        target_address=(str(row["target_address"]) if row["target_address"] is not None else None),
        mode=_validate_delivery_mode(str(row["mode"])),
        content=str(row["content"]),
        idempotency_key=(
            str(row["idempotency_key"]) if row["idempotency_key"] is not None else None
        ),
        in_reply_to=str(row["in_reply_to"]) if row["in_reply_to"] is not None else None,
        ancestry=_load_string_tuple(row["ancestry_json"]),
        hop_count=int(row["hop_count"]),
        status=_validate_delivery_status(str(row["status"])),
        created_at=str(row["created_at"]),
        accepted_at=str(row["accepted_at"]) if row["accepted_at"] is not None else None,
        completed_at=(str(row["completed_at"]) if row["completed_at"] is not None else None),
        error=_load_json_object(row["error_json"]) if row["error_json"] is not None else None,
    )


def _usage_from_row(row: Row) -> UsageRecord:
    return UsageRecord(
        usage_id=int(row["usage_id"]),
        session_id=str(row["session_id"]),
        run_id=str(row["run_id"]) if row["run_id"] is not None else None,
        provider_name=str(row["provider_name"]),
        model=str(row["model"]),
        input_tokens=int(row["input_tokens"]),
        output_tokens=int(row["output_tokens"]),
        cached_input_tokens=int(row["cached_input_tokens"]),
        cost_microunits=(
            int(row["cost_microunits"]) if row["cost_microunits"] is not None else None
        ),
        details=_load_json_object(row["details_json"]),
        recorded_at=str(row["recorded_at"]),
    )


def _media_blob_from_row(row: Row) -> MediaBlobRecord:
    raw_content = row["content"]
    content = raw_content if isinstance(raw_content, bytes) else bytes(raw_content)
    return MediaBlobRecord(
        blob_id=str(row["blob_id"]),
        sha256=str(row["sha256"]),
        content=content,
        byte_length=int(row["byte_length"]),
        created_at=str(row["created_at"]),
    )


def _media_item_from_row(row: Row) -> MediaItemRecord:
    return MediaItemRecord(
        media_id=str(row["media_id"]),
        session_id=str(row["session_id"]) if row["session_id"] is not None else None,
        blob_id=str(row["blob_id"]),
        thumbnail_blob_id=(
            str(row["thumbnail_blob_id"]) if row["thumbnail_blob_id"] is not None else None
        ),
        filename=str(row["filename"]),
        media_type=str(row["media_type"]),
        width=int(row["width"]) if row["width"] is not None else None,
        height=int(row["height"]) if row["height"] is not None else None,
        metadata=_load_json_object(row["metadata_json"]),
        created_at=str(row["created_at"]),
        deleted_at=str(row["deleted_at"]) if row["deleted_at"] is not None else None,
    )


def _media_reference_from_row(row: Row) -> MediaReferenceRecord:
    return MediaReferenceRecord(
        media_id=str(row["media_id"]),
        reference_type=str(row["reference_type"]),
        reference_id=str(row["reference_id"]),
        created_at=str(row["created_at"]),
    )


def _extension_state_from_row(row: Row) -> ExtensionStateRecord:
    return ExtensionStateRecord(
        extension_id=str(row["extension_id"]),
        scope=_validate_extension_scope(str(row["scope"])),
        scope_id=str(row["scope_id"]),
        key=str(row["key"]),
        value=_load_json_value(row["value_json"]),
        revision=int(row["revision"]),
        updated_at=str(row["updated_at"]),
    )


def _audit_from_row(row: Row) -> AuditRecord:
    return AuditRecord(
        audit_id=int(row["audit_id"]),
        event_type=str(row["event_type"]),
        actor_type=str(row["actor_type"]),
        actor_id=str(row["actor_id"]) if row["actor_id"] is not None else None,
        workspace_id=(str(row["workspace_id"]) if row["workspace_id"] is not None else None),
        session_id=str(row["session_id"]) if row["session_id"] is not None else None,
        extension_id=(str(row["extension_id"]) if row["extension_id"] is not None else None),
        request_id=str(row["request_id"]) if row["request_id"] is not None else None,
        details=_load_json_object(row["details_json"]),
        created_at=str(row["created_at"]),
    )


def _search_result_from_row(row: Row) -> SearchResult:
    return SearchResult(
        entity_type=str(row["entity_type"]),
        entity_id=str(row["entity_id"]),
        session_id=str(row["session_id"]) if row["session_id"] is not None else None,
        text=str(row["text"]),
        rank=float(row["rank"]),
    )
