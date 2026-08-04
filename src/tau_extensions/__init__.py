"""Portable Python extension contracts for Tau.

This package deliberately has no dependency on the Tau Web server, aiohttp,
SQLite, or browser implementation details.
"""

from tau_extensions.discovery import (
    MANIFEST_FILENAME,
    Candidate,
    Diagnostic,
    DiscoveryResult,
    ExtensionSource,
    discover_extensions,
)
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
from tau_extensions.resolution import (
    ActivationPlan,
    Approval,
    ResolutionDecision,
    TrustPolicy,
    resolve_extensions,
)

__all__ = [
    "API_VERSION",
    "ActivationPlan",
    "Approval",
    "Candidate",
    "Dependency",
    "Diagnostic",
    "DiscoveryResult",
    "ExtensionManifest",
    "ExtensionSource",
    "MANIFEST_FILENAME",
    "MAX_CONTRIBUTIONS_BYTES",
    "MAX_MANIFEST_BYTES",
    "ManifestError",
    "Permission",
    "ResolutionDecision",
    "SemVer",
    "TrustPolicy",
    "VersionRange",
    "discover_extensions",
    "parse_manifest_bytes",
    "parse_manifest_file",
    "resolve_extensions",
]
