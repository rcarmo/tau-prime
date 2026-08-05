from __future__ import annotations

from tau_agent import UserAttachment, UserMessage
from tau_ai.anthropic import _anthropic_message
from tau_ai.openai_codex import _messages_to_responses_input as codex_input
from tau_ai.openai_compatible import (
    _message_to_openai,
)
from tau_ai.openai_compatible import (
    _messages_to_responses_input as openai_responses_input,
)


def _image_message() -> UserMessage:
    return UserMessage(
        content="describe this",
        attachments=[
            UserAttachment(
                media_id="media-1",
                filename="pixel.png",
                media_type="image/png",
                size_bytes=3,
                data=b"png",
            )
        ],
    )


def test_attachment_bytes_are_transient_during_serialisation() -> None:
    dumped = _image_message().model_dump(mode="json")

    assert _image_message().model_copy(update={"content": "expanded"}).attachments[0].data == b"png"
    assert dumped == {
        "role": "user",
        "content": "describe this",
        "attachments": [
            {
                "media_id": "media-1",
                "filename": "pixel.png",
                "media_type": "image/png",
                "size_bytes": 3,
            }
        ],
    }


def test_openai_chat_serialises_hydrated_images() -> None:
    assert _message_to_openai(_image_message()) == {
        "role": "user",
        "content": [
            {"type": "text", "text": "describe this"},
            {
                "type": "image_url",
                "image_url": {"url": "data:image/png;base64,cG5n"},
            },
        ],
    }


def test_openai_responses_and_codex_serialise_hydrated_images() -> None:
    expected = [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "describe this"},
                {"type": "input_image", "image_url": "data:image/png;base64,cG5n"},
            ],
        }
    ]

    assert openai_responses_input([_image_message()]) == expected
    assert codex_input([_image_message()]) == expected


def test_anthropic_serialises_hydrated_images() -> None:
    assert _anthropic_message(_image_message()) == {
        "role": "user",
        "content": [
            {"type": "text", "text": "describe this"},
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": "cG5n",
                },
            },
        ],
    }


def test_unhydrated_and_unsupported_attachments_preserve_text_payloads() -> None:
    message = UserMessage(
        content="read these",
        attachments=[
            UserAttachment(
                media_id="media-1",
                filename="image.png",
                media_type="image/png",
                size_bytes=3,
            ),
            UserAttachment(
                media_id="media-2",
                filename="notes.txt",
                media_type="text/plain",
                size_bytes=3,
                data=b"txt",
            ),
        ],
    )

    assert _message_to_openai(message) == {"role": "user", "content": "read these"}
    assert _anthropic_message(message) == {"role": "user", "content": "read these"}
