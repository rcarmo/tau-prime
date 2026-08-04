from __future__ import annotations

from pathlib import Path

import pytest

import tau_coding.live_session_manager as live_session_manager_module
from tau_agent.session import JsonlSessionStorage
from tau_coding.live_session_manager import (
    live_session_manager_context,
    manager_create_session,
    manager_create_session_exclusive,
    manager_list_sessions,
    manager_prepare_session,
    manager_touch_session,
    session_storage_for_record,
)
from tau_coding.paths import TauPaths
from tau_coding.session_manager import CodingSessionRecord, SessionManager
from tau_coding.sqlite_session_manager import SqliteCodingSessionManager


def _paths(tmp_path: Path) -> TauPaths:
    return TauPaths(home=tmp_path / ".tau", agents_home=tmp_path / ".agents")


class _LegacyManager:
    def __init__(self, record: CodingSessionRecord) -> None:
        self.record = record
        self.calls: list[tuple[object, ...]] = []
        self.close_calls = 0

    def list_sessions(self) -> list[CodingSessionRecord]:
        self.calls.append(("list_sessions",))
        return [self.record]

    def get_session(self, session_id: str) -> CodingSessionRecord | None:
        self.calls.append(("get_session", session_id))
        return self.record if session_id == self.record.id else None

    def prepare_session(
        self,
        *,
        cwd: Path,
        model: str,
        title: str | None = None,
        session_id: str | None = None,
    ) -> CodingSessionRecord:
        self.calls.append(("prepare_session", cwd, model, title, session_id))
        return self.record

    def create_session(
        self,
        *,
        cwd: Path,
        model: str,
        title: str | None = None,
        session_id: str | None = None,
    ) -> CodingSessionRecord:
        self.calls.append(("create_session", cwd, model, title, session_id))
        return self.record

    def touch_session(
        self,
        session_id: str,
        *,
        model: str | None = None,
        title: str | None = None,
    ) -> CodingSessionRecord | None:
        self.calls.append(("touch_session", session_id, model, title))
        return self.record if session_id == self.record.id else None

    async def close(self) -> None:
        self.close_calls += 1


class _AsyncExclusiveLegacyManager(_LegacyManager):
    async def create_session_exclusive(
        self,
        *,
        cwd: Path,
        model: str,
        title: str | None = None,
        session_id: str | None = None,
    ) -> CodingSessionRecord:
        self.calls.append(("create_session_exclusive", cwd, model, title, session_id))
        return self.record


@pytest.mark.anyio
async def test_live_session_manager_context_owns_and_closes_default_sqlite_manager(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[object] = []

    class FakeSqliteManager:
        def __init__(self) -> None:
            self.open_calls = 0
            self.close_calls = 0
            self.opened = False
            created.append(self)

        async def open(self) -> None:
            self.open_calls += 1
            self.opened = True

        async def close(self) -> None:
            self.close_calls += 1
            self.opened = False

    monkeypatch.setattr(
        live_session_manager_module,
        "SqliteCodingSessionManager",
        FakeSqliteManager,
    )

    async with live_session_manager_context() as manager:
        assert isinstance(manager, FakeSqliteManager)
        assert manager.opened is True
        assert manager.open_calls == 1
        assert manager.close_calls == 0

    owned = created[0]
    assert isinstance(owned, FakeSqliteManager)
    assert owned.opened is False
    assert owned.close_calls == 1


@pytest.mark.anyio
async def test_live_session_manager_context_does_not_close_injected_legacy_manager(
    tmp_path: Path,
) -> None:
    record = CodingSessionRecord(
        id="legacy-session",
        path=tmp_path / "legacy.jsonl",
        cwd=tmp_path,
        model="fake-model",
        title="Legacy",
        created_at=1.0,
        updated_at=1.0,
    )
    manager = _LegacyManager(record)

    async with live_session_manager_context(manager) as yielded:
        assert yielded is manager

    assert manager.close_calls == 0


@pytest.mark.anyio
async def test_live_session_manager_storage_dispatches_by_record_type(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    legacy_manager = SessionManager(_paths(tmp_path / "legacy"))
    legacy_record = legacy_manager.prepare_session(
        cwd=project,
        model="fake-model",
        provider_name="legacy-provider",
        session_id="legacy-session",
    )
    legacy_storage = session_storage_for_record(legacy_manager, legacy_record)

    assert isinstance(legacy_storage, JsonlSessionStorage)
    assert legacy_storage.path == legacy_record.path

    async with SqliteCodingSessionManager(paths=_paths(tmp_path / "sqlite")) as sqlite_manager:
        sqlite_record = await sqlite_manager.create_session(
            cwd=project,
            model="fake-model",
            provider_name="sqlite-provider",
            session_id="sqlite-session",
        )
        sqlite_storage = session_storage_for_record(sqlite_manager, sqlite_record)

        assert type(sqlite_storage).__name__ == "SqliteSessionStorage"
        assert sqlite_storage.session_id == sqlite_record.id


@pytest.mark.anyio
async def test_live_session_manager_create_session_exclusive_supports_awaitable_legacy_manager(
    tmp_path: Path,
) -> None:
    record = CodingSessionRecord(
        id="legacy-session",
        path=tmp_path / "legacy.jsonl",
        cwd=tmp_path,
        model="fake-model",
        title="Legacy",
        created_at=1.0,
        updated_at=1.0,
    )
    manager = _AsyncExclusiveLegacyManager(record)

    created = await manager_create_session_exclusive(
        manager,
        cwd=tmp_path,
        model="fake-model",
        provider_name="legacy-provider",
        title="Created",
        session_id="created-session",
    )

    assert created == record
    assert manager.calls == [
        ("create_session_exclusive", tmp_path, "fake-model", "Created", "created-session")
    ]


@pytest.mark.anyio
async def test_live_session_manager_helpers_support_legacy_manager_signatures(
    tmp_path: Path,
) -> None:
    record = CodingSessionRecord(
        id="legacy-session",
        path=tmp_path / "legacy.jsonl",
        cwd=tmp_path,
        model="fake-model",
        title="Legacy",
        created_at=1.0,
        updated_at=1.0,
    )
    manager = _LegacyManager(record)

    listed = await manager_list_sessions(manager, cwd=tmp_path)
    prepared = await manager_prepare_session(
        manager,
        cwd=tmp_path,
        model="fake-model",
        provider_name="legacy-provider",
        title="Prepared",
        session_id="prepared-session",
    )
    created = await manager_create_session(
        manager,
        cwd=tmp_path,
        model="fake-model",
        provider_name="legacy-provider",
        title="Created",
        session_id="created-session",
    )
    touched = await manager_touch_session(
        manager,
        record.id,
        model="updated-model",
        provider_name="legacy-provider",
        title="Updated",
    )

    assert listed == [record]
    assert prepared == record
    assert created == record
    assert touched == record
    assert manager.calls == [
        ("list_sessions",),
        ("prepare_session", tmp_path, "fake-model", "Prepared", "prepared-session"),
        ("create_session", tmp_path, "fake-model", "Created", "created-session"),
        ("touch_session", record.id, "updated-model", "Updated"),
    ]
