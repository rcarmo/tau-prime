from __future__ import annotations

from pathlib import Path

import pytest

from tau_agent import UserMessage
from tau_agent.session import MessageEntry, SessionInfoEntry
from tau_coding.paths import TauPaths
from tau_coding.sqlite_session_manager import SqliteCodingSessionManager


def _paths(tmp_path: Path) -> TauPaths:
    return TauPaths(home=tmp_path / ".tau", agents_home=tmp_path / ".agents")


@pytest.mark.anyio
async def test_sqlite_session_manager_lifecycle_and_prepare(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    manager = SqliteCodingSessionManager(paths=_paths(tmp_path))

    assert not manager.opened
    with pytest.raises(RuntimeError, match="not open"):
        await manager.list_sessions()

    await manager.open()
    assert manager.opened

    prepared = await manager.prepare_session(
        cwd=project,
        model="gpt-test",
        provider_name="provider",
        title="Prepared",
    )

    assert prepared.cwd == project.resolve()
    assert prepared.provider_name == "provider"
    assert await manager.get_session(prepared.id) is None
    assert await manager.list_sessions(project) == []

    await manager.close()
    assert not manager.opened


@pytest.mark.anyio
async def test_sqlite_session_manager_persists_across_reopen(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    project = tmp_path / "project"
    project.mkdir()

    async with SqliteCodingSessionManager(paths=paths) as manager:
        created = await manager.create_session(
            cwd=project,
            model="gpt-test",
            provider_name="provider",
            title="Saved",
            session_id="worker-499",
        )
        assert created.id == "worker-499"

    async with SqliteCodingSessionManager(paths=paths) as reopened:
        loaded = await reopened.get_session("worker-499")
        latest = await reopened.latest_session_for_cwd(project)

        assert loaded == created
        assert await reopened.list_sessions(project) == [created]
        assert latest == created


@pytest.mark.anyio
async def test_sqlite_session_manager_scopes_sessions_by_workspace(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    async with SqliteCodingSessionManager(paths=_paths(tmp_path)) as manager:
        first_record = await manager.create_session(
            cwd=first,
            model="model-a",
            provider_name="provider",
            title="First",
            session_id="worker-a",
        )
        second_record = await manager.create_session(
            cwd=second,
            model="model-b",
            provider_name="provider",
            title="Second",
            session_id="worker-b",
        )

        assert await manager.list_sessions(first) == [first_record]
        assert await manager.list_sessions(second) == [second_record]
        assert {record.id for record in await manager.list_sessions()} == {"worker-a", "worker-b"}


@pytest.mark.anyio
async def test_sqlite_session_manager_rejects_session_id_collisions(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    async with SqliteCodingSessionManager(paths=_paths(tmp_path)) as manager:
        await manager.create_session(
            cwd=project,
            model="gpt-test",
            provider_name="provider",
            session_id="worker-499",
        )

        with pytest.raises(RuntimeError, match="Session already exists"):
            await manager.create_session(
                cwd=project,
                model="gpt-test",
                provider_name="provider",
                session_id="worker-499",
            )


@pytest.mark.anyio
async def test_sqlite_session_manager_touch_updates_metadata_and_ordering(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    async with SqliteCodingSessionManager(paths=_paths(tmp_path)) as manager:
        older = await manager.create_session(
            cwd=project,
            model="older-model",
            provider_name="provider",
            session_id="older",
        )
        newer = await manager.create_session(
            cwd=project,
            model="newer-model",
            provider_name="provider",
            session_id="newer",
        )

        updated = await manager.touch_session(
            older.id,
            model="updated-model",
            provider_name="updated-provider",
            title="Updated",
        )

        assert updated is not None
        assert updated.id == older.id
        assert updated.model == "updated-model"
        assert updated.provider_name == "updated-provider"
        assert updated.title == "Updated"
        assert updated.updated_at >= older.updated_at
        assert await manager.latest_session_for_cwd(project) == updated
        assert [record.id for record in await manager.list_sessions(project)] == ["older", "newer"]
        assert newer in await manager.list_sessions(project)
        assert await manager.touch_session("missing") is None


@pytest.mark.anyio
async def test_sqlite_session_manager_storage_round_trip(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    async with SqliteCodingSessionManager(paths=_paths(tmp_path)) as manager:
        created = await manager.create_session(
            cwd=project,
            model="gpt-test",
            provider_name="provider",
            session_id="worker-storage",
        )
        storage = manager.session_storage(created.id)
        info = SessionInfoEntry(id="info", cwd=str(project.resolve()), title="Storage")
        message = MessageEntry(
            id="message",
            parent_id="info",
            message=UserMessage(content="hello"),
        )

        assert storage.session_id == created.id

        await storage.append(info)
        await storage.append(message)

        assert await storage.read_all() == [info, message]
