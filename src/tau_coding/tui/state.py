"""Display state for Tau's Textual TUI."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Literal

from tau_agent.messages import AgentMessage

ChatItemRole = Literal["user", "assistant", "tool", "error", "status"]


@dataclass(slots=True)
class ChatItem:
    """One rendered item in the TUI transcript."""

    role: ChatItemRole
    text: str


@dataclass(slots=True)
class TuiState:
    """Mutable display state for the interactive TUI."""

    items: list[ChatItem] = field(default_factory=list)
    assistant_buffer: str = ""
    running: bool = False
    error: str | None = None

    def add_item(self, role: ChatItemRole, text: str) -> None:
        """Append a transcript item."""
        self.items.append(ChatItem(role=role, text=text))

    def clear(self) -> None:
        """Clear visible transcript state without modifying durable session history."""
        self.items.clear()
        self.assistant_buffer = ""
        self.error = None

    def load_messages(self, messages: Iterable[AgentMessage]) -> None:
        """Populate the transcript from restored session messages."""
        for message in messages:
            if message.role == "user":
                self.add_item("user", message.content)
            elif message.role == "assistant":
                if message.content:
                    self.add_item("assistant", message.content)
                for tool_call in message.tool_calls:
                    self.add_item("tool", f"→ {tool_call.name} {tool_call.arguments}")
            elif message.role == "tool":
                status = "✓" if message.ok else "✗"
                text = f"{status} {message.name}"
                if message.content:
                    text = f"{text}\n{message.content}"
                self.add_item("tool", text)
