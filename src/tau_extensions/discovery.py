"""Filesystem discovery helpers for portable Tau extensions."""

from __future__ import annotations

import hashlib
import stat
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from tau_extensions.manifest import ExtensionManifest, ManifestError, parse_manifest_bytes

MANIFEST_FILENAME = "tau-extension.json"


class ExtensionSource(StrEnum):
    """Stable extension origin buckets used for discovery precedence."""

    BUILT_IN = "built_in"
    ADMIN = "admin"
    WORKSPACE = "workspace"


_SOURCE_PRIORITY: dict[ExtensionSource, int] = {
    ExtensionSource.BUILT_IN: 0,
    ExtensionSource.ADMIN: 1,
    ExtensionSource.WORKSPACE: 2,
}


@dataclass(frozen=True, slots=True)
class Candidate:
    """A discovered extension candidate before later runtime loading."""

    manifest: ExtensionManifest
    path: Path
    source: ExtensionSource
    fingerprint: str

    @property
    def manifest_path(self) -> Path:
        """Return the manifest file path for this candidate."""
        return self.path / MANIFEST_FILENAME


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """A non-fatal extension discovery problem."""

    code: str
    message: str
    path: Path | None = None
    id: str | None = None


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    """Immutable result from extension discovery."""

    candidates: tuple[Candidate, ...]
    diagnostics: tuple[Diagnostic, ...]


def discover_extensions(
    roots: Mapping[ExtensionSource, Sequence[Path]],
) -> DiscoveryResult:
    """Discover extension manifests under immediate child directories.

    Discovery never imports or otherwise executes extension entrypoints.
    """

    candidates: list[Candidate] = []
    diagnostics: list[Diagnostic] = []
    for source in ExtensionSource:
        for root in _sorted_paths(roots.get(source, ())):
            root_candidates, root_diagnostics = _discover_root(source=source, root=root)
            candidates.extend(root_candidates)
            diagnostics.extend(root_diagnostics)

    candidates.sort(key=_candidate_sort_key)

    winners: list[Candidate] = []
    winners_by_id: dict[str, Candidate] = {}
    for candidate in candidates:
        existing = winners_by_id.get(candidate.manifest.id)
        if existing is None:
            winners_by_id[candidate.manifest.id] = candidate
            winners.append(candidate)
            continue
        diagnostics.append(
            Diagnostic(
                code="duplicate_id",
                message=(
                    f"duplicate extension id {candidate.manifest.id!r} ignored in favor of "
                    f"{existing.manifest_path}"
                ),
                path=candidate.manifest_path,
                id=candidate.manifest.id,
            )
        )

    return DiscoveryResult(candidates=tuple(winners), diagnostics=tuple(diagnostics))


def _discover_root(
    *,
    source: ExtensionSource,
    root: Path,
) -> tuple[list[Candidate], list[Diagnostic]]:
    root_path = root.expanduser()
    try:
        root_stat = root_path.lstat()
    except FileNotFoundError:
        return [], []
    if stat.S_ISLNK(root_stat.st_mode):
        return [], [
            Diagnostic(
                code="root_symlink",
                message="extension root must not be a symlink",
                path=root_path,
            )
        ]
    if not stat.S_ISDIR(root_stat.st_mode):
        return [], []

    try:
        root_resolved = root_path.resolve(strict=True)
        children = list(root_path.iterdir())
    except OSError:
        return [], []

    candidates: list[Candidate] = []
    diagnostics: list[Diagnostic] = []
    for child in _sorted_paths(children):
        candidate, child_diagnostics = _discover_child(
            source=source,
            root_resolved=root_resolved,
            child=child,
        )
        if candidate is not None:
            candidates.append(candidate)
        diagnostics.extend(child_diagnostics)
    return candidates, diagnostics


def _discover_child(
    *,
    source: ExtensionSource,
    root_resolved: Path,
    child: Path,
) -> tuple[Candidate | None, tuple[Diagnostic, ...]]:
    try:
        child_stat = child.lstat()
    except FileNotFoundError:
        return None, ()
    if stat.S_ISLNK(child_stat.st_mode):
        return None, (
            Diagnostic(
                code="child_symlink",
                message="extension directory must not be a symlink",
                path=child,
            ),
        )
    if not stat.S_ISDIR(child_stat.st_mode):
        return None, ()

    try:
        child_resolved = child.resolve(strict=True)
    except OSError:
        return None, ()
    if not child_resolved.is_relative_to(root_resolved):
        return None, (
            Diagnostic(
                code="child_outside_root",
                message="resolved extension directory escapes its root",
                path=child,
            ),
        )

    manifest_path = child / MANIFEST_FILENAME
    try:
        manifest_stat = manifest_path.lstat()
    except FileNotFoundError:
        return None, ()
    if stat.S_ISLNK(manifest_stat.st_mode):
        return None, (
            Diagnostic(
                code="manifest_symlink",
                message="manifest file must not be a symlink",
                path=manifest_path,
            ),
        )
    if not stat.S_ISREG(manifest_stat.st_mode):
        return None, (
            Diagnostic(
                code="invalid_manifest",
                message="manifest file must be a regular file",
                path=manifest_path,
            ),
        )

    try:
        raw = manifest_path.read_bytes()
        manifest = parse_manifest_bytes(raw)
    except (ManifestError, OSError) as exc:
        return None, (
            Diagnostic(
                code="invalid_manifest",
                message=str(exc),
                path=manifest_path,
            ),
        )

    return (
        Candidate(
            manifest=manifest,
            path=child_resolved,
            source=source,
            fingerprint=hashlib.sha256(raw).hexdigest(),
        ),
        (),
    )


def _candidate_sort_key(candidate: Candidate) -> tuple[int, str]:
    return (_SOURCE_PRIORITY[candidate.source], _path_sort_key(candidate.manifest_path))


def _sorted_paths(paths: Iterable[Path]) -> list[Path]:
    return sorted(paths, key=_path_sort_key)


def _path_sort_key(path: Path) -> str:
    return str(path.expanduser().resolve(strict=False))


__all__ = [
    "Candidate",
    "Diagnostic",
    "DiscoveryResult",
    "ExtensionSource",
    "MANIFEST_FILENAME",
    "discover_extensions",
]
