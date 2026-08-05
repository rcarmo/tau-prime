"""Security helpers shared by Tau Web runtime and persistence boundaries."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from ipaddress import ip_address
from typing import cast

from tau_agent.types import JSONValue

_SENSITIVE_KEY_PATTERN = re.compile(
    r"(?:^|[_-])(api[_-]?key|auth|authorization|credential|password|secret|token)(?:$|[_-])",
    re.IGNORECASE,
)
_SECRET_PATTERNS = (
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/-]+=*"),
    re.compile(r"\b(?:gh[opusr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})\b"),
    re.compile(
        r"(?i)((?:api[_-]?key|password|secret|token)\s*[=:]\s*)"
        r"(?:[^\s'\";,]+|'[^']*'|\"[^\"]*\")"
    ),
)
_REDACTED = "[REDACTED]"


def is_loopback_host(host: str) -> bool:
    """Return whether a bind host is unambiguously loopback-only."""
    normalized = host.strip().casefold()
    if normalized in {"localhost", "ip6-localhost"}:
        return True
    if normalized.startswith("[") and normalized.endswith("]"):
        normalized = normalized[1:-1]
    try:
        return ip_address(normalized).is_loopback
    except ValueError:
        return False


def redact_text(value: str) -> str:
    """Remove common credential forms from text before browser or audit exposure."""
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(
            lambda match: f"{match.group(1)}{_REDACTED}" if match.lastindex else _REDACTED,
            redacted,
        )
    return redacted


def redact_json(value: JSONValue) -> JSONValue:
    """Recursively redact sensitive keys and credential-like string values."""
    if isinstance(value, Mapping):
        output: dict[str, JSONValue] = {}
        for raw_key, item in value.items():
            key = str(raw_key)
            output[key] = _REDACTED if _SENSITIVE_KEY_PATTERN.search(key) else redact_json(item)
        return output
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact_json(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return cast(JSONValue, value)


__all__ = ["is_loopback_host", "redact_json", "redact_text"]
