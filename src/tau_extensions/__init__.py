"""Portable Python extension contracts for Tau.

This package deliberately has no dependency on the Tau Web server, aiohttp,
SQLite, or browser implementation details.
"""

from tau_extensions.manifest import (
    API_VERSION,
    MAX_CONTRIBUTIONS_BYTES,
    MAX_MANIFEST_BYTES,
    Dependency,
    ExtensionManifest,
    ManifestError,
    Permission,
    SemVer,
    VersionRange,
    parse_manifest_bytes,
    parse_manifest_file,
)

__all__ = [
    "API_VERSION",
    "Dependency",
    "ExtensionManifest",
    "MAX_CONTRIBUTIONS_BYTES",
    "MAX_MANIFEST_BYTES",
    "ManifestError",
    "Permission",
    "SemVer",
    "VersionRange",
    "parse_manifest_bytes",
    "parse_manifest_file",
]
