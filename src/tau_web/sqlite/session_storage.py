"""Tau append-only session storage implemented on the shared SQLite store."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from tau_agent.session import LeafEntry, SessionEntry, SessionTreeError, path_to_entry
from tau_agent.session.jsonl import entry_from_json_line, entry_to_json_line
from tau_web.sqlite.connection import SqliteDatabase, SqliteReader
from tau_web.sqlite.writer import SqliteTransaction


class SqliteSessionStorageError(RuntimeError):
    """Raised when persisted entry-tree invariants are violated."""


class SqliteSessionStorage:
    """Implement Tau's ``SessionStorage`` protocol for one durable session."""

    def __init__(self, database: SqliteDatabase, session_id: str) -> None:
        if not session_id:
            raise ValueError("Session id must not be empty")
        self.database = database
        self.session_id = session_id

    async def append(self, entry: SessionEntry) -> None:
        await self.append_many((entry,))

    async def append_many(self, entries: Sequence[SessionEntry]) -> None:
        """Append entries in order and atomically apply the final leaf pointer."""
        if not entries:
            return
        entry_ids = [entry.id for entry in entries]
        if len(set(entry_ids)) != len(entry_ids):
            raise SqliteSessionStorageError("Append batch contains duplicate entry ids")
        timestamp = datetime.now(UTC).isoformat()

        async def write(transaction: SqliteTransaction) -> None:
            session = await transaction.fetch_one(
                "SELECT session_id FROM sessions WHERE session_id = ?",
                (self.session_id,),
            )
            if session is None:
                raise SqliteSessionStorageError(f"Unknown session: {self.session_id}")
            row = await transaction.fetch_one(
                """
                SELECT COALESCE(MAX(ordinal), -1) + 1 AS next_ordinal
                FROM session_entries
                WHERE session_id = ?
                """,
                (self.session_id,),
            )
            if row is None:
                raise SqliteSessionStorageError("Could not allocate session entry ordinal")
            next_ordinal = int(row["next_ordinal"])
            leaf_changed = False
            active_leaf: str | None = None

            for offset, entry in enumerate(entries):
                await _validate_entry_reference(transaction, self.session_id, entry.parent_id)
                if isinstance(entry, LeafEntry):
                    await _validate_entry_reference(transaction, self.session_id, entry.entry_id)
                    leaf_changed = True
                    active_leaf = entry.entry_id
                await transaction.execute(
                    """
                    INSERT INTO session_entries(
                        entry_id, session_id, parent_entry_id, entry_type,
                        timestamp, ordinal, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.id,
                        self.session_id,
                        entry.parent_id,
                        entry.type,
                        entry.timestamp,
                        next_ordinal + offset,
                        entry_to_json_line(entry).strip(),
                    ),
                )

            if not leaf_changed:
                await transaction.execute(
                    "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                    (timestamp, self.session_id),
                )
            else:
                await transaction.execute(
                    """
                    UPDATE sessions
                    SET active_leaf_entry_id = ?, updated_at = ?
                    WHERE session_id = ?
                    """,
                    (active_leaf, timestamp, self.session_id),
                )

        await self.database.write(write)

    async def read_all(self) -> list[SessionEntry]:
        async def read(reader: SqliteReader) -> list[SessionEntry]:
            rows = await reader.fetch_all(
                """
                SELECT entry_id, parent_entry_id, entry_type, timestamp, ordinal, payload_json
                FROM session_entries
                WHERE session_id = ?
                ORDER BY ordinal
                """,
                (self.session_id,),
            )
            entries: list[SessionEntry] = []
            for expected_ordinal, row in enumerate(rows):
                if int(row["ordinal"]) != expected_ordinal:
                    raise SqliteSessionStorageError(
                        f"Session {self.session_id} has a non-contiguous entry ordinal"
                    )
                entry = entry_from_json_line(str(row["payload_json"]))
                if (
                    entry.id != str(row["entry_id"])
                    or entry.parent_id != row["parent_entry_id"]
                    or entry.type != str(row["entry_type"])
                    or entry.timestamp != float(row["timestamp"])
                ):
                    raise SqliteSessionStorageError(
                        f"Session entry columns disagree with payload: {entry.id}"
                    )
                entries.append(entry)
            return entries

        return await self.database.read(read)

    async def read_path(self, leaf_entry_id: str) -> list[SessionEntry]:
        """Return the root-to-leaf path using Tau's canonical tree semantics."""
        entries = await self.read_all()
        try:
            return path_to_entry(entries, leaf_entry_id)
        except SessionTreeError as exc:
            raise SqliteSessionStorageError(str(exc)) from exc


async def _validate_entry_reference(
    transaction: SqliteTransaction,
    session_id: str,
    entry_id: str | None,
) -> None:
    if entry_id is None:
        return
    row = await transaction.fetch_one(
        "SELECT session_id FROM session_entries WHERE entry_id = ?",
        (entry_id,),
    )
    if row is None:
        raise SqliteSessionStorageError(f"Entry reference does not exist: {entry_id}")
    if str(row["session_id"]) != session_id:
        raise SqliteSessionStorageError(
            f"Entry reference belongs to another session: {entry_id}"
        )
