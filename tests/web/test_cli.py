from __future__ import annotations

from pathlib import Path

import anyio
import pytest
from typer.testing import CliRunner

from tau_agent import UserMessage
from tau_agent.session import LeafEntry, MessageEntry, SessionInfoEntry
from tau_agent.session.jsonl import entry_to_json_line
from tau_coding import cli
from tau_coding.provider_config import DEFAULT_MODEL, DEFAULT_PROVIDER_NAME
from tau_web.sqlite.connection import SqliteDatabase
from tau_web.sqlite.interchange import JsonlImportOptions, SessionInterchange
from tau_web.sqlite.sessions import SessionRepository


def _jsonl_fixture() -> tuple[list[SessionInfoEntry | MessageEntry | LeafEntry], str]:
    info = SessionInfoEntry(id="info", cwd="/workspace", title="Imported")
    message = MessageEntry(
        id="message",
        parent_id=info.id,
        message=UserMessage(content="hello"),
    )
    leaf = LeafEntry(id="leaf", parent_id=message.id, entry_id=message.id)
    entries: list[SessionInfoEntry | MessageEntry | LeafEntry] = [info, message, leaf]
    return entries, "".join(entry_to_json_line(entry) for entry in entries)


def test_tau_web_command_uses_lazy_server_entrypoint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[tuple[Path, str, int, Path | None]] = []

    def fake_run(*, cwd: Path, host: str, port: int, database_path: Path | None = None) -> None:
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


def test_import_session_command_uses_default_sqlite_database_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(cli, "should_enter_macos_sandbox", lambda **_: False)
    monkeypatch.setattr(cli, "should_enter_linux_sandbox", lambda **_: False)
    monkeypatch.setenv("TAU_HOME", str(tmp_path / ".tau"))
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    monkeypatch.chdir(workspace_root)
    entries, jsonl_text = _jsonl_fixture()
    source = tmp_path / "incoming.jsonl"
    source.write_text(jsonl_text, encoding="utf-8")

    result = CliRunner().invoke(cli.app, ["import-session", str(source)])

    assert result.exit_code == 0, result.output
    assert "Imported session" in result.stdout
    assert not (tmp_path / ".tau" / "sessions").exists()

    async def inspect() -> None:
        async with SqliteDatabase(tmp_path / ".tau" / "tau.sqlite3") as database:
            session = await SessionRepository(database).resolve("@default")
            assert session is not None
            assert session.provider_name == DEFAULT_PROVIDER_NAME
            assert session.model == DEFAULT_MODEL
            exported = await SessionInterchange(database).export_jsonl(session.session_id)
            assert SessionInterchange(database).parse_jsonl(exported) == entries

    anyio.run(inspect)


def test_export_session_command_honours_output_and_overwrite(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(cli, "should_enter_macos_sandbox", lambda **_: False)
    monkeypatch.setattr(cli, "should_enter_linux_sandbox", lambda **_: False)
    _, jsonl_text = _jsonl_fixture()
    database_path = tmp_path / "runtime.sqlite3"

    async def seed() -> None:
        async with SqliteDatabase(database_path) as database:
            await SessionInterchange(database).import_jsonl(
                jsonl_text,
                options=JsonlImportOptions(
                    workspace_root=tmp_path / "workspace",
                    provider_name="test",
                    model="model",
                    session_id="exported",
                    agent_name="worker",
                ),
            )

    anyio.run(seed)
    output_path = tmp_path / "export" / "session.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("existing", encoding="utf-8")
    runner = CliRunner()

    blocked = runner.invoke(
        cli.app,
        [
            "export-session",
            "exported",
            "--format",
            "jsonl",
            "--database",
            str(database_path),
            "--output",
            str(output_path),
        ],
    )

    assert blocked.exit_code == 2
    assert "already exists" in blocked.stderr

    exported = runner.invoke(
        cli.app,
        [
            "export-session",
            "exported",
            "--format",
            "jsonl",
            "--database",
            str(database_path),
            "--output",
            str(output_path),
            "--overwrite",
        ],
    )

    assert exported.exit_code == 0, exported.output
    assert output_path.read_text(encoding="utf-8") == jsonl_text


def test_export_session_command_defaults_output_to_cwd(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(cli, "should_enter_macos_sandbox", lambda **_: False)
    monkeypatch.setattr(cli, "should_enter_linux_sandbox", lambda **_: False)
    _, jsonl_text = _jsonl_fixture()
    database_path = tmp_path / "runtime.sqlite3"

    async def seed() -> None:
        async with SqliteDatabase(database_path) as database:
            await SessionInterchange(database).import_jsonl(
                jsonl_text,
                options=JsonlImportOptions(
                    workspace_root=tmp_path / "workspace",
                    provider_name="test",
                    model="model",
                    session_id="exported",
                    agent_name="worker",
                ),
            )

    anyio.run(seed)
    export_dir = tmp_path / "exports"
    export_dir.mkdir()
    monkeypatch.chdir(export_dir)

    result = CliRunner().invoke(
        cli.app,
        [
            "export-session",
            "exported",
            "--format",
            "jsonl",
            "--database",
            str(database_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (export_dir / "exported.jsonl").read_text(encoding="utf-8") == jsonl_text
