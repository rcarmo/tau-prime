"""Portable Python extension contracts for Tau.

This package deliberately has no dependency on the Tau Web server, aiohttp,
SQLite, or browser implementation details.
"""

from __future__ import annotations

API_VERSION = "1.0"

__all__ = ["API_VERSION"]
