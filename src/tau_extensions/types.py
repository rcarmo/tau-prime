"""Public JSON-compatible types for portable Tau extensions."""

from __future__ import annotations

type JSONPrimitive = str | int | float | bool | None
type JSONValue = JSONPrimitive | list[JSONValue] | dict[str, JSONValue]
type JSONObject = dict[str, JSONValue]

__all__ = ["JSONPrimitive", "JSONObject", "JSONValue"]
