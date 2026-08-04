"""Validated Tau JSONL interchange for SQLite-backed sessions."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from tau_agent.session import LeafEntry, SessionEntry
from tau_agent.session.jsonl import entries_from_json_lines, entry_to_json_line
from tau_agent.types import JSONValue
from tau_web.sqlite.connection import SqliteDatabase, SqliteReader
from tau_web.sqlite.session_storage import SqliteSessionStorage
from tau_web.sqlite.sessions import (
    AgentNameConflictError,
    validate_agent_name,
    workspace_id_for_path,
)
from tau_web.sqlite.writer import SqliteTransaction


class SessionInterchangeError(RuntimeError):
    """Raised when a session cannot be safely imported or exported."""


@dataclass(frozen=True, slots=True)
class JsonlImportOptions:
    workspace_root: Path
    provider_name: str
    model: str
    session_id: str | None = None
    agent_name: str | None = None
    title: str | None = None
    thinking_level: str | None = None
    metadata: dict[str, JSONValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SessionImportResult:
    session_id: str
    agent_name: str
    entry_count: int
    workspace_id: str


class SessionInterchange:
    """Import and export Tau JSONL without making it a live sidecar store."""

    def __init__(self, database: SqliteDatabase) -> None:
        self.database = database

    def parse_jsonl(self, text: str) -> list[SessionEntry]:
        try:
            entries = entries_from_json_lines(text.splitlines())
        except ValueError as exc:
            raise SessionInterchangeError(str(exc)) from exc
        if not entries:
            raise SessionInterchangeError("Session JSONL contains no entries")
        validate_entry_sequence(entries)
        return entries

    async def import_jsonl(
        self,
        text: str,
        *,
        options: JsonlImportOptions,
    ) -> SessionImportResult:
        """Validate and import one complete JSONL session in one transaction."""
        entries = self.parse_jsonl(text)
        session_id = options.session_id or uuid4().hex
        if not session_id:
            raise SessionInterchangeError("Session id must not be empty")
        provider_name = options.provider_name.strip()
        model = options.model.strip()
        if not provider_name or not model:
            raise SessionInterchangeError("Provider name and model must not be empty")
        requested_name = (
            validate_agent_name(options.agent_name) if options.agent_name is not None else None
        )
        workspace_root = options.workspace_root.expanduser().resolve()
        workspace_id = workspace_id_for_path(workspace_root)
        timestamp = datetime.now(UTC).isoformat()
        metadata = dict(options.metadata)
        metadata.setdefault("interchange_format", "tau-jsonl")
        metadata_json = json.dumps(metadata, separators=(",", ":"), sort_keys=True)
        storage = SqliteSessionStorage(self.database, session_id)

        async def write(transaction: SqliteTransaction) -> SessionImportResult:
            existing = await transaction.fetch_one(
                "SELECT 1 FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            if existing is not None:
                raise SessionInterchangeError(f"Session already exists: {session_id}")
            for entry in entries:
                collision = await transaction.fetch_one(
                    "SELECT session_id FROM session_entries WHERE entry_id = ?",
                    (entry.id,),
                )
                if collision is not None:
                    raise SessionInterchangeError(
                        f"Entry id already belongs to another session: {entry.id}"
                    )
            await transaction.execute(
                """
                INSERT INTO workspaces(workspace_id, root_path, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(root_path) DO UPDATE SET updated_at = excluded.updated_at
                """,
                (workspace_id, str(workspace_root), timestamp, timestamp),
            )
            agent_name = requested_name
            if agent_name is None:
                agent_name = await _allocate_agent_name(transaction, "default")
            elif await _agent_name_exists(transaction, agent_name):
                raise AgentNameConflictError(f"Active agent name already exists: @{agent_name}")
            await transaction.execute(
                """
                INSERT INTO sessions(
                    session_id, workspace_id, agent_name, title, provider_name, model,
                    thinking_level, created_at, updated_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    workspace_id,
                    agent_name,
                    options.title,
                    provider_name,
                    model,
                    options.thinking_level,
                    timestamp,
                    timestamp,
                    metadata_json,
                ),
            )
            await storage.append_many_in_transaction(transaction, entries)
            return SessionImportResult(
                session_id=session_id,
                agent_name=agent_name,
                entry_count=len(entries),
                workspace_id=workspace_id,
            )

        return await self.database.write(write)

    async def import_jsonl_file(
        self,
        source: Path,
        *,
        options: JsonlImportOptions,
    ) -> SessionImportResult:
        text = await asyncio.to_thread(source.read_text, encoding="utf-8")
        metadata = dict(options.metadata)
        metadata.setdefault("source_path", str(source.expanduser().resolve()))
        return await self.import_jsonl(
            text,
            options=JsonlImportOptions(
                workspace_root=options.workspace_root,
                provider_name=options.provider_name,
                model=options.model,
                session_id=options.session_id,
                agent_name=options.agent_name,
                title=options.title,
                thinking_level=options.thinking_level,
                metadata=metadata,
            ),
        )

    async def export_jsonl(self, session_id: str) -> str:
        session = await _session_exists(self.database, session_id)
        if not session:
            raise SessionInterchangeError(f"Unknown session: {session_id}")
        entries = await SqliteSessionStorage(self.database, session_id).read_all()
        return "".join(entry_to_json_line(entry) for entry in entries)

    async def export_jsonl_file(
        self,
        session_id: str,
        destination: Path,
        *,
        overwrite: bool = False,
    ) -> Path:
        text = await self.export_jsonl(session_id)
        resolved = destination.expanduser().resolve()
        await asyncio.to_thread(_write_private_file, resolved, text, overwrite)
        return resolved


def validate_entry_sequence(entries: list[SessionEntry]) -> None:
    """Validate append order and references before opening a write transaction."""
    seen: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        if entry.id in seen:
            raise SessionInterchangeError(
                f"Duplicate session entry id at import position {index}: {entry.id}"
            )
        if entry.parent_id is not None and entry.parent_id not in seen:
            raise SessionInterchangeError(
                f"Entry {entry.id} refers to a parent that was not imported earlier: "
                f"{entry.parent_id}"
            )
        if (
            isinstance(entry, LeafEntry)
            and entry.entry_id is not None
            and entry.entry_id not in seen
        ):
            raise SessionInterchangeError(
                f"Leaf entry {entry.id} refers to an unavailable entry: {entry.entry_id}"
            )
        seen.add(entry.id)


async def _session_exists(database: SqliteDatabase, session_id: str) -> bool:
    async def read(reader: SqliteReader) -> bool:
        return (
            await reader.fetch_one(
                "SELECT 1 FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            is not None
        )

    return await database.read(read)


async def _agent_name_exists(transaction: SqliteTransaction, agent_name: str) -> bool:
    row = await transaction.fetch_one(
        """
        SELECT 1 FROM sessions
        WHERE agent_name = ? COLLATE NOCASE AND archived_at IS NULL
        """,
        (agent_name,),
    )
    return row is not None


async def _allocate_agent_name(transaction: SqliteTransaction, base: str) -> str:
    suffix = 1
    while True:
        candidate = base if suffix == 1 else f"{base}-{suffix}"
        if not await _agent_name_exists(transaction, candidate):
            return candidate
        suffix += 1


def _write_private_file(path: Path, text: str, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise SessionInterchangeError(f"Export destination already exists: {path}")
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as file:
            file.write(text)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        temporary.unlink(missing_ok=True)
