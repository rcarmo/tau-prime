"""Provider-neutral tool-call identifier handling."""

from __future__ import annotations

import re
from hashlib import sha256

_PORTABLE_TOOL_CALL_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def portable_tool_call_id(value: str) -> str:
    """Return a deterministic tool-call ID accepted by supported providers.

    Provider-native IDs that already use the common portable subset are kept
    verbatim. Foreign, malformed, empty, or oversized IDs are hashed so a tool
    call and its result are translated identically without rewriting history.
    """
    if _PORTABLE_TOOL_CALL_ID.fullmatch(value):
        return value
    digest = sha256(value.encode("utf-8")).hexdigest()[:40]
    return f"tc_{digest}"
