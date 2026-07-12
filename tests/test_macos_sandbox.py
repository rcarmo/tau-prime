import os
from pathlib import Path

import pytest

from tau_coding.macos_sandbox import (
    MacOSSandboxError,
    build_macos_sandbox_profile,
    enter_macos_sandbox,
    should_enter_macos_sandbox,
)
from tau_coding.paths import TauPaths


def test_should_enter_macos_sandbox_only_on_unsandboxed_macos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TAU_MACOS_SANDBOXED", raising=False)

    assert should_enter_macos_sandbox(disabled=False, platform="darwin")
    assert not should_enter_macos_sandbox(disabled=True, platform="darwin")
    assert not should_enter_macos_sandbox(disabled=False, platform="linux")

    monkeypatch.setenv("TAU_MACOS_SANDBOXED", "1")
    assert not should_enter_macos_sandbox(disabled=False, platform="darwin")


def test_profile_allows_only_project_tau_logs_and_tmp_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / 'project "quoted"'
    home = tmp_path / "config"
    logs = tmp_path / "logs"
    temp = tmp_path / "temporary"
    monkeypatch.setenv("TAU_LOGS_DIR", str(logs))

    profile = build_macos_sandbox_profile(
        project_dir=project,
        paths=TauPaths(home=home),
        tmpdir=temp,
    )

    assert "(allow default)" in profile
    assert "(deny file-write*)" in profile
    assert f"(subpath {project.resolve().as_posix()!r})" not in profile
    assert f'(subpath "{home.resolve()}")' in profile
    assert f'(subpath "{logs.resolve()}")' in profile
    assert f'(subpath "{temp.resolve()}")' in profile
    assert '\\"quoted\\"' in profile
    assert "/Users/example" not in profile


def test_profile_removes_writable_roots_nested_under_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    profile = build_macos_sandbox_profile(
        project_dir=project,
        paths=TauPaths(home=project / ".tau"),
        tmpdir=project / ".tmp",
    )

    assert profile.count("(allow file-write* (subpath") == 1
    assert f'(subpath "{project.resolve()}")' in profile


def test_enter_macos_sandbox_reexecutes_and_sets_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sandbox_exec = tmp_path / "sandbox-exec"
    sandbox_exec.write_text("", encoding="utf-8")
    sandbox_exec.chmod(0o755)
    tau = tmp_path / "tau"
    tau.write_text("", encoding="utf-8")
    tau.chmod(0o755)
    (tmp_path / "project").mkdir()
    captured: dict[str, object] = {}

    class ExecCalled(Exception):
        pass

    def fake_execve(path: str, argv: list[str], env: dict[str, str]) -> None:
        captured.update(path=path, argv=argv, env=env)
        raise ExecCalled

    monkeypatch.setattr(os, "execve", fake_execve)

    with pytest.raises(ExecCalled):
        enter_macos_sandbox(
            argv=[str(tau), "--model", "local"],
            project_dir=tmp_path / "project",
            paths=TauPaths(home=tmp_path / "config"),
            sandbox_exec=sandbox_exec,
        )

    assert captured["path"] == str(sandbox_exec)
    argv = captured["argv"]
    assert isinstance(argv, list)
    assert argv[:2] == [str(sandbox_exec), "-p"]
    assert argv[-3:] == [str(tau.resolve()), "--model", "local"]
    env = captured["env"]
    assert isinstance(env, dict)
    assert env["TAU_MACOS_SANDBOXED"] == "1"


def test_enter_macos_sandbox_fails_when_cli_is_unavailable(tmp_path: Path) -> None:
    with pytest.raises(MacOSSandboxError, match="unavailable"):
        enter_macos_sandbox(
            argv=["tau"],
            project_dir=tmp_path,
            paths=TauPaths(home=tmp_path / "config"),
            sandbox_exec=tmp_path / "missing-sandbox-exec",
        )
