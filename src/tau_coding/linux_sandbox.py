"""Linux Landlock write confinement, applied before Tau starts worker threads.

Reads, execution and networking remain unrestricted. Existing open descriptors
are not revoked. This is filesystem write confinement, not namespace isolation.
"""
from __future__ import annotations

import ctypes
import os
import platform as host_platform
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from tau_coding.paths import TauPaths

_SANDBOXED_ENV = "TAU_LINUX_SANDBOXED"
_SANDBOX_MODE_ENV = "TAU_LINUX_SANDBOX"
_EXTRA_WRITABLE_ENV = "TAU_SANDBOX_WRITABLE_PATHS"
_DEFAULT_ON_ENV = "TAU_LINUX_SANDBOX_DEFAULT_ON"
_TRUE_VALUES = {"1", "true", "yes", "on", "auto"}
_REQUIRED_VALUES = {"required", "force", "fail-closed"}
_FALSE_VALUES = {"0", "false", "no", "off", "disabled"}
# ABI 3 is required to mediate truncation as well as cross-directory rename.
_WRITE = (1 << 1) | sum(1 << bit for bit in range(4, 15))
_entered = False

class LinuxSandboxError(RuntimeError):
    """The requested Landlock policy could not be installed."""

class _Ruleset(ctypes.Structure):
    _fields_ = [("handled_access_fs", ctypes.c_uint64)]

class _PathRule(ctypes.Structure):
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]

def _libc():
    if sys.platform != "linux" or host_platform.machine() not in {
        "x86_64", "aarch64", "riscv64", "i386", "i686", "armv7l"
    }:
        raise LinuxSandboxError("Landlock syscall numbers unavailable on this platform")
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long
    return libc

def _call(number, *args):
    result = _libc().syscall(ctypes.c_long(number), *args)
    if result < 0:
        error = ctypes.get_errno()
        raise LinuxSandboxError(f"Landlock syscall {number}: {os.strerror(error)}")
    return result

def landlock_abi() -> int:
    """Probe kernel support without applying any restrictions."""
    try:
        return _call(444, ctypes.c_void_p(), ctypes.c_size_t(0), ctypes.c_uint(1))
    except LinuxSandboxError:
        return 0

def should_enter_linux_sandbox(*, disabled: bool, platform: str | None = None) -> bool:
    if disabled or _entered or (platform or sys.platform) != "linux":
        return False
    mode = _sandbox_mode()
    if mode in {"enabled", "required"}:
        return True
    return mode == "auto" and landlock_abi() >= 3

def enter_linux_sandbox(
    *, argv: Sequence[str] | None = None, project_dir: Path,
    tau_paths: TauPaths | None = None, temp_dir: Path | None = None,
    extra_writable_paths: Sequence[Path] | None = None,
) -> None:
    """Restrict this thread and its future children; never re-exec or fail open."""
    global _entered
    if landlock_abi() < 3:
        raise LinuxSandboxError("Linux sandbox requires Landlock ABI 3 or newer")
    project = project_dir.resolve()
    if not project.is_dir():
        raise LinuxSandboxError(f"Project directory does not exist: {project}")
    paths = tau_paths or TauPaths()
    extras = extra_writable_paths_from_env() if extra_writable_paths is None else extra_writable_paths
    roots = [project, paths.home, paths.logs_dir, temp_dir or Path(tempfile.gettempdir())]
    for path in extras:
        if not path.expanduser().resolve().is_dir():
            raise LinuxSandboxError(f"Extra writable sandbox path is not a directory: {path}")
    try:
        for path in roots[1:]:
            path.expanduser().mkdir(parents=True, exist_ok=True)
        roots = _dedupe_paths([p.expanduser().resolve() for p in [*roots, *extras]])
        ruleset = _Ruleset(_WRITE)
        fd = _call(444, ctypes.byref(ruleset), ctypes.c_size_t(ctypes.sizeof(ruleset)), ctypes.c_uint(0))
        try:
            # Device writes were allowed by the former /dev bind mount.
            for root in [*roots, Path("/dev")]:
                parent = os.open(root, os.O_PATH | os.O_CLOEXEC)
                try:
                    rule = _PathRule(_WRITE, parent)
                    _call(445, ctypes.c_int(fd), ctypes.c_int(1), ctypes.byref(rule), ctypes.c_uint(0))
                finally:
                    os.close(parent)
            if _libc().prctl(38, 1, 0, 0, 0) != 0:
                raise LinuxSandboxError("Cannot set no_new_privs for Landlock")
            _call(446, ctypes.c_int(fd), ctypes.c_uint(0))
        finally:
            os.close(fd)
    except OSError as exc:
        raise LinuxSandboxError(f"Cannot configure Landlock: {exc}") from exc
    _entered = True
    os.environ[_SANDBOXED_ENV] = "1"  # informational, never trusted to bypass policy
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True

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
