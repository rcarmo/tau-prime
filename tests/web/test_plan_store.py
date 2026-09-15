from __future__ import annotations

import json
from pathlib import Path

import pytest

from tau_coding.plan import PlanConflictError, PlanItem, PlanSnapshot, parse_plan_markdown
from tau_web.plan import SqlitePlanStore
from tau_web.sqlite.connection import SqliteDatabase
from tau_web.sqlite.repositories import PlanRepository
from tau_web.sqlite.writer import SqliteTransaction


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


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
async def test_sqlite_plan_store_round_trips_and_stores_valid_json(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        await _seed_session(database)
        repository = PlanRepository(database)
        store = SqlitePlanStore(repository)

        assert await store.get("session") is None

        created = await store.save(
            PlanSnapshot(
                session_id="session",
                items=(
                    PlanItem(step="inspect workspace"),
                    PlanItem(step="ship tests", status="completed"),
                ),
                updated_by="agent",
            ),
            expected_revision=0,
        )
        assert created.revision == 1

        record = await repository.get("session")
        assert record is not None
        payload = json.loads(record.markdown)
        assert payload == {
            "format": "tau.plan/v1",
            "items": [
                {"status": "pending", "step": "inspect workspace"},
                {"status": "completed", "step": "ship tests"},
            ],
            "markdown": "- [ ] inspect workspace\n- [x] ship tests",
        }

        updated = await store.save(
            PlanSnapshot(
                session_id="session",
                items=parse_plan_markdown("- [-] inspect workspace\n- [x] ship tests"),
                revision=created.revision,
                updated_by="assistant",
            ),
            expected_revision=created.revision,
        )
        assert updated.revision == 2
        assert await store.get("session") == updated


@pytest.mark.anyio
async def test_sqlite_plan_store_reads_plain_markdown_and_rejects_invalid_payload(
    tmp_path: Path,
) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        await _seed_session(database)
        repository = PlanRepository(database)
        store = SqlitePlanStore(repository)

        await repository.save(
            "session",
            markdown="- [ ] fallback\n- [x] done",
            explanation=None,
            updated_by="user",
            expected_revision=None,
        )
        fallback = await store.get("session")
        assert fallback is not None
        assert fallback.items == parse_plan_markdown("- [ ] fallback\n- [x] done")

        await repository.save(
            "session",
            markdown=json.dumps({"format": "tau.plan/v1", "items": "bad"}),
            explanation=None,
            updated_by="user",
            expected_revision=fallback.revision,
        )
        with pytest.raises(RuntimeError, match="not a valid plan payload"):
            await store.get("session")


@pytest.mark.anyio
async def test_sqlite_plan_store_translates_revision_conflicts(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        await _seed_session(database)
        store = SqlitePlanStore(PlanRepository(database))

        created = await store.save(
            PlanSnapshot(
                session_id="session",
                items=(PlanItem(step="first"),),
                updated_by="agent",
            ),
            expected_revision=0,
        )
        assert created.revision == 1

        with pytest.raises(PlanConflictError, match="expected 0, actual 1") as exc:
            await store.save(
                PlanSnapshot(
                    session_id="session",
                    items=(PlanItem(step="stale"),),
                    updated_by="agent",
                ),
                expected_revision=0,
            )

        assert exc.value.expected_revision == 0
        assert exc.value.actual_revision == 1


@pytest.mark.anyio
async def test_agent_plan_tool_and_browser_repository_share_revisions(tmp_path: Path) -> None:
    from tau_coding.plan import create_plan_tool

    database = SqliteDatabase(tmp_path / "tool-browser.sqlite3")
    await database.open()
    try:
        await _seed_session(database)
        repository = PlanRepository(database)
        changes: list[PlanSnapshot] = []
        tool = create_plan_tool(SqlitePlanStore(repository), "session", on_change=changes.append)
        written = await tool.execute({"action": "write", "markdown": "- [ ] Tool task"})
        assert written.ok
        record = await repository.get("session")
        assert record is not None
        assert record.revision == 1
        assert len(changes) == 1
        assert changes[0].revision == record.revision
        await repository.save(
            "session",
            markdown="- [x] Browser completed task",
            explanation=None,
            updated_by="browser",
            expected_revision=record.revision,
        )
        read = await tool.execute({"action": "read"})
        assert "Browser completed task" in read.content
        assert read.data is not None
        assert read.data["revision"] == 2
        with pytest.raises(PlanConflictError):
            await tool.execute(
                {"action": "write", "markdown": "- [ ] stale", "expected_revision": 1}
            )
        assert len(changes) == 1
    finally:
        await database.close()
