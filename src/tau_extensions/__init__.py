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
from tau_extensions.runtime import (
    Contribution,
    ContributionRegistry,
    Disposable,
    DisposalHandle,
    ExtensionDefinition,
    ExtensionHost,
    ExtensionRegistrar,
    RegistryError,
    RuntimeDiagnostic,
)

__all__ = [
    "API_VERSION",
    "ActivationPlan",
    "Approval",
    "Candidate",
    "Contribution",
    "ContributionRegistry",
    "Dependency",
    "Diagnostic",
    "DiscoveryResult",
    "Disposable",
    "DisposalHandle",
    "ExtensionDefinition",
    "ExtensionHost",
    "ExtensionManifest",
    "ExtensionRegistrar",
    "ExtensionSource",
    "MANIFEST_FILENAME",
    "MAX_CONTRIBUTIONS_BYTES",
    "MAX_MANIFEST_BYTES",
    "ManifestError",
    "Permission",
    "RegistryError",
    "ResolutionDecision",
    "RuntimeDiagnostic",
    "SemVer",
    "TrustPolicy",
    "VersionRange",
    "discover_extensions",
    "parse_manifest_bytes",
    "parse_manifest_file",
    "resolve_extensions",
]
