"""macOS Seatbelt re-execution for Tau's command-line process."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

from tau_coding.paths import TauPaths

_SANDBOXED_ENV = "TAU_MACOS_SANDBOXED"
_SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")


class MacOSSandboxError(RuntimeError):
    """Raised when Tau cannot establish its required macOS sandbox."""


def should_enter_macos_sandbox(*, disabled: bool, platform: str | None = None) -> bool:
    """Return whether this process must re-execute under macOS Seatbelt."""
    current_platform = sys.platform if platform is None else platform
    return current_platform == "darwin" and not disabled and os.environ.get(_SANDBOXED_ENV) != "1"


def build_macos_sandbox_profile(
    *,
    project_dir: Path,
    paths: TauPaths | None = None,
    tmpdir: Path | None = None,
) -> str:
    """Build a profile that permits writes only to Tau and working directories."""
    tau_paths = paths or TauPaths()
    writable_roots = _minimal_roots(
        (
            project_dir,
            tau_paths.home,
            tau_paths.logs_dir,
            tmpdir or Path(tempfile.gettempdir()),
        )
    )
    rules = [
        "(version 1)",
        "(allow default)",
        "(deny file-write*)",
    ]
    rules.extend(
        f"(allow file-write* (subpath {json.dumps(str(root))}))" for root in writable_roots
    )
    rules.extend(
        (
            '(allow file-write* (literal "/dev/null"))',
            '(allow file-write* (literal "/dev/tty"))',
        )
    )
    return "\n".join(rules) + "\n"


def enter_macos_sandbox(
    *,
    argv: Sequence[str],
    project_dir: Path,
    paths: TauPaths | None = None,
    sandbox_exec: Path = _SANDBOX_EXEC,
) -> NoReturn:
    """Replace this process with an equivalent invocation under sandbox-exec."""
    if not sandbox_exec.is_file() or not os.access(sandbox_exec, os.X_OK):
        raise MacOSSandboxError(f"macOS sandbox executable is unavailable: {sandbox_exec}")

    executable = _resolve_executable(argv[0] if argv else "tau")
    resolved_project = project_dir.expanduser().resolve(strict=False)
    if not resolved_project.is_dir():
        raise MacOSSandboxError(f"sandbox working directory does not exist: {resolved_project}")
    tau_paths = paths or TauPaths()
    try:
        tau_paths.home.mkdir(parents=True, exist_ok=True)
        tau_paths.logs_dir.mkdir(parents=True, exist_ok=True)
        Path(tempfile.gettempdir()).mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise MacOSSandboxError(f"could not prepare a writable sandbox directory: {exc}") from exc
    profile = build_macos_sandbox_profile(project_dir=resolved_project, paths=tau_paths)
    environment = dict(os.environ)
    environment[_SANDBOXED_ENV] = "1"
    command = [str(sandbox_exec), "-p", profile, executable, *argv[1:]]
    try:
        os.execve(str(sandbox_exec), command, environment)
    except OSError as exc:
        raise MacOSSandboxError(f"could not start Tau's macOS sandbox: {exc}") from exc
    raise AssertionError("os.execve returned unexpectedly")


def _resolve_executable(value: str) -> str:
    resolved = shutil.which(value)
    if resolved is not None:
        return str(Path(resolved).resolve())
    path = Path(value).expanduser()
    if path.is_file():
        return str(path.resolve())
    raise MacOSSandboxError(f"could not resolve Tau executable: {value}")


def _minimal_roots(paths: Sequence[Path]) -> tuple[Path, ...]:
    """Canonicalise roots and remove duplicates nested beneath another root."""
    resolved = sorted(
        {path.expanduser().resolve(strict=False) for path in paths},
        key=lambda item: (len(item.parts), str(item)),
    )
    roots: list[Path] = []
    for candidate in resolved:
        if any(candidate == root or candidate.is_relative_to(root) for root in roots):
            continue
        roots.append(candidate)
    return tuple(roots)
