"""Helpers for polymorphic live coding-session managers."""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterator, Awaitable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast

from tau_agent.session import JsonlSessionStorage, SessionStorage
from tau_coding.session_manager import CodingSessionRecord, SessionManager
from tau_coding.sqlite_session_manager import SqliteCodingSessionManager, SqliteCodingSessionRecord

type CodingSessionManager = SessionManager | SqliteCodingSessionManager
type CodingSessionRecordLike = CodingSessionRecord | SqliteCodingSessionRecord


async def manager_result[T](result: T | Awaitable[T]) -> T:
    """Await sync-or-async manager results behind one call shape."""
    if inspect.isawaitable(result):
        return await cast(Awaitable[T], result)
    return result


def _manager_supports_parameter(manager_call: object, parameter_name: str) -> bool:
    """Return whether a manager call accepts one keyword parameter."""
    try:
        signature = inspect.signature(manager_call)
    except (TypeError, ValueError):
        return True
    return any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD or parameter.name == parameter_name
        for parameter in signature.parameters.values()
    )


async def manager_list_sessions(
    manager: CodingSessionManager,
    cwd: Path | None = None,
) -> list[CodingSessionRecordLike]:
    """Return session records from sync or async managers."""
    list_sessions = manager.list_sessions
    if cwd is None or not _manager_supports_parameter(list_sessions, "cwd"):
        return list(await manager_result(list_sessions()))
    return list(await manager_result(list_sessions(cwd)))


async def manager_get_session(
    manager: CodingSessionManager,
    session_id: str,
) -> CodingSessionRecordLike | None:
    """Return one session record from sync or async managers."""
    return await manager_result(manager.get_session(session_id))


async def manager_prepare_session(
    manager: CodingSessionManager,
    *,
    cwd: Path,
    model: str,
    provider_name: str,
    title: str | None = None,
    session_id: str | None = None,
) -> CodingSessionRecordLike:
    """Prepare one unpersisted session record from sync or async managers."""
    kwargs: dict[str, str | Path | None] = {
        "cwd": cwd,
        "model": model,
        "title": title,
        "session_id": session_id,
    }
    if _manager_supports_parameter(manager.prepare_session, "provider_name"):
        kwargs["provider_name"] = provider_name
    return await manager_result(manager.prepare_session(**kwargs))


async def manager_create_session(
    manager: CodingSessionManager,
    *,
    cwd: Path,
    model: str,
    provider_name: str,
    title: str | None = None,
    session_id: str | None = None,
) -> CodingSessionRecordLike:
    """Create one persisted session record from sync or async managers."""
    kwargs: dict[str, str | Path | None] = {
        "cwd": cwd,
        "model": model,
        "title": title,
        "session_id": session_id,
    }
    if _manager_supports_parameter(manager.create_session, "provider_name"):
        kwargs["provider_name"] = provider_name
    return await manager_result(manager.create_session(**kwargs))


async def manager_create_session_exclusive(
    manager: CodingSessionManager,
    *,
    cwd: Path,
    model: str,
    provider_name: str,
    title: str | None = None,
    session_id: str | None = None,
) -> CodingSessionRecordLike:
    """Create one persisted session with exclusive transcript semantics when supported."""
    create_session_exclusive = getattr(manager, "create_session_exclusive", None)
    if create_session_exclusive is None:
        return await manager_create_session(
            manager,
            cwd=cwd,
            model=model,
            provider_name=provider_name,
            title=title,
            session_id=session_id,
        )
    kwargs: dict[str, str | Path | None] = {
        "cwd": cwd,
        "model": model,
        "title": title,
        "session_id": session_id,
    }
    if _manager_supports_parameter(create_session_exclusive, "provider_name"):
        kwargs["provider_name"] = provider_name
    return await manager_result(create_session_exclusive(**kwargs))


async def manager_touch_session(
    manager: CodingSessionManager,
    session_id: str,
    *,
    model: str | None = None,
    provider_name: str | None = None,
    title: str | None = None,
) -> CodingSessionRecordLike | None:
    """Update one session record from sync or async managers."""
    kwargs: dict[str, str | None] = {
        "model": model,
        "title": title,
    }
    if _manager_supports_parameter(manager.touch_session, "provider_name"):
        kwargs["provider_name"] = provider_name
    return await manager_result(manager.touch_session(session_id, **kwargs))


def session_storage_for_record(
    manager: CodingSessionManager,
    record: CodingSessionRecordLike,
) -> SessionStorage:
    """Return the durable storage backing one record."""
    if isinstance(record, SqliteCodingSessionRecord):
        if not isinstance(manager, SqliteCodingSessionManager):
            raise RuntimeError(f"SQLite session record requires a SQLite manager: {record.id}")
        return manager.session_storage(record.id)
    return JsonlSessionStorage(record.path)


def manager_session_storage(
    manager: CodingSessionManager,
    record: CodingSessionRecordLike,
) -> SessionStorage:
    """Return the durable storage backing one manager-owned record."""
    return session_storage_for_record(manager, record)


@asynccontextmanager
async def live_session_manager_context(
    session_manager: CodingSessionManager | None = None,
) -> AsyncIterator[CodingSessionManager]:
    """Yield the injected live manager or own one default SQLite manager."""
    if session_manager is not None:
        yield session_manager
        return

    manager = SqliteCodingSessionManager()
    await manager.open()
    try:
        yield manager
    finally:
        await manager.close()
