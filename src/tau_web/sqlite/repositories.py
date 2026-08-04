"""Repository boundaries and revisioned core records for Tau SQLite."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from tau_web.sqlite.connection import SqliteDatabase, SqliteReader
from tau_web.sqlite.writer import SqliteTransaction


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
            if row is None:
                return None
            return PlanRecord(
                session_id=str(row["session_id"]),
                markdown=str(row["markdown"]),
                explanation=(
                    str(row["explanation"]) if row["explanation"] is not None else None
                ),
                revision=int(row["revision"]),
                updated_at=str(row["updated_at"]),
                updated_by=str(row["updated_by"]),
            )

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
        timestamp = datetime.now(UTC).isoformat()

        async def write(transaction: SqliteTransaction) -> PlanRecord:
            row = await transaction.fetch_one(
                "SELECT revision FROM session_plans WHERE session_id = ?",
                (session_id,),
            )
            actual_revision = int(row["revision"]) if row is not None else None
            if actual_revision is None:
                if expected_revision not in (None, 0):
                    raise RevisionConflictError(
                        f"session_plan:{session_id}",
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
                    (session_id, markdown, explanation, revision, timestamp, updated_by),
                )
            else:
                if expected_revision != actual_revision:
                    raise RevisionConflictError(
                        f"session_plan:{session_id}",
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
                        updated_by,
                        session_id,
                        actual_revision,
                    ),
                )
                if changed != 1:
                    raise RevisionConflictError(
                        f"session_plan:{session_id}",
                        expected=expected_revision,
                        actual=None,
                    )
            return PlanRecord(
                session_id=session_id,
                markdown=markdown,
                explanation=explanation,
                revision=revision,
                updated_at=timestamp,
                updated_by=updated_by,
            )

        return await self.database.write(write)
