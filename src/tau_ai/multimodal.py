"""Provider payload helpers for transient user image attachments."""

from __future__ import annotations

from base64 import b64encode

from tau_agent.messages import UserAttachment, UserMessage
from tau_agent.types import JSONValue

_SUPPORTED_IMAGE_TYPES = frozenset(
    {
        "image/gif",
        "image/jpeg",
        "image/png",
        "image/webp",
    }
)


def usable_images(message: UserMessage) -> tuple[UserAttachment, ...]:
    """Return hydrated images that provider APIs can accept."""
    return tuple(
        attachment
        for attachment in message.attachments
        if attachment.data is not None and attachment.media_type.lower() in _SUPPORTED_IMAGE_TYPES
    )


def data_url(attachment: UserAttachment) -> str:
    """Encode one hydrated image as a provider-compatible data URL."""
    assert attachment.data is not None
    encoded = b64encode(attachment.data).decode("ascii")
    return f"data:{attachment.media_type.lower()};base64,{encoded}"


def openai_chat_content(message: UserMessage) -> JSONValue:
    """Build Chat Completions text/image content, preserving text-only payloads."""
    images = usable_images(message)
    if not images:
        return message.content
    parts: list[JSONValue] = [{"type": "text", "text": message.content}]
    parts.extend(
        {"type": "image_url", "image_url": {"url": data_url(attachment)}} for attachment in images
    )
    return parts


def openai_responses_blocks(message: UserMessage) -> list[JSONValue]:
    """Build Responses API input blocks from text and hydrated images."""
    parts: list[JSONValue] = [{"type": "input_text", "text": message.content}]
    parts.extend(
        {"type": "input_image", "image_url": data_url(attachment)}
        for attachment in usable_images(message)
    )
    return parts


def openai_responses_content(message: UserMessage) -> JSONValue:
    """Build Responses input while preserving historical text-only payloads."""
    if not usable_images(message):
        return message.content
    return openai_responses_blocks(message)


def anthropic_content(message: UserMessage) -> JSONValue:
    """Build Anthropic text/image blocks, preserving text-only payloads."""
    images = usable_images(message)
    if not images:
        return message.content
    parts: list[JSONValue] = [{"type": "text", "text": message.content}]
    for attachment in images:
        assert attachment.data is not None
        parts.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": attachment.media_type.lower(),
                    "data": b64encode(attachment.data).decode("ascii"),
                },
            }
        )
    return parts
