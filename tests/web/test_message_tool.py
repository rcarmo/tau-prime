from pathlib import Path

import pytest

from tau_agent import UserMessage
from tau_web.message_tool import create_message_tool
from tau_web.sqlite.connection import SqliteDatabase
from tau_web.sqlite.repositories import TimelineMessageRepository
from tau_web.sqlite.sessions import SessionRepository


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_message_tool_reads_only_current_session(tmp_path: Path) -> None:
    db = SqliteDatabase(tmp_path / "messages.sqlite3")
    await db.open()
    try:
        sessions = SessionRepository(db)
        for name in ["one", "two"]:
            await sessions.create(
                workspace_root=tmp_path, provider_name="test", model="test", session_id=name
            )
        repo = TimelineMessageRepository(db)
        first = await repo.project_message_end(
            session_id="one",
            run_id="run",
            sequence=1,
            message=UserMessage(content="café " + "x" * 16000),
            created_at="2026-09-14T00:00:00Z",
        )
        tool = create_message_tool(repo, "one")
        result = await tool.execute({"message_id": first.message_id})
        assert result.ok
        assert "café" in result.content
        assert result.data["truncated"] is True
        rest = await tool.execute({"message_id": first.message_id, "offset": 16000})
        assert rest.data["truncated"] is False
        with pytest.raises(ValueError, match="not found"):
            await create_message_tool(repo, "two").execute({"message_id": first.message_id})
    finally:
        await db.close()


@pytest.mark.anyio
async def test_message_tool_reads_multiple_ids_with_context_and_reports_missing(
    tmp_path: Path,
) -> None:
    db = SqliteDatabase(tmp_path / "messages.sqlite3")
    await db.open()
    try:
        await SessionRepository(db).create(
            workspace_root=tmp_path, provider_name="test", model="test", session_id="one"
        )
        repo = TimelineMessageRepository(db)
        records = []
        for sequence in range(1, 7):
            records.append(
                await repo.project_message_end(
                    session_id="one",
                    run_id="run",
                    sequence=sequence,
                    message=UserMessage(content=f"message {sequence}"),
                    created_at=f"2026-09-14T00:00:0{sequence}Z",
                )
            )

        missing_id = records[-1].message_id + 100
        result = await create_message_tool(repo, "one").execute(
            {
                "row_ids": [records[1].message_id, records[4].message_id, missing_id],
                "context_before": 1,
                "context_after": 1,
            }
        )

        assert result.ok
        assert result.data["missing_row_ids"] == [missing_id]
        assert result.data["count"] == 6
        assert [f"message {sequence}" in result.content for sequence in range(1, 7)] == [True] * 6
        assert result.content.index("message 1") < result.content.index("message 6")
    finally:
        await db.close()


@pytest.mark.anyio
async def test_message_tool_applies_bounded_row_windows_and_session_scope(tmp_path: Path) -> None:
    db = SqliteDatabase(tmp_path / "messages.sqlite3")
    await db.open()
    try:
        sessions = SessionRepository(db)
        for name in ["one", "two"]:
            await sessions.create(
                workspace_root=tmp_path, provider_name="test", model="test", session_id=name
            )
        repo = TimelineMessageRepository(db)
        records = []
        for sequence in range(1, 6):
            records.append(
                await repo.project_message_end(
                    session_id="one",
                    run_id="run-one",
                    sequence=sequence,
                    message=UserMessage(content=f"one {sequence}"),
                    created_at=f"2026-09-14T00:00:0{sequence}Z",
                )
            )
        foreign = await repo.project_message_end(
            session_id="two",
            run_id="run-two",
            sequence=1,
            message=UserMessage(content="foreign"),
            created_at="2026-09-14T00:01:00Z",
        )
        tool = create_message_tool(repo, "one")

        after = await tool.execute({"after_row": records[0].message_id, "limit": 2})
        assert "one 1" not in after.content
        assert "one 4" in after.content and "one 5" in after.content
        assert "one 3" not in after.content

        before = await tool.execute({"before_row": records[4].message_id, "limit": 2})
        assert "one 3" in before.content and "one 4" in before.content
        assert "one 2" not in before.content
        assert "foreign" not in before.content

        missing = await tool.execute({"row_ids": [foreign.message_id]})
        assert missing.data["missing_row_ids"] == [foreign.message_id]
        assert "foreign" not in missing.content
    finally:
        await db.close()


@pytest.mark.anyio
async def test_message_tool_validates_ranges_and_limits(tmp_path: Path) -> None:
    db = SqliteDatabase(tmp_path / "messages.sqlite3")
    await db.open()
    try:
        await SessionRepository(db).create(
            workspace_root=tmp_path, provider_name="test", model="test", session_id="one"
        )
        tool = create_message_tool(TimelineMessageRepository(db), "one")

        with pytest.raises(ValueError, match="between 1 and 50"):
            await tool.execute({"row_ids": list(range(1, 52))})
        with pytest.raises(ValueError, match="at most 50"):
            await tool.execute({"after_row": 1, "limit": 51})
        with pytest.raises(ValueError, match="cannot be combined"):
            await tool.execute({"row_ids": [1], "after_row": 1})
        with pytest.raises(ValueError, match="precede"):
            await tool.execute({"after_row": 4, "before_row": 2})
    finally:
        await db.close()
