from __future__ import annotations

from pathlib import Path

import pytest

from tau_agent import UserMessage
from tau_coding.agent_pool import AsyncAgentPool
from tau_web.runtime import DurableAgentRuntime
from tau_web.sqlite.connection import SqliteDatabase
from tau_web.sqlite.repositories import (
    AuditRepository,
    MediaRepository,
    QueueRepository,
    RunRepository,
)
from tau_web.sqlite.sessions import SessionRepository


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class _RecordingSession:
    def __init__(self) -> None:
        self.prompts: list[str | UserMessage] = []

    async def prompt(self, content: str | UserMessage, *, streaming_behavior=None):
        del streaming_behavior
        self.prompts.append(content)
        if False:
            yield

    async def continue_(self):
        if False:
            yield

    async def queue_message(self, content, *, behavior):
        raise AssertionError((content, behavior))

    def cancel(self) -> None:
        return None

    async def aclose(self) -> None:
        return None


@pytest.mark.anyio
async def test_runtime_hydrates_media_markers_without_persisting_blob_bytes(tmp_path: Path) -> None:
    database = SqliteDatabase(tmp_path / "tau.sqlite3")
    await database.open()
    session_id = "media-session"
    await SessionRepository(database).create(
        workspace_root=tmp_path,
        provider_name="test",
        model="model",
        agent_name=session_id,
        session_id=session_id,
    )
    media = MediaRepository(database)
    blob = await media.store_blob(b"png")
    item = await media.create_item(
        blob_id=blob.blob_id,
        filename="pixel.png",
        media_type="image/png",
        session_id=session_id,
    )
    pool = AsyncAgentPool(max_concurrency=1)
    runtime = DurableAgentRuntime(
        pool,
        RunRepository(database),
        QueueRepository(database),
        AuditRepository(database),
        media=media,
    )
    recording = _RecordingSession()
    runtime.register_session(session_id, recording)

    try:
        handle = await runtime.submit_prompt(
            session_id,
            f"describe it\n\n[media:{item.media_id}] pixel.png (image/png)",
        )
        completed = await handle.wait()
        assert completed.status == "completed"
        assert len(recording.prompts) == 1
        prompt = recording.prompts[0]
        assert isinstance(prompt, UserMessage)
        assert prompt.attachments[0].data == b"png"
        assert prompt.model_dump()["attachments"][0] == {
            "media_id": item.media_id,
            "filename": "pixel.png",
            "media_type": "image/png",
            "size_bytes": 3,
        }
        references = await media.list_references(item.media_id)
        assert [(reference.reference_type, reference.reference_id) for reference in references] == [
            ("session", session_id)
        ]
    finally:
        await runtime.shutdown()
        await database.close()
