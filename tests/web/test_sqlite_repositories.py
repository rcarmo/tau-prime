from __future__ import annotations

from pathlib import Path

import pytest

from tau_web.sqlite.connection import SqliteDatabase
from tau_web.sqlite.repositories import PlanRepository, RevisionConflictError
from tau_web.sqlite.writer import SqliteTransaction


async def _seed_session(database: SqliteDatabase) -> None:
    async def seed(transaction: SqliteTransaction) -> None:
        await transaction.execute(
            """
            INSERT INTO workspaces(workspace_id, root_path, created_at, updated_at)
            VALUES ('workspace', '/workspace', 'now', 'now')
            """
        )
        await transaction.execute(
            """
            INSERT INTO sessions(
                session_id, workspace_id, agent_name, provider_name, model,
                created_at, updated_at
            ) VALUES ('session', 'workspace', 'default', 'test', 'model', 'now', 'now')
            """
        )

    await database.write(seed)


@pytest.mark.anyio
async def test_plan_repository_uses_optimistic_revisions(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        await _seed_session(database)
        plans = PlanRepository(database)

        created = await plans.save(
            "session",
            markdown="- [ ] first",
            explanation=None,
            updated_by="user",
            expected_revision=None,
        )
        updated = await plans.save(
            "session",
            markdown="- [x] first",
            explanation="done",
            updated_by="agent",
            expected_revision=created.revision,
        )

        assert created.revision == 1
        assert updated.revision == 2
        assert await plans.get("session") == updated


@pytest.mark.anyio
async def test_plan_repository_rejects_stale_and_blind_updates(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        await _seed_session(database)
        plans = PlanRepository(database)
        await plans.save(
            "session",
            markdown="initial",
            explanation=None,
            updated_by="user",
            expected_revision=0,
        )

        with pytest.raises(RevisionConflictError) as blind:
            await plans.save(
                "session",
                markdown="blind",
                explanation=None,
                updated_by="user",
                expected_revision=None,
            )
        assert blind.value.actual == 1

        with pytest.raises(RevisionConflictError) as stale:
            await plans.save(
                "session",
                markdown="stale",
                explanation=None,
                updated_by="agent",
                expected_revision=0,
            )
        assert stale.value.expected == 0
        assert stale.value.actual == 1
