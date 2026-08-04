from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from tau_coding import cli


def test_tau_web_command_uses_lazy_server_entrypoint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[tuple[Path, str, int, Path | None]] = []

    def fake_run(
        *, cwd: Path, host: str, port: int, database_path: Path | None = None
    ) -> None:
        calls.append((cwd, host, port, database_path))

    monkeypatch.setattr(cli, "should_enter_macos_sandbox", lambda **_: False)
    monkeypatch.setattr(cli, "should_enter_linux_sandbox", lambda **_: False)
    monkeypatch.setattr(cli, "run_tau_web_server", fake_run)
    database_path = tmp_path / "runtime.sqlite3"

    result = CliRunner().invoke(
        cli.app,
        [
            "web",
            "--cwd",
            str(tmp_path),
            "--host",
            "127.0.0.2",
            "--port",
            "9090",
            "--database",
            str(database_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [(tmp_path, "127.0.0.2", 9090, database_path)]


def test_tau_web_command_reports_missing_extra(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fail(**_: object) -> None:
        raise RuntimeError("install 'tau-prime[web]'")

    monkeypatch.setattr(cli, "should_enter_macos_sandbox", lambda **_: False)
    monkeypatch.setattr(cli, "should_enter_linux_sandbox", lambda **_: False)
    monkeypatch.setattr(cli, "run_tau_web_server", fail)

    result = CliRunner().invoke(cli.app, ["web", "--cwd", str(tmp_path)])

    assert result.exit_code == 1
    assert "tau-prime[web]" in result.stderr
