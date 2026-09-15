from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from typing import cast

import pytest
from aiohttp import FormData, web
from aiohttp.test_utils import TestClient, TestServer
from PIL import Image

from tau_web.app import SERVICES_KEY, create_app
from tau_web.config import WebConfig
from tau_web.services import TauWebServices


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def _start_client(app: web.Application) -> TestClient:
    client = TestClient(TestServer(app))
    await client.start_server()
    return client


def _services(client: TestClient) -> TauWebServices:
    return cast(TauWebServices, client.app[SERVICES_KEY])


async def _create_session(client: TestClient, session_id: str) -> str:
    record = await _services(client).sessions.create(
        workspace_root=_services(client).config.cwd,
        provider_name="test",
        model="base",
        agent_name=session_id,
        session_id=session_id,
        thinking_level="low",
    )
    return record.session_id


async def _upload_media(
    client: TestClient,
    *,
    content: bytes,
    filename: str,
    media_type: str,
    session_id: str | None = None,
):
    form = FormData()
    form.add_field("file", content, filename=filename, content_type=media_type)
    if session_id is not None:
        form.add_field("session_id", session_id)
    return await client.post("/api/media", data=form)


@pytest.mark.anyio
async def test_file_route_lists_directories_first_and_reads_text_file(
    web_config: WebConfig,
) -> None:
    workspace = web_config.cwd / "workspace"
    workspace.mkdir()
    (workspace / "z-dir").mkdir()
    (workspace / "b-dir").mkdir()
    (workspace / "a.txt").write_text("alpha", encoding="utf-8")
    (workspace / "c.txt").write_text("charlie", encoding="utf-8")

    client = await _start_client(create_app(web_config))
    try:
        listing = await client.get("/api/files", params={"path": "workspace"})
        assert listing.status == 200
        payload = await listing.json()

        assert payload["kind"] == "directory"
        assert payload["path"] == "workspace"
        assert [entry["name"] for entry in payload["entries"]] == [
            "b-dir",
            "z-dir",
            "a.txt",
            "c.txt",
        ]
        assert [entry["kind"] for entry in payload["entries"]] == [
            "directory",
            "directory",
            "file",
            "file",
        ]

        file_response = await client.get("/api/files", params={"path": "workspace/c.txt"})
        assert file_response.status == 200
        assert await file_response.json() == {
            "kind": "file",
            "path": "workspace/c.txt",
            "encoding": "utf-8",
            "content": "charlie",
        }
    finally:
        await client.close()


@pytest.mark.anyio
async def test_file_route_rejects_missing_parent_escape_symlink_escape_and_binary(
    web_config: WebConfig,
) -> None:
    outside = web_config.cwd.parent / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("secret", encoding="utf-8")
    (web_config.cwd / "escape-link").symlink_to(outside, target_is_directory=True)
    (web_config.cwd / "image.bin").write_bytes(b"\x00\x01tau")

    client = await _start_client(create_app(web_config))
    try:
        missing = await client.get("/api/files", params={"path": "missing.txt"})
        assert missing.status == 404
        assert (await missing.json())["error"]["message"] == "Unknown file path: missing.txt"

        traversal = await client.get("/api/files", params={"path": "../outside/secret.txt"})
        assert traversal.status == 403
        assert (await traversal.json())["error"]["message"] == "Path escapes the working directory."

        symlink = await client.get("/api/files", params={"path": "escape-link/secret.txt"})
        assert symlink.status == 403
        assert (await symlink.json())["error"]["message"] == "Symlinks are not accessible."

        binary = await client.get("/api/files", params={"path": "image.bin"})
        assert binary.status == 415
        assert (await binary.json())["error"]["message"] == "Binary files are not accessible."
    finally:
        await client.close()


@pytest.mark.anyio
async def test_file_route_enforces_configured_max_size(web_config: WebConfig) -> None:
    (web_config.cwd / "large.txt").write_text("12345", encoding="utf-8")

    client = await _start_client(create_app(replace(web_config, max_request_bytes=4)))
    try:
        response = await client.get("/api/files", params={"path": "large.txt"})
        assert response.status == 413
        payload = await response.json()
        assert payload["error"]["code"] == "request_entity_too_large"
    finally:
        await client.close()


@pytest.mark.anyio
async def test_media_upload_dedupes_blobs_and_lists_by_session(web_config: WebConfig) -> None:
    client = await _start_client(create_app(web_config))
    try:
        first_session = await _create_session(client, "session-one")
        second_session = await _create_session(client, "session-two")

        first_upload = await _upload_media(
            client,
            content=b"same bytes",
            filename="first.txt",
            media_type="text/plain",
            session_id=first_session,
        )
        assert first_upload.status == 201
        first = await first_upload.json()

        second_upload = await _upload_media(
            client,
            content=b"same bytes",
            filename="second.txt",
            media_type="text/plain",
            session_id=second_session,
        )
        assert second_upload.status == 201
        second = await second_upload.json()

        assert first["blob_id"] == second["blob_id"]
        assert first["media_id"] != second["media_id"]
        assert first["session_id"] == first_session
        assert second["session_id"] == second_session

        first_list = await client.get("/api/media", params={"session_id": first_session})
        second_list = await client.get("/api/media", params={"session_id": second_session})
        all_media = await client.get("/api/media")

        assert [item["media_id"] for item in (await first_list.json())["media"]] == [
            first["media_id"]
        ]
        assert [item["media_id"] for item in (await second_list.json())["media"]] == [
            second["media_id"]
        ]
        assert {item["media_id"] for item in (await all_media.json())["media"]} == {
            first["media_id"],
            second["media_id"],
        }
    finally:
        await client.close()


@pytest.mark.anyio
async def test_media_routes_return_metadata_download_headers_and_deleted_not_found(
    web_config: WebConfig,
) -> None:
    client = await _start_client(create_app(web_config))
    try:
        upload = await _upload_media(
            client,
            content=b"hello world",
            filename="hello world.txt",
            media_type="text/plain",
        )
        assert upload.status == 201
        created = await upload.json()

        metadata = await client.get(f"/api/media/{created['media_id']}")
        assert metadata.status == 200
        metadata_payload = await metadata.json()
        assert metadata_payload["media_id"] == created["media_id"]
        assert metadata_payload["metadata"] == {}
        assert "content" not in metadata_payload

        content = await client.get(f"/api/media/{created['media_id']}/content")
        assert content.status == 200
        assert await content.read() == b"hello world"
        assert content.content_type == "text/plain"
        assert content.headers["Content-Disposition"] == (
            "inline; filename=\"hello world.txt\"; filename*=UTF-8''hello%20world.txt"
        )
        expected_etag = f'"{sha256(b"hello world").hexdigest()}"'
        assert content.headers["ETag"] == expected_etag

        not_modified = await client.get(
            f"/api/media/{created['media_id']}/content",
            headers={"If-None-Match": expected_etag},
        )
        assert not_modified.status == 304
        assert not_modified.headers["ETag"] == expected_etag

        deleted = await client.delete(f"/api/media/{created['media_id']}")
        assert deleted.status == 200
        deleted_payload = await deleted.json()
        assert deleted_payload["deleted_at"] is not None

        deleted_metadata = await client.get(f"/api/media/{created['media_id']}")
        assert deleted_metadata.status == 404
        assert (await client.get(f"/api/media/{created['media_id']}/content")).status == 404

        live_list = await client.get("/api/media")
        assert (await live_list.json())["media"] == []

        deleted_list = await client.get("/api/media", params={"include_deleted": "true"})
        assert [item["media_id"] for item in (await deleted_list.json())["media"]] == [
            created["media_id"]
        ]
    finally:
        await client.close()


@pytest.mark.anyio
async def test_image_upload_records_dimensions_and_serves_png_thumbnail(
    web_config: WebConfig,
) -> None:
    source = BytesIO()
    Image.new("RGB", (800, 400), color=(30, 120, 200)).save(source, format="PNG")

    client = await _start_client(create_app(web_config))
    try:
        session_id = await _create_session(client, "image-session")
        upload = await _upload_media(
            client,
            content=source.getvalue(),
            filename="wide.png",
            media_type="image/png",
            session_id=session_id,
        )
        assert upload.status == 201
        created = await upload.json()
        assert created["width"] == 800
        assert created["height"] == 400
        assert created["thumbnail_blob_id"]
        assert created["reference_count"] == 1
        assert created["content_url"] == f"/api/media/{created['media_id']}/content"
        assert created["thumbnail_url"] == f"/api/media/{created['media_id']}/thumbnail"
        assert created["metadata"] == {
            "animated": False,
            "frame_count": 1,
            "thumbnail_height": 256,
            "thumbnail_media_type": "image/png",
            "thumbnail_width": 512,
        }

        thumbnail = await client.get(f"/api/media/{created['media_id']}/thumbnail")
        assert thumbnail.status == 200
        assert thumbnail.content_type == "image/png"
        with Image.open(BytesIO(await thumbnail.read())) as preview:
            assert preview.size == (512, 256)

        references = await _services(client).media.list_references(created["media_id"])
        assert [(reference.reference_type, reference.reference_id) for reference in references] == [
            ("session", session_id)
        ]
    finally:
        await client.close()


@pytest.mark.anyio
async def test_media_upload_enforces_session_item_and_byte_quotas(web_config: WebConfig) -> None:
    config = replace(
        web_config,
        max_media_items_per_session=1,
        max_media_bytes_per_session=5,
    )
    client = await _start_client(create_app(config))
    try:
        session_id = await _create_session(client, "quota-session")
        first = await _upload_media(
            client,
            content=b"1234",
            filename="first.txt",
            media_type="text/plain",
            session_id=session_id,
        )
        assert first.status == 201

        second = await _upload_media(
            client,
            content=b"x",
            filename="second.txt",
            media_type="text/plain",
            session_id=session_id,
        )
        assert second.status == 413
    finally:
        await client.close()


@pytest.mark.anyio
async def test_media_routes_validate_unknown_sessions_and_empty_upload(
    web_config: WebConfig,
) -> None:
    client = await _start_client(create_app(web_config))
    try:
        missing_list = await client.get("/api/media", params={"session_id": "missing"})
        assert missing_list.status == 404
        assert (await missing_list.json())["error"]["message"] == "Unknown session: missing"

        unknown_upload = await _upload_media(
            client,
            content=b"data",
            filename="note.txt",
            media_type="text/plain",
            session_id="missing",
        )
        assert unknown_upload.status == 404
        assert (await unknown_upload.json())["error"]["message"] == "Unknown session: missing"

        empty_upload = await _upload_media(
            client,
            content=b"",
            filename="empty.txt",
            media_type="text/plain",
        )
        assert empty_upload.status == 400
        assert (await empty_upload.json())["error"]["message"] == (
            "Media blob content must not be empty"
        )
    finally:
        await client.close()
