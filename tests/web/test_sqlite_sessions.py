from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from tau_web.sqlite.connection import SqliteDatabase
from tau_web.sqlite.repositories import RecordNotFoundError, RepositoryError
from tau_web.sqlite.sessions import (
    AgentNameConflictError,
    InvalidAgentNameError,
    SessionRepository,
    validate_agent_name,
    workspace_id_for_path,
)


def test_agent_name_validation() -> None:
    assert validate_agent_name("@Review_2") == "Review_2"

    for invalid in ("", "@", "-bad", "bad name", "bad/name", "x" * 129):
        with pytest.raises(InvalidAgentNameError):
            validate_agent_name(invalid)


@pytest.mark.anyio
async def test_workspace_identity_is_stable(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        sessions = SessionRepository(database)
        first = await sessions.ensure_workspace(tmp_path / "project")
        second = await sessions.ensure_workspace(tmp_path / "project" / ".." / "project")

        assert first.workspace_id == workspace_id_for_path(tmp_path / "project")
        assert second.workspace_id == first.workspace_id
        assert second.root_path == (tmp_path / "project").resolve()


@pytest.mark.anyio
async def test_session_creation_allocates_unique_default_names(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        sessions = SessionRepository(database)

        created = await asyncio.gather(
            *(
                sessions.create(
                    workspace_root=tmp_path,
                    provider_name="test",
                    model="model",
                )
                for _ in range(3)
            )
        )

        assert [record.agent_name for record in created] == ["default", "default-2", "default-3"]
        assert len({record.session_id for record in created}) == 3


@pytest.mark.anyio
async def test_explicit_agent_names_are_case_insensitively_unique(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        sessions = SessionRepository(database)
        await sessions.create(
            workspace_root=tmp_path,
            provider_name="test",
            model="model",
            agent_name="Review",
        )

        with pytest.raises(AgentNameConflictError):
            await sessions.create(
                workspace_root=tmp_path,
                provider_name="test",
                model="model",
                agent_name="review",
            )


@pytest.mark.anyio
async def test_rename_archive_restore_and_alias_reallocation(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        sessions = SessionRepository(database)
        first = await sessions.create(
            workspace_root=tmp_path,
            provider_name="test",
            model="model",
            agent_name="first",
        )
        renamed = await sessions.rename(first.session_id, "worker")
        archived = await sessions.archive(first.session_id)
        replacement = await sessions.create(
            workspace_root=tmp_path,
            provider_name="test",
            model="model",
            agent_name="worker",
        )
        restored = await sessions.restore(first.session_id)

        assert renamed.agent_name == "worker"
        assert archived.archived_at is not None
        assert replacement.agent_name == "worker"
        assert restored.archived_at is None
        assert restored.agent_name == "worker-2"

        with pytest.raises(AgentNameConflictError):
            await sessions.restore(first.session_id, agent_name="worker")


@pytest.mark.anyio
async def test_archived_session_cannot_be_renamed(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        sessions = SessionRepository(database)
        created = await sessions.create(
            workspace_root=tmp_path,
            provider_name="test",
            model="model",
        )
        await sessions.archive(created.session_id)

        with pytest.raises(RepositoryError, match="restored"):
            await sessions.rename(created.session_id, "renamed")

        with pytest.raises(RecordNotFoundError):
            await sessions.archive("missing")


@pytest.mark.anyio
async def test_session_address_resolution_and_archived_filter(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        sessions = SessionRepository(database)
        created = await sessions.create(
            workspace_root=tmp_path,
            provider_name="test",
            model="model",
            agent_name="Worker",
            metadata={"chat_jid": "web:worker", "source_id": 42},
        )

        assert await sessions.resolve("@worker") == created
        assert await sessions.resolve(f"session:{created.session_id}") == created
        assert await sessions.resolve(created.session_id) == created
        assert await sessions.resolve("chat_jid:web:worker") == created
        assert await sessions.resolve("@missing") is None

        archived = await sessions.archive(created.session_id)
        assert await sessions.resolve("@worker") is None
        assert await sessions.resolve("@worker", include_archived=True) == archived
        assert await sessions.list() == []
        assert await sessions.list(include_archived=True) == [archived]
