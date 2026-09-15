"""Session-confined agent tool for uploaded media attachments."""

from __future__ import annotations

from collections.abc import Mapping

from tau_agent import AgentTool, AgentToolResult
from tau_agent.tools import ToolCancellationToken
from tau_agent.types import JSONValue
from tau_web.sqlite.repositories import MediaItemRecord, MediaRepository

_DEFAULT_MAX_TEXT_BYTES = 256 * 1024


def create_attachment_tool(
    media: MediaRepository,
    session_id: str,
    *,
    max_text_bytes: int = _DEFAULT_MAX_TEXT_BYTES,
) -> AgentTool:
    """Create a provider-neutral tool for listing and reading session media."""
    if not session_id.strip():
        raise ValueError("session_id must be non-blank")
    if max_text_bytes <= 0:
        raise ValueError("max_text_bytes must be positive")

    async def execute(
        arguments: Mapping[str, JSONValue],
        signal: ToolCancellationToken | None = None,
    ) -> AgentToolResult:
        if signal is not None and signal.is_cancelled():
            return _error("Attachment operation cancelled.")
        action = arguments.get("action", "list")
        if action == "list":
            records = await media.list(session_id=session_id)
            return AgentToolResult(
                tool_call_id="",
                name="attachment",
                ok=True,
                content=_render_listing(records),
                data={"count": len(records)},
            )
        if action != "read":
            return _error("action must be either 'list' or 'read'.")
        media_id = arguments.get("media_id")
        if not isinstance(media_id, str) or not media_id.strip():
            return _error("media_id is required when action is 'read'.")
        item = await media.get_item(media_id)
        if item is None or item.deleted_at is not None or item.session_id not in {None, session_id}:
            return _error(f"Unknown attachment: {media_id}")
        blob = await media.get_blob(item.blob_id)
        if blob is None:
            return _error(f"Attachment content is unavailable: {media_id}")
        metadata: dict[str, JSONValue] = {
            "media_id": item.media_id,
            "filename": item.filename,
            "media_type": item.media_type,
            "bytes": blob.byte_length,
        }
        if item.media_type.startswith("image/"):
            return AgentToolResult(
                tool_call_id="",
                name="attachment",
                ok=True,
                content=(
                    f"Image attachment {item.filename} [{item.media_type}, "
                    f"{blob.byte_length} bytes] is included in the user prompt."
                ),
                data=metadata,
            )
        if blob.byte_length > max_text_bytes:
            return _error(
                f"Attachment is too large to read as text ({blob.byte_length} bytes; "
                f"limit {max_text_bytes})."
            )
        try:
            text = blob.content.decode("utf-8")
        except UnicodeDecodeError:
            return _error(f"Attachment is not UTF-8 text: {item.filename}")
        return AgentToolResult(
            tool_call_id="",
            name="attachment",
            ok=True,
            content=text,
            data=metadata,
        )

    return AgentTool(
        name="attachment",
        description="List uploaded attachments for this session or read one UTF-8 attachment.",
        input_schema={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "read"]},
                "media_id": {"type": "string"},
            },
            "additionalProperties": False,
        },
        executor=execute,
        prompt_guidelines=(
            "Use attachment to inspect uploaded non-image files by media ID.",
            "Images attached to user messages are already sent as multimodal input.",
        ),
    )


def _render_listing(records: list[MediaItemRecord]) -> str:
    if not records:
        return "No uploaded attachments are available for this session."
    return "\n".join(
        f"{record.media_id}\t{record.filename}\t{record.media_type}" for record in records
    )


def _error(content: str) -> AgentToolResult:
    return AgentToolResult(
        tool_call_id="",
        name="attachment",
        ok=False,
        content=content,
        error=content,
    )
