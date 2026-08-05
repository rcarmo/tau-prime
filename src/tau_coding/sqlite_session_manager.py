"""Shared SQLite-backed coding-session manager boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import time
from typing import TYPE_CHECKING, cast
from uuid import uuid4

from tau_agent.session import SessionStorage
from tau_coding.paths import TauPaths
from tau_coding.session_manager import validate_session_id

_SQLITE_SUPPORT_MESSAGE = "Install 'tau-prime[web]' to use SQLite coding sessions"

if TYPE_CHECKING:
    from aiosqlite import Row

    from tau_coding.coding_session_factory import ExtraToolsFactory, TurnContextProviderFactory
    from tau_web.sqlite.connection import SqliteDatabase, SqliteReader
    from tau_web.sqlite.session_storage import SqliteSessionStorage
    from tau_web.sqlite.sessions import SessionRepository


@dataclass(frozen=True, slots=True)
class SqliteCodingSessionRecord:
    """Durable coding-session metadata loaded from the shared SQLite store."""

    id: str
    cwd: Path
    model: str
    provider_name: str
    title: str | None
    created_at: float
    updated_at: float


class SqliteCodingSessionManager:
    """Async coding-session service backed solely by the shared SQLite store."""

    def __init__(
        self,
        paths: TauPaths | None = None,
        *,
        database_path: Path | None = None,
        database: object | None = None,
        manage_database_lifecycle: bool | None = None,
    ) -> None:
        self.paths = paths or TauPaths()
        default_database_path = (database_path or self.paths.home / "tau.sqlite3").expanduser()
        self._database_path = default_database_path.resolve()
        self._database = database
        self._manage_database_lifecycle = (
            database is None if manage_database_lifecycle is None else manage_database_lifecycle
        )
        if database is not None:
            raw_path = getattr(database, "path", self._database_path)
            self._database_path = Path(cast(str | Path, raw_path)).expanduser().resolve()
        self._opened = False

    @property
    def database_path(self) -> Path:
        """Return the shared SQLite database path."""
        return self._database_path

    @property
    def opened(self) -> bool:
        """Return whether this manager is ready for use."""
        return self._opened

    async def open(self) -> None:
        """Open the shared SQLite database when this manager owns its lifecycle."""
        if self._opened:
            return
        if self._database is None:
            self._database = _create_database(self._database_path)
        database = self._database_instance()
        if self._manage_database_lifecycle:
            await database.open()
        elif not database.opened:
            raise RuntimeError("Shared SQLite database must be open before use")
        self._opened = True

    async def close(self) -> None:
        """Close the shared SQLite database when this manager owns its lifecycle."""
        if not self._opened:
            return
        database = self._database_instance()
        self._opened = False
        if self._manage_database_lifecycle:
            await database.close()

    async def __aenter__(self) -> SqliteCodingSessionManager:
        await self.open()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    def plan_factory_hooks(self) -> tuple[ExtraToolsFactory, TurnContextProviderFactory]:
        """Return plan-tool and turn-context hooks for this open SQLite manager."""
        from tau_web.plan import create_plan_factory_hooks
        from tau_web.sqlite.repositories import PlanRepository

        return create_plan_factory_hooks(PlanRepository(self._database_instance()))

    async def list_sessions(self, cwd: Path | None = None) -> list[SqliteCodingSessionRecord]:
        """Return active sessions, newest updated first."""
        if cwd is None:
            query = (
                "SELECT s.session_id, w.root_path, s.model, s.provider_name, "
                "s.title, s.created_at, s.updated_at "
                "FROM sessions AS s "
                "JOIN workspaces AS w ON w.workspace_id = s.workspace_id "
                "WHERE s.archived_at IS NULL "
                "ORDER BY s.updated_at DESC, s.session_id"
            )
            parameters: tuple[object, ...] = ()
        else:
            query = (
                "SELECT s.session_id, w.root_path, s.model, s.provider_name, "
                "s.title, s.created_at, s.updated_at "
                "FROM sessions AS s "
                "JOIN workspaces AS w ON w.workspace_id = s.workspace_id "
                "WHERE s.archived_at IS NULL AND s.workspace_id = ? "
                "ORDER BY s.updated_at DESC, s.session_id"
            )
            parameters = (_workspace_id_for_path(cwd),)

        async def read(reader: SqliteReader) -> list[SqliteCodingSessionRecord]:
            rows = await reader.fetch_all(query, parameters)
            return [_record_from_row(row) for row in rows]

        return await self._require_database().read(read)

    async def get_session(self, session_id: str) -> SqliteCodingSessionRecord | None:
        """Return one active session by id, if present."""

        async def read(reader: SqliteReader) -> SqliteCodingSessionRecord | None:
            row = await reader.fetch_one(
                """
                SELECT s.session_id, w.root_path, s.model, s.provider_name,
                       s.title, s.created_at, s.updated_at
                FROM sessions AS s
                JOIN workspaces AS w ON w.workspace_id = s.workspace_id
                WHERE s.session_id = ? AND s.archived_at IS NULL
                """,
                (session_id,),
            )
            return _record_from_row(row) if row is not None else None

        return await self._require_database().read(read)

    async def latest_session_for_cwd(self, cwd: Path) -> SqliteCodingSessionRecord | None:
        """Return the most recently updated active session for one workspace."""
        records = await self.list_sessions(cwd)
        return records[0] if records else None

    async def prepare_session(
        self,
        *,
        cwd: Path,
        model: str,
        provider_name: str,
        title: str | None = None,
        session_id: str | None = None,
    ) -> SqliteCodingSessionRecord:
        """Return validated session metadata without persisting it."""
        normalized_model = model.strip()
        if not normalized_model:
            raise ValueError("Model must not be empty")
        normalized_provider_name = provider_name.strip()
        if not normalized_provider_name:
            raise ValueError("Provider name must not be empty")
        resolved_cwd = cwd.expanduser().resolve()

        if session_id is not None:
            validate_session_id(session_id)
            existing = await self.get_session(session_id)
            if existing is not None:
                raise RuntimeError(f"Session already exists with id '{session_id}'")
            record_id = session_id
        else:
            record_id = await self._new_session_id()

        now = time()
        return SqliteCodingSessionRecord(
            id=record_id,
            cwd=resolved_cwd,
            model=normalized_model,
            provider_name=normalized_provider_name,
            title=title,
            created_at=now,
            updated_at=now,
        )

    async def create_session(
        self,
        *,
        cwd: Path,
        model: str,
        provider_name: str,
        title: str | None = None,
        session_id: str | None = None,
    ) -> SqliteCodingSessionRecord:
        """Create a durable coding-session record in SQLite."""
        prepared = await self.prepare_session(
            cwd=cwd,
            model=model,
            provider_name=provider_name,
            title=title,
            session_id=session_id,
        )
        repository = _create_session_repository(self._require_database())
        try:
            await repository.create(
                workspace_root=prepared.cwd,
                provider_name=prepared.provider_name,
                model=prepared.model,
                title=prepared.title,
                session_id=prepared.id,
            )
        except Exception as exc:
            if await self.get_session(prepared.id) is not None:
                raise RuntimeError(f"Session already exists with id '{prepared.id}'") from exc
            raise
        created = await self.get_session(prepared.id)
        if created is None:
            raise RuntimeError(f"Created session could not be reloaded: {prepared.id}")
        return created

    async def touch_session(
        self,
        session_id: str,
        *,
        model: str | None = None,
        provider_name: str | None = None,
        title: str | None = None,
    ) -> SqliteCodingSessionRecord | None:
        """Update a session's mutable metadata and last-used timestamp."""
        repository = _create_session_repository(self._require_database())
        try:
            await repository.update_metadata(
                session_id,
                provider_name=provider_name,
                model=model,
                title=title,
            )
        except Exception as exc:
            record_not_found_error = _record_not_found_error_type()
            if isinstance(exc, record_not_found_error):
                return None
            raise
        return await self.get_session(session_id)

    def session_storage(self, session_id: str) -> SessionStorage:
        """Return the SQLite-backed session storage for one session id."""
        return _create_session_storage(self._require_database(), session_id)

    async def _new_session_id(self) -> str:
        for _ in range(8):
            candidate = uuid4().hex
            if await self.get_session(candidate) is None:
                return candidate
        raise RuntimeError("Could not allocate a unique session id")

    def _require_database(self) -> SqliteDatabase:
        if not self._opened:
            raise RuntimeError("SQLite coding-session manager is not open")
        return self._database_instance()

    def _database_instance(self) -> SqliteDatabase:
        if self._database is None:
            raise RuntimeError("SQLite coding-session manager has no database")
        return cast("SqliteDatabase", self._database)


def _record_from_row(row: Row) -> SqliteCodingSessionRecord:
    return SqliteCodingSessionRecord(
        id=str(row["session_id"]),
        cwd=Path(str(row["root_path"])),
        model=str(row["model"]),
        provider_name=str(row["provider_name"]),
        title=str(row["title"]) if row["title"] is not None else None,
        created_at=datetime.fromisoformat(str(row["created_at"])).timestamp(),
        updated_at=datetime.fromisoformat(str(row["updated_at"])).timestamp(),
    )


def _create_database(path: Path) -> SqliteDatabase:
    try:
        from tau_web.sqlite.connection import SqliteDatabase
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised without web extras
        raise RuntimeError(_SQLITE_SUPPORT_MESSAGE) from exc
    return SqliteDatabase(path)


def _create_session_repository(database: SqliteDatabase) -> SessionRepository:
    try:
        from tau_web.sqlite.sessions import SessionRepository
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised without web extras
        raise RuntimeError(_SQLITE_SUPPORT_MESSAGE) from exc
    return SessionRepository(database)


def _create_session_storage(database: SqliteDatabase, session_id: str) -> SqliteSessionStorage:
    try:
        from tau_web.sqlite.session_storage import SqliteSessionStorage
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised without web extras
        raise RuntimeError(_SQLITE_SUPPORT_MESSAGE) from exc
    return SqliteSessionStorage(database, session_id)


def _record_not_found_error_type() -> type[Exception]:
    try:
        from tau_web.sqlite.repositories import RecordNotFoundError
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised without web extras
        raise RuntimeError(_SQLITE_SUPPORT_MESSAGE) from exc
    return RecordNotFoundError


def _workspace_id_for_path(cwd: Path) -> str:
    try:
        from tau_web.sqlite.sessions import workspace_id_for_path
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised without web extras
        raise RuntimeError(_SQLITE_SUPPORT_MESSAGE) from exc
    return workspace_id_for_path(cwd.expanduser().resolve())
