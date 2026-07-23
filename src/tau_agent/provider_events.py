"""Pi-shaped assistant stream events used by extension/event bridges."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field
from tau_agent.messages import AssistantMessage
from tau_agent.tools import ToolCall


class AssistantStartEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["start"] = "start"
    partial: AssistantMessage


class TextStartEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["text_start"] = "text_start"
    content_index: int = 0
    partial: AssistantMessage


class TextDeltaEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["text_delta"] = "text_delta"
    content_index: int = 0
    delta: str
    partial: AssistantMessage


class TextEndEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["text_end"] = "text_end"
    content_index: int = 0
    content: str
    partial: AssistantMessage


class ThinkingStartEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["thinking_start"] = "thinking_start"
    content_index: int = 0
    partial: AssistantMessage


class ThinkingDeltaEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["thinking_delta"] = "thinking_delta"
    content_index: int = 0
    delta: str
    partial: AssistantMessage


class ThinkingEndEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["thinking_end"] = "thinking_end"
    content_index: int = 0
    content: str
    partial: AssistantMessage


class ToolCallStartEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["toolcall_start"] = "toolcall_start"
    content_index: int
    partial: AssistantMessage


class ToolCallDeltaEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["toolcall_delta"] = "toolcall_delta"
    content_index: int
    delta: str
    partial: AssistantMessage


class ToolCallEndEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["toolcall_end"] = "toolcall_end"
    content_index: int
    tool_call: ToolCall
    partial: AssistantMessage


class AssistantDoneEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["done"] = "done"
    reason: Literal["stop", "length", "toolUse"] = "stop"
    message: AssistantMessage


class AssistantErrorEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["error"] = "error"
    reason: Literal["aborted", "error"] = "error"
    error: AssistantMessage


type AssistantMessageEvent = Annotated[
    AssistantStartEvent
    | TextStartEvent
    | TextDeltaEvent
    | TextEndEvent
    | ThinkingStartEvent
    | ThinkingDeltaEvent
    | ThinkingEndEvent
    | ToolCallStartEvent
    | ToolCallDeltaEvent
    | ToolCallEndEvent
    | AssistantDoneEvent
    | AssistantErrorEvent,
    Field(discriminator="type"),
]
