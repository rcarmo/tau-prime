from __future__ import annotations

from pathlib import Path

import pytest

from tau_web.media_tools import create_attachment_tool
from tau_web.sqlite.connection import SqliteDatabase
from tau_web.sqlite.repositories import MediaRepository
from tau_web.sqlite.sessions import SessionRepository


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_attachment_tool_lists_and_reads_only_session_media(tmp_path: Path) -> None:
    database = SqliteDatabase(tmp_path / "tau.sqlite3")
    await database.open()
    sessions = SessionRepository(database)
    for session_id in ("alpha", "beta"):
        await sessions.create(
            workspace_root=tmp_path,
            provider_name="test",
            model="model",
            agent_name=session_id,
            session_id=session_id,
        )
    media = MediaRepository(database)
    own_blob = await media.store_blob(b"hello attachment")
    own = await media.create_item(
        blob_id=own_blob.blob_id,
        filename="notes.txt",
        media_type="text/plain",
        session_id="alpha",
    )
    other_blob = await media.store_blob(b"private")
    other = await media.create_item(
        blob_id=other_blob.blob_id,
        filename="private.txt",
        media_type="text/plain",
        session_id="beta",
    )
    tool = create_attachment_tool(media, "alpha")

    try:
        listing = await tool.execute({"action": "list"})
        assert listing.ok is True
        assert own.media_id in listing.content
        assert other.media_id not in listing.content

        read = await tool.execute({"action": "read", "media_id": own.media_id})
        assert read.ok is True
        assert read.content == "hello attachment"
        assert read.data == {
            "media_id": own.media_id,
            "filename": "notes.txt",
            "media_type": "text/plain",
            "bytes": 16,
        }

        denied = await tool.execute({"action": "read", "media_id": other.media_id})
        assert denied.ok is False
        assert denied.error == f"Unknown attachment: {other.media_id}"
    finally:
        await database.close()
