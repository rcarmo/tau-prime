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
