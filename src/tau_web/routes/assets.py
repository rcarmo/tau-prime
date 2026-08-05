"""Workspace file browsing and media asset REST routes."""

from __future__ import annotations

import stat
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote

from aiohttp import web
from aiohttp.multipart import BodyPartReader, MultipartReader
from PIL import Image, ImageOps, UnidentifiedImageError

from tau_agent.types import JSONObject
from tau_web.routes.common import (
    config_for,
    json_response,
    parse_bool,
    raise_for_repository_error,
    record_response,
    require_found,
    services_for,
)
from tau_web.services import TauWebServices
from tau_web.sqlite.repositories import MediaItemRecord
from tau_web.sqlite.sessions import SessionRecord


@dataclass(frozen=True, slots=True)
class FileEntry:
    name: str
    path: str
    kind: str


@dataclass(frozen=True, slots=True)
class DirectoryResource:
    kind: str
    path: str
    entries: tuple[FileEntry, ...]


@dataclass(frozen=True, slots=True)
class TextFileResource:
    kind: str
    path: str
    encoding: str
    content: str


@dataclass(frozen=True, slots=True)
class MediaItemResource:
    media_id: str
    session_id: str | None
    blob_id: str
    thumbnail_blob_id: str | None
    filename: str
    media_type: str
    width: int | None
    height: int | None
    metadata: JSONObject
    reference_count: int
    content_url: str
    thumbnail_url: str | None
    created_at: str
    deleted_at: str | None


@dataclass(frozen=True, slots=True)
class MediaListResource:
    media: tuple[MediaItemResource, ...]


@dataclass(frozen=True, slots=True)
class _ImagePreview:
    width: int
    height: int
    thumbnail_content: bytes
    metadata: dict[str, str | int | bool]


def setup_routes(app: web.Application) -> None:
    app.router.add_get("/api/files", get_file_or_directory)
    app.router.add_get("/api/media", list_media)
    app.router.add_post("/api/media", upload_media)
    app.router.add_get("/api/media/{media_id}", get_media_item)
    app.router.add_get("/api/media/{media_id}/content", get_media_content)
    app.router.add_get("/api/media/{media_id}/thumbnail", get_media_thumbnail)
    app.router.add_delete("/api/media/{media_id}", delete_media_item)


async def get_file_or_directory(request: web.Request) -> web.Response:
    config = config_for(request)
    target, display_path = _resolve_workspace_path(config.cwd, request.query.get("path"))
    mode = _path_mode(target)
    if stat.S_ISDIR(mode):
        return json_response(_directory_resource(config.cwd, target, display_path))
    if not stat.S_ISREG(mode):
        raise web.HTTPUnsupportedMediaType(
            reason="Only directories and regular UTF-8 files are accessible."
        )

    content = _read_bounded_file(target, max_bytes=config.max_request_bytes)
    if b"\x00" in content:
        raise web.HTTPUnsupportedMediaType(reason="Binary files are not accessible.")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise web.HTTPUnsupportedMediaType(reason="Only UTF-8 text files are accessible.") from exc
    return json_response(
        TextFileResource(
            kind="file",
            path=display_path,
            encoding="utf-8",
            content=text,
        )
    )


async def upload_media(request: web.Request) -> web.Response:
    if request.content_type != "multipart/form-data":
        raise web.HTTPUnsupportedMediaType(reason="Content-Type must be multipart/form-data.")

    reader = await request.multipart()
    if not isinstance(reader, MultipartReader):
        raise web.HTTPBadRequest(reason="Request body must be multipart form data.")

    config = config_for(request)
    services = services_for(request)
    file_content: bytes | None = None
    file_name: str | None = None
    file_media_type: str | None = None
    session_id: str | None = None

    while True:
        part = await reader.next()
        if part is None:
            break
        if not isinstance(part, BodyPartReader):
            raise web.HTTPBadRequest(reason="Nested multipart fields are not supported.")

        field_name = part.name
        if field_name == "file":
            if file_content is not None:
                raise web.HTTPBadRequest(reason="Provide exactly one 'file' field.")
            file_name = _safe_upload_filename(part.filename)
            file_media_type = _require_upload_content_type(part.headers.get("Content-Type"))
            file_content = await _read_multipart_bytes(part, max_bytes=config.max_request_bytes)
            continue

        if field_name == "session_id":
            if session_id is not None:
                raise web.HTTPBadRequest(reason="Provide at most one 'session_id' field.")
            session_id = _decode_optional_session_id(
                await _read_multipart_bytes(part, max_bytes=config.max_request_bytes)
            )
            continue

        raise web.HTTPBadRequest(reason=f"Unknown multipart field: {field_name}.")

    if file_content is None or file_name is None or file_media_type is None:
        raise web.HTTPBadRequest(reason="Multipart form data must include one 'file' field.")
    if session_id is not None:
        await _require_session(services, session_id)
    await _enforce_media_quota(
        services,
        session_id=session_id,
        incoming_bytes=len(file_content),
        max_bytes=config.max_media_bytes_per_session,
        max_items=config.max_media_items_per_session,
    )

    image = _build_image_preview(file_content, file_media_type)
    try:
        blob = await services.media.store_blob(file_content)
        thumbnail_blob = (
            await services.media.store_blob(image.thumbnail_content) if image is not None else None
        )
        item = await services.media.create_item(
            blob_id=blob.blob_id,
            filename=file_name,
            media_type=file_media_type,
            session_id=session_id,
            thumbnail_blob_id=thumbnail_blob.blob_id if thumbnail_blob is not None else None,
            width=image.width if image is not None else None,
            height=image.height if image is not None else None,
            metadata=image.metadata if image is not None else None,
        )
        if session_id is not None:
            await services.media.add_reference(item.media_id, "session", session_id)
    except Exception as exc:
        raise_for_repository_error(exc)

    return record_response(await _media_resource(services, item), status=201)


async def list_media(request: web.Request) -> web.Response:
    services = services_for(request)
    session_id = request.query.get("session_id")
    include_deleted = parse_bool(
        request.query.get("include_deleted"),
        field="include_deleted",
        default=False,
    )
    if session_id is not None:
        await _require_session(services, session_id)
    records = await services.media.list(session_id=session_id, include_deleted=include_deleted)
    resources = tuple([await _media_resource(services, record) for record in records])
    return json_response(MediaListResource(media=resources))


async def get_media_item(request: web.Request) -> web.Response:
    services = services_for(request)
    item = await _require_live_media_item(services, request.match_info["media_id"])
    return record_response(await _media_resource(services, item))


async def get_media_content(request: web.Request) -> web.Response:
    services = services_for(request)
    item = await _require_live_media_item(services, request.match_info["media_id"])
    blob = require_found(
        await services.media.get_blob(item.blob_id),
        resource="media blob",
        identifier=item.blob_id,
    )
    etag = f'"{blob.sha256}"'
    if _if_none_match_matches(request.headers.get("If-None-Match"), etag):
        return web.Response(status=304, headers={"ETag": etag})
    return web.Response(
        body=blob.content,
        content_type=item.media_type,
        headers={
            "Content-Disposition": _content_disposition_header(item.filename),
            "ETag": etag,
        },
    )


async def get_media_thumbnail(request: web.Request) -> web.Response:
    services = services_for(request)
    item = await _require_live_media_item(services, request.match_info["media_id"])
    if item.thumbnail_blob_id is None:
        raise web.HTTPNotFound(reason=f"Media item has no thumbnail: {item.media_id}")
    blob = require_found(
        await services.media.get_blob(item.thumbnail_blob_id),
        resource="media blob",
        identifier=item.thumbnail_blob_id,
    )
    etag = f'"{blob.sha256}"'
    if _if_none_match_matches(request.headers.get("If-None-Match"), etag):
        return web.Response(status=304, headers={"ETag": etag})
    return web.Response(
        body=blob.content,
        content_type="image/png",
        headers={"Content-Disposition": "inline", "ETag": etag},
    )


async def delete_media_item(request: web.Request) -> web.Response:
    services = services_for(request)
    media_id = request.match_info["media_id"]
    try:
        item = await services.media.mark_deleted(media_id)
    except Exception as exc:
        raise_for_repository_error(exc)
    return record_response(await _media_resource(services, item))


async def _media_resource(
    services: TauWebServices,
    item: MediaItemRecord,
) -> MediaItemResource:
    references = await services.media.list_references(item.media_id)
    return MediaItemResource(
        media_id=item.media_id,
        session_id=item.session_id,
        blob_id=item.blob_id,
        thumbnail_blob_id=item.thumbnail_blob_id,
        filename=item.filename,
        media_type=item.media_type,
        width=item.width,
        height=item.height,
        metadata=item.metadata,
        reference_count=len(references),
        content_url=f"/api/media/{item.media_id}/content",
        thumbnail_url=(
            f"/api/media/{item.media_id}/thumbnail" if item.thumbnail_blob_id is not None else None
        ),
        created_at=item.created_at,
        deleted_at=item.deleted_at,
    )


async def _enforce_media_quota(
    services: TauWebServices,
    *,
    session_id: str | None,
    incoming_bytes: int,
    max_bytes: int,
    max_items: int,
) -> None:
    items = await services.media.list(session_id=session_id)
    if len(items) >= max_items:
        raise web.HTTPRequestEntityTooLarge(max_size=max_items, actual_size=len(items) + 1)
    used_bytes = 0
    for item in items:
        blob = await services.media.get_blob(item.blob_id)
        if blob is not None:
            used_bytes += blob.byte_length
    if used_bytes + incoming_bytes > max_bytes:
        raise web.HTTPRequestEntityTooLarge(
            max_size=max_bytes,
            actual_size=used_bytes + incoming_bytes,
        )


def _build_image_preview(content: bytes, media_type: str) -> _ImagePreview | None:
    normalized_type = media_type.partition(";")[0].strip().lower()
    formats = {
        "image/gif": "GIF",
        "image/jpeg": "JPEG",
        "image/png": "PNG",
        "image/webp": "WEBP",
    }
    expected_format = formats.get(normalized_type)
    if expected_format is None:
        return None
    try:
        with Image.open(BytesIO(content)) as opened:
            if opened.format != expected_format:
                raise web.HTTPUnsupportedMediaType(
                    reason="Image content does not match Content-Type."
                )
            frame_count = getattr(opened, "n_frames", 1)
            opened.seek(0)
            image = ImageOps.exif_transpose(opened).copy()
            image.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise web.HTTPUnsupportedMediaType(reason="Uploaded image could not be decoded.") from exc

    width, height = image.size
    thumbnail = image.copy()
    thumbnail.thumbnail((512, 512), Image.Resampling.LANCZOS)
    if thumbnail.mode not in {"RGB", "RGBA"}:
        thumbnail = thumbnail.convert("RGBA")
    buffer = BytesIO()
    thumbnail.save(buffer, format="PNG", optimize=True)
    return _ImagePreview(
        width=width,
        height=height,
        thumbnail_content=buffer.getvalue(),
        metadata={
            "thumbnail_media_type": "image/png",
            "thumbnail_width": thumbnail.width,
            "thumbnail_height": thumbnail.height,
            "animated": frame_count > 1,
            "frame_count": frame_count,
        },
    )


async def _require_session(services: TauWebServices, session_id: str) -> SessionRecord:
    return require_found(
        await services.sessions.get(session_id),
        resource="session",
        identifier=session_id,
    )


async def _require_live_media_item(services: TauWebServices, media_id: str) -> MediaItemRecord:
    item = require_found(
        await services.media.get_item(media_id),
        resource="media item",
        identifier=media_id,
    )
    if item.deleted_at is not None:
        raise web.HTTPNotFound(reason=f"Unknown media item: {media_id}")
    return item


def _resolve_workspace_path(root: Path, raw_path: str | None) -> tuple[Path, str]:
    if raw_path in (None, ""):
        return root, "."

    candidate = PurePosixPath(raw_path.replace("\\", "/"))
    if candidate.is_absolute():
        raise web.HTTPForbidden(reason="Path escapes the working directory.")

    current = root
    clean_parts: list[str] = []
    for part in candidate.parts:
        if part in ("", "."):
            continue
        if part == "..":
            raise web.HTTPForbidden(reason="Path escapes the working directory.")
        current = current / part
        clean_parts.append(part)
        try:
            mode = _path_mode(current)
        except FileNotFoundError as exc:
            raise web.HTTPNotFound(reason=f"Unknown file path: {raw_path}") from exc
        if stat.S_ISLNK(mode):
            raise web.HTTPForbidden(reason="Symlinks are not accessible.")

    return current, "/".join(clean_parts) or "."


def _directory_resource(root: Path, directory: Path, display_path: str) -> DirectoryResource:
    entries = sorted(directory.iterdir(), key=_directory_sort_key)
    return DirectoryResource(
        kind="directory",
        path=display_path,
        entries=tuple(
            FileEntry(
                name=entry.name,
                path=_display_child_path(root, entry),
                kind=_entry_kind(entry),
            )
            for entry in entries
        ),
    )


def _directory_sort_key(path: Path) -> tuple[int, str]:
    kind = _entry_kind(path)
    ranks = {
        "directory": 0,
        "file": 1,
        "symlink": 2,
        "special": 3,
    }
    return ranks.get(kind, 4), path.name


def _display_child_path(root: Path, path: Path) -> str:
    relative = path.relative_to(root)
    return relative.as_posix() or "."


def _entry_kind(path: Path) -> str:
    mode = _path_mode(path)
    if stat.S_ISLNK(mode):
        return "symlink"
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISREG(mode):
        return "file"
    return "special"


def _path_mode(path: Path) -> int:
    return path.lstat().st_mode


def _read_bounded_file(path: Path, *, max_bytes: int) -> bytes:
    with path.open("rb") as handle:
        content = handle.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise web.HTTPRequestEntityTooLarge(max_size=max_bytes, actual_size=len(content))
    return content


async def _read_multipart_bytes(part: BodyPartReader, *, max_bytes: int) -> bytes:
    content = bytearray()
    while True:
        chunk = await part.read_chunk()
        if not chunk:
            return bytes(content)
        content.extend(chunk)
        if len(content) > max_bytes:
            raise web.HTTPRequestEntityTooLarge(max_size=max_bytes, actual_size=len(content))


def _safe_upload_filename(filename: str | None) -> str:
    if filename is None:
        raise web.HTTPBadRequest(reason="Uploaded file must include a filename.")
    candidate = PurePosixPath(filename.replace("\\", "/")).name.strip()
    decoded = PurePosixPath(unquote(candidate)).name.strip()
    if decoded in {"", ".", ".."}:
        raise web.HTTPBadRequest(reason="Uploaded file must include a safe basename.")
    return decoded


def _require_upload_content_type(content_type: str | None) -> str:
    if content_type is None:
        raise web.HTTPBadRequest(reason="Uploaded file must include a non-blank Content-Type.")
    candidate = content_type.strip()
    if not candidate:
        raise web.HTTPBadRequest(reason="Uploaded file must include a non-blank Content-Type.")
    return candidate


def _decode_optional_session_id(raw: bytes) -> str:
    try:
        session_id = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise web.HTTPBadRequest(reason="Field 'session_id' must be valid UTF-8 text.") from exc
    candidate = session_id.strip()
    if not candidate:
        raise web.HTTPBadRequest(reason="Field 'session_id' must not be blank.")
    return candidate


def _content_disposition_header(filename: str) -> str:
    escaped_filename = filename.replace("\\", "_").replace('"', "_")
    encoded_filename = quote(filename, safe="")
    return f"inline; filename=\"{escaped_filename}\"; filename*=UTF-8''{encoded_filename}"


def _if_none_match_matches(header_value: str | None, etag: str) -> bool:
    if header_value is None:
        return False
    for item in header_value.split(","):
        candidate = item.strip()
        if candidate == "*":
            return True
        if candidate.startswith("W/"):
            candidate = candidate[2:].strip()
        if candidate == etag:
            return True
    return False
