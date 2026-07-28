"""Linux bubblewrap filesystem sandbox for Tau's command-line process."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from tau_coding.paths import TauPaths

_SANDBOXED_ENV = "TAU_LINUX_SANDBOXED"
_SANDBOX_MODE_ENV = "TAU_LINUX_SANDBOX"
_EXTRA_WRITABLE_ENV = "TAU_SANDBOX_WRITABLE_PATHS"
_DEFAULT_ON_ENV = "TAU_LINUX_SANDBOX_DEFAULT_ON"
_BWRAP_EXECUTABLE = "bwrap"
_TRUE_VALUES = {"1", "true", "yes", "on", "auto"}
_REQUIRED_VALUES = {"required", "force", "fail-closed"}
_FALSE_VALUES = {"0", "false", "no", "off", "disabled"}


class LinuxSandboxError(RuntimeError):
    """Raised when Tau cannot establish the requested Linux sandbox."""


def should_enter_linux_sandbox(
    *,
    disabled: bool,
    platform: str | None = None,
    bwrap_path: str | None = None,
) -> bool:
    """Return whether the current process should re-exec under bubblewrap.

    By default the Linux sandbox is opt-in with ``TAU_LINUX_SANDBOX=1``.
    Phase-3 default-on behavior is available behind
    ``TAU_LINUX_SANDBOX_DEFAULT_ON=1``: use bubblewrap when it is present, but do
    not break systems that lack it unless the user explicitly requests the
    sandbox with ``TAU_LINUX_SANDBOX=1`` or ``required``. ``--no-sandbox`` and
    false-like ``TAU_LINUX_SANDBOX`` values always disable it.
    """
    if disabled or os.environ.get(_SANDBOXED_ENV) == "1":
        return False
    if (platform or sys.platform) != "linux":
        return False

    mode = _sandbox_mode()
    if mode == "disabled":
        return False
    if mode in {"enabled", "required"}:
        return True
    if mode == "auto":
        return bwrap_path is not None or shutil.which(_BWRAP_EXECUTABLE) is not None
    return False


def build_linux_bwrap_args(
    *,
    executable: Path,
    argv: Sequence[str],
    project_dir: Path,
    tau_paths: TauPaths | None = None,
    temp_dir: Path | None = None,
    extra_writable_paths: Sequence[Path] = (),
) -> list[str]:
    """Build bubblewrap arguments for Tau's filesystem sandbox."""
    paths = tau_paths or TauPaths()
    resolved_project = project_dir.resolve()
    if not resolved_project.is_dir():
        raise LinuxSandboxError(f"Project directory does not exist: {resolved_project}")

    temp_root = (temp_dir or Path(tempfile.gettempdir())).expanduser().resolve()
    writable_roots = _dedupe_paths(
        [
            resolved_project,
            paths.home.expanduser().resolve(),
            paths.logs_dir.expanduser().resolve(),
            temp_root,
            *[path.expanduser().resolve() for path in extra_writable_paths],
        ]
    )

    args = [
        "--die-with-parent",
        "--ro-bind",
        "/",
        "/",
        "--dev-bind",
        "/dev",
        "/dev",
        "--proc",
        "/proc",
    ]
    for root in writable_roots:
        args.extend(["--bind", str(root), str(root)])
    args.extend(
        [
            "--setenv",
            _SANDBOXED_ENV,
            "1",
            "--setenv",
            "PYTHONDONTWRITEBYTECODE",
            "1",
            "--chdir",
            str(resolved_project),
            str(executable),
            *list(argv[1:]),
        ]
    )
    return args


def enter_linux_sandbox(
    *,
    argv: Sequence[str] | None = None,
    project_dir: Path,
    tau_paths: TauPaths | None = None,
    bwrap_executable: str | Path = _BWRAP_EXECUTABLE,
    temp_dir: Path | None = None,
    extra_writable_paths: Sequence[Path] | None = None,
) -> None:
    """Re-execute Tau inside a Linux bubblewrap sandbox."""
    current_argv = list(argv or sys.argv)
    if not current_argv:
        raise LinuxSandboxError("Cannot enter Linux sandbox without argv")

    bwrap_path = _resolve_bwrap(bwrap_executable)
    executable = _resolve_executable(current_argv[0])
    paths = tau_paths or TauPaths()
    paths.home.mkdir(parents=True, exist_ok=True)
    paths.logs_dir.mkdir(parents=True, exist_ok=True)
    temp_root = temp_dir or Path(tempfile.gettempdir())
    temp_root.mkdir(parents=True, exist_ok=True)
    extra_paths = tuple(extra_writable_paths or extra_writable_paths_from_env())
    for path in extra_paths:
        resolved = path.expanduser().resolve()
        if not resolved.is_dir():
            raise LinuxSandboxError(f"Extra writable sandbox path is not a directory: {resolved}")

    bwrap_args = build_linux_bwrap_args(
        executable=executable,
        argv=current_argv,
        project_dir=project_dir,
        tau_paths=paths,
        temp_dir=temp_root,
        extra_writable_paths=extra_paths,
    )
    os.execv(str(bwrap_path), [str(bwrap_path), *bwrap_args])


def extra_writable_paths_from_env(value: str | None = None) -> tuple[Path, ...]:
    """Return extra writable paths requested through TAU_SANDBOX_WRITABLE_PATHS."""
    raw = os.environ.get(_EXTRA_WRITABLE_ENV, "") if value is None else value
    if not raw.strip():
        return ()
    return tuple(Path(part).expanduser() for part in raw.split(os.pathsep) if part.strip())


def _sandbox_mode() -> str:
    raw = os.environ.get(_SANDBOX_MODE_ENV)
    if raw is None or not raw.strip():
        default_on = os.environ.get(_DEFAULT_ON_ENV, "").strip().casefold()
        return "auto" if default_on in _TRUE_VALUES else "disabled"
    normalized = raw.strip().casefold()
    if normalized in _FALSE_VALUES:
        return "disabled"
    if normalized in _REQUIRED_VALUES:
        return "required"
    if normalized in _TRUE_VALUES:
        return "enabled"
    return "enabled"


def _resolve_bwrap(value: str | Path) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or candidate.parent != Path("."):
        path = candidate
    else:
        resolved = shutil.which(str(value))
        if resolved is None:
            raise LinuxSandboxError(
                "bubblewrap (bwrap) is required for the Linux sandbox; "
                "install it or use --no-sandbox"
            )
        path = Path(resolved)
    if not path.is_file() or not os.access(path, os.X_OK):
        raise LinuxSandboxError(f"bubblewrap executable is not available: {path}")
    return path


def _resolve_executable(value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or candidate.parent != Path("."):
        return candidate
    resolved = shutil.which(value)
    if resolved is None:
        raise LinuxSandboxError(f"Cannot resolve Tau executable for Linux sandbox: {value}")
    return Path(resolved)


def _dedupe_paths(paths: Sequence[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result
