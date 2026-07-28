from __future__ import annotations

import os
from pathlib import Path

import pytest

from tau_coding.linux_sandbox import (
    LinuxSandboxError,
    build_linux_bwrap_args,
    enter_linux_sandbox,
    extra_writable_paths_from_env,
    should_enter_linux_sandbox,
)
from tau_coding.paths import TauPaths


def test_should_enter_linux_sandbox_is_opt_in_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TAU_LINUX_SANDBOX", raising=False)
    monkeypatch.delenv("TAU_LINUX_SANDBOX_DEFAULT_ON", raising=False)

    assert (
        should_enter_linux_sandbox(
            disabled=False,
            platform="linux",
            bwrap_path="/usr/bin/bwrap",
        )
        is False
    )


def test_should_enter_linux_sandbox_honors_explicit_enable_and_disable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAU_LINUX_SANDBOX", "1")
    assert should_enter_linux_sandbox(disabled=False, platform="linux", bwrap_path=None) is True

    monkeypatch.setenv("TAU_LINUX_SANDBOX", "0")
    assert (
        should_enter_linux_sandbox(
            disabled=False,
            platform="linux",
            bwrap_path="/usr/bin/bwrap",
        )
        is False
    )

    monkeypatch.setenv("TAU_LINUX_SANDBOX", "1")
    assert (
        should_enter_linux_sandbox(
            disabled=True,
            platform="linux",
            bwrap_path="/usr/bin/bwrap",
        )
        is False
    )


def test_should_enter_linux_sandbox_supports_default_on_auto_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TAU_LINUX_SANDBOX", raising=False)
    monkeypatch.setenv("TAU_LINUX_SANDBOX_DEFAULT_ON", "1")
    monkeypatch.setattr("tau_coding.linux_sandbox.shutil.which", lambda _name: None)

    assert should_enter_linux_sandbox(
        disabled=False,
        platform="linux",
        bwrap_path="/usr/bin/bwrap",
    ) is True
    assert should_enter_linux_sandbox(disabled=False, platform="linux", bwrap_path=None) is False


def test_should_enter_linux_sandbox_skips_non_linux_and_existing_sandbox(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TAU_LINUX_SANDBOX", "1")
    assert (
        should_enter_linux_sandbox(
            disabled=False,
            platform="darwin",
            bwrap_path="/usr/bin/bwrap",
        )
        is False
    )

    monkeypatch.setenv("TAU_LINUX_SANDBOXED", "1")
    assert (
        should_enter_linux_sandbox(
            disabled=False,
            platform="linux",
            bwrap_path="/usr/bin/bwrap",
        )
        is False
    )


def test_extra_writable_paths_from_env_parses_pathsep() -> None:
    assert extra_writable_paths_from_env(f"/cache{os.pathsep}/var/tmp") == (
        Path("/cache"),
        Path("/var/tmp"),
    )
    assert extra_writable_paths_from_env("") == ()


def test_build_linux_bwrap_args_mounts_readonly_root_and_writable_roots(tmp_path: Path) -> None:
    project = tmp_path / "project"
    tau_home = tmp_path / ".tau"
    logs = tmp_path / "logs"
    tmp = tmp_path / "tmp"
    extra = tmp_path / "cache"
    for path in (project, tau_home, logs, tmp, extra):
        path.mkdir()

    args = build_linux_bwrap_args(
        executable=Path("/usr/bin/tau"),
        argv=["tau", "--version"],
        project_dir=project,
        tau_paths=TauPaths(home=tau_home, agents_home=tmp_path / ".agents"),
        temp_dir=tmp,
        extra_writable_paths=(extra,),
    )

    assert args[:4] == ["--die-with-parent", "--ro-bind", "/", "/"]
    project_bind = ["--bind", str(project.resolve()), str(project.resolve())]
    assert project_bind in [args[index : index + 3] for index in range(len(args) - 2)]
    assert "--dev-bind" in args
    assert "--proc" in args
    sandbox_marker = ["--setenv", "TAU_LINUX_SANDBOXED", "1"]
    assert sandbox_marker in [args[index : index + 3] for index in range(len(args) - 2)]
    assert args[-2:] == ["/usr/bin/tau", "--version"]


def test_build_linux_bwrap_args_rejects_missing_project(tmp_path: Path) -> None:
    with pytest.raises(LinuxSandboxError, match="Project directory does not exist"):
        build_linux_bwrap_args(
            executable=Path("/usr/bin/tau"),
            argv=["tau"],
            project_dir=tmp_path / "missing",
            tau_paths=TauPaths(home=tmp_path / ".tau", agents_home=tmp_path / ".agents"),
            temp_dir=tmp_path,
        )


def test_enter_linux_sandbox_reports_missing_bwrap(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    with pytest.raises(LinuxSandboxError, match="bubblewrap executable is not available"):
        enter_linux_sandbox(
            argv=["tau"],
            project_dir=project,
            tau_paths=TauPaths(home=tmp_path / ".tau", agents_home=tmp_path / ".agents"),
            bwrap_executable=tmp_path / "missing-bwrap",
            temp_dir=tmp_path,
        )


def test_enter_linux_sandbox_rejects_missing_extra_writable_path(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    bwrap = tmp_path / "bwrap"
    bwrap.write_text("#!/bin/sh\n", encoding="utf-8")
    bwrap.chmod(0o755)
    tau = tmp_path / "tau"
    tau.write_text("#!/bin/sh\n", encoding="utf-8")
    tau.chmod(0o755)

    with pytest.raises(LinuxSandboxError, match="Extra writable sandbox path is not a directory"):
        enter_linux_sandbox(
            argv=[str(tau)],
            project_dir=project,
            tau_paths=TauPaths(home=tmp_path / ".tau", agents_home=tmp_path / ".agents"),
            bwrap_executable=bwrap,
            temp_dir=tmp_path,
            extra_writable_paths=(tmp_path / "missing",),
        )
