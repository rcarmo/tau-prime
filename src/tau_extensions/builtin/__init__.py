"""Bundled portable Tau extensions.

This package intentionally avoids importing individual built-in extensions so
manifest discovery never loads extension entrypoints as a side effect.
"""

from __future__ import annotations

from pathlib import Path

BUILTIN_ROOT = Path(__file__).resolve().parent


def extension_roots() -> tuple[Path, ...]:
    """Return filesystem roots that contain bundled extension manifests."""
    return (BUILTIN_ROOT,)


__all__ = ["BUILTIN_ROOT", "extension_roots"]
