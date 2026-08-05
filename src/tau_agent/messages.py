"""Provider-neutral transcript message models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from tau_agent.tools import ToolCall
from tau_agent.types import JSONValue


class UserAttachment(BaseModel):
    """Metadata for media attached to a user message.

    ``data`` is transient: providers may use it for one request, while session
    stores and exports retain only the stable media metadata and ID.
    """

    model_config = ConfigDict(extra="forbid")

    media_id: str
    filename: str
    media_type: str
    size_bytes: int
    data: bytes | None = Field(default=None, exclude=True, repr=False)


class UserMessage(BaseModel):
    """A message authored by the user."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["user"] = "user"
    content: str
    attachments: list[UserAttachment] = Field(default_factory=list, exclude_if=lambda value: not value)


class AssistantMessage(BaseModel):
    """A message authored by the assistant, optionally requesting tool calls."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["assistant"] = "assistant"
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)


class ToolResultMessage(BaseModel):
    """A transcript message containing the result of a previous tool call."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["tool"] = "tool"
    tool_call_id: str
    name: str
    content: str
    ok: bool = True
    data: dict[str, JSONValue] | None = None
    details: dict[str, JSONValue] | None = None
    error: str | None = None


type AgentMessage = UserMessage | AssistantMessage | ToolResultMessage
