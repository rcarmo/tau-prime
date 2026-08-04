"""Command-line entry point for Tau."""

from __future__ import annotations

import shutil
import sys
from os import environ
from pathlib import Path
from typing import Annotated

import anyio
import typer
from typer import _click
from typer.core import TyperGroup

from tau_agent.session import JsonlSessionStorage, SessionEntry, SessionStorage
from tau_ai import (
    DEFAULT_OPENAI_COMPATIBLE_MAX_RETRIES,
    DEFAULT_OPENAI_COMPATIBLE_MAX_RETRY_DELAY_SECONDS,
    DEFAULT_OPENAI_COMPATIBLE_TIMEOUT_SECONDS,
    LLMObserver,
    ModelProvider,
)
from tau_ai.env import DEFAULT_OPENAI_COMPATIBLE_BASE_URL
from tau_coding import __version__
from tau_coding.credentials import FileCredentialStore
from tau_coding.diagnostics import llm_observer_from_env
from tau_coding.linux_sandbox import (
    LinuxSandboxError,
    enter_linux_sandbox,
    should_enter_linux_sandbox,
)
from tau_coding.macos_sandbox import (
    MacOSSandboxError,
    enter_macos_sandbox,
    should_enter_macos_sandbox,
)
from tau_coding.paths import TauPaths
from tau_coding.provider_config import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER_NAME,
    CredentialReader,
    OpenAICompatibleProviderConfig,
    ProviderConfig,
    ProviderSettings,
    ensure_dynamic_provider_models,
    load_provider_settings,
    provider_default_thinking_level,
    provider_kind,
    resolve_provider_selection,
    save_provider_settings,
    upsert_openai_compatible_provider,
)
from tau_coding.provider_runtime import create_model_provider
from tau_coding.rendering import PrintOutputMode, create_event_renderer
from tau_coding.resources import TauResourcePaths
from tau_coding.session import (
    CodingSession,
    CodingSessionConfig,
    TerminalCommandResult,
    jsonl_session_storage,
    parse_terminal_command,
)
from tau_coding.session_export import (
    default_session_export_artifact_path,
    export_session_artifact,
    normalize_export_format,
)
from tau_coding.session_manager import CodingSessionRecord, SessionManager, validate_session_id
from tau_coding.shell_config import load_shell_settings
from tau_coding.tui import run_tui_app
from tau_coding.update_check import (
    UpdateNotice,
    startup_update_notice,
    tau_prime_update_instructions,
)


class PromptCompatibleTyperGroup(TyperGroup):
    """Allow legacy positional prompts alongside registered subcommands."""

    def parse_args(self, ctx: _click.Context, args: list[str]) -> list[str]:
        if not args and self.no_args_is_help and not ctx.resilient_parsing:
            raise _click.exceptions.NoArgsIsHelpError(ctx)

        rest = _click.core.Command.parse_args(self, ctx, args)
        if not rest:
            return ctx.args

        command = self.get_command(ctx, rest[0])
        if command is None:
            ctx._protected_args = []
            ctx.args = rest
            return ctx.args

        ctx._protected_args, ctx.args = rest[:1], rest[1:]
        return ctx.args


app = typer.Typer(
    name="tau",
    cls=PromptCompatibleTyperGroup,
    help="Terminal coding agent.",
    add_completion=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)


def providers_command() -> None:
    """List configured model providers."""
    render_provider_settings(load_provider_settings(), credential_reader=FileCredentialStore())


def run_tau_web_server(
    *, cwd: Path, host: str, port: int, database_path: Path | None = None
) -> None:
    """Load and run the optional Tau Web server."""
    from tau_web.app import run
    from tau_web.config import WebConfig

    run(WebConfig(cwd=cwd, host=host, port=port, database_path=database_path))


def setup_command(
    *,
    provider_name: str = DEFAULT_PROVIDER_NAME,
    base_url: str = DEFAULT_OPENAI_COMPATIBLE_BASE_URL,
    api_key_env: str = "OPENAI_API_KEY",
    model: str = DEFAULT_MODEL,
    timeout_seconds: float = DEFAULT_OPENAI_COMPATIBLE_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_OPENAI_COMPATIBLE_MAX_RETRIES,
    max_retry_delay_seconds: float = DEFAULT_OPENAI_COMPATIBLE_MAX_RETRY_DELAY_SECONDS,
    set_default: bool = True,
) -> None:
    """Create or update an OpenAI-compatible provider entry."""
    settings = load_provider_settings()
    provider = OpenAICompatibleProviderConfig(
        name=provider_name,
        base_url=base_url.rstrip("/"),
        api_key_env=api_key_env,
        models=(model,),
        default_model=model,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
        max_retry_delay_seconds=max_retry_delay_seconds,
    )
    updated = upsert_openai_compatible_provider(settings, provider, set_default=set_default)
    path = save_provider_settings(updated)
    typer.echo(f"Saved provider '{provider.name}' to {path}")
    if provider.api_key_env not in environ:
        typer.echo(f"Set {provider.api_key_env} before running Tau with this provider.", err=True)


@app.command("import-session")
def import_session_cli(
    source_path: Annotated[
        Path,
        typer.Argument(help="Tau JSONL session file to import into the SQLite session store."),
    ],
    workspace_root: Annotated[
        Path | None,
        typer.Option(
            "--workspace",
            "--cwd",
            help="Workspace root to record for the imported SQLite session.",
        ),
    ] = None,
    provider: Annotated[
        str | None,
        typer.Option("--provider", help="Configured provider name to record for the import."),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", help="Model name to record for the import."),
    ] = None,
    database_path: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path for session import/export."),
    ] = None,
    session_id: Annotated[
        str | None,
        typer.Option("--session-id", help="Exact SQLite session id to assign."),
    ] = None,
    agent_name: Annotated[
        str | None,
        typer.Option("--agent-name", "--name", help="Agent name to assign to the import."),
    ] = None,
    title: Annotated[
        str | None,
        typer.Option("--title", help="Session title to record for the import."),
    ] = None,
    thinking_level: Annotated[
        str | None,
        typer.Option("--thinking-level", help="Thinking level metadata to record."),
    ] = None,
) -> None:
    """Import a JSONL session into Tau's SQLite session store."""
    if session_id is not None:
        try:
            validate_session_id(session_id)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
    selected_workspace_root = workspace_root or Path.cwd()
    try:
        imported_session_id, imported_agent_name, imported_entry_count, selected_database = (
            anyio.run(
                import_sqlite_session_command,
                source_path,
                selected_workspace_root,
                provider,
                model,
                database_path,
                session_id,
                agent_name,
                title,
                thinking_level,
            )
        )
    except (RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(
        f"Imported session {imported_session_id} as @{imported_agent_name} "
        f"({imported_entry_count} entries) into {selected_database}"
    )


@app.command("export-session")
def export_session_cli(
    session_ref: Annotated[
        str,
        typer.Argument(help="SQLite session id or local address to export as Tau JSONL."),
    ],
    export_format: Annotated[
        str,
        typer.Option("--format", help="Export format (only jsonl is currently supported)."),
    ] = "jsonl",
    output_path: Annotated[
        Path | None,
        typer.Option("--output", help="Destination path for the exported JSONL file."),
    ] = None,
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite/--no-overwrite",
            help="Allow overwriting an existing JSONL export file.",
        ),
    ] = False,
    database_path: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path for session import/export."),
    ] = None,
) -> None:
    """Export one SQLite-backed session as Tau JSONL."""
    try:
        exported_path = anyio.run(
            export_sqlite_session_command,
            session_ref,
            output_path,
            export_format,
            overwrite,
            database_path,
        )
    except (RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Exported session to {exported_path}")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    prompt_option: Annotated[
        str | None,
        typer.Option("--prompt", "-p", help="Prompt to run in non-interactive print mode."),
    ] = None,
    provider: Annotated[
        str | None,
        typer.Option("--provider", help="Configured provider name to use."),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", "-m", help="Model name to request from the provider."),
    ] = None,
    setup_base_url: Annotated[
        str,
        typer.Option("--base-url", help="OpenAI-compatible base URL for `tau setup`."),
    ] = DEFAULT_OPENAI_COMPATIBLE_BASE_URL,
    setup_api_key_env: Annotated[
        str,
        typer.Option("--api-key-env", help="API key environment variable for `tau setup`."),
    ] = "OPENAI_API_KEY",
    setup_timeout_seconds: Annotated[
        float,
        typer.Option(
            "--timeout-seconds",
            help="HTTP timeout in seconds for `tau setup` provider requests.",
        ),
    ] = DEFAULT_OPENAI_COMPATIBLE_TIMEOUT_SECONDS,
    setup_max_retries: Annotated[
        int,
        typer.Option("--max-retries", help="Provider retry count for `tau setup`."),
    ] = DEFAULT_OPENAI_COMPATIBLE_MAX_RETRIES,
    setup_max_retry_delay_seconds: Annotated[
        float,
        typer.Option(
            "--max-retry-delay-seconds",
            help="Provider retry delay in seconds for `tau setup`.",
        ),
    ] = DEFAULT_OPENAI_COMPATIBLE_MAX_RETRY_DELAY_SECONDS,
    setup_default: Annotated[
        bool,
        typer.Option("--set-default/--no-set-default", help="Make setup provider the default."),
    ] = True,
    cwd: Annotated[
        Path | None,
        typer.Option("--cwd", help="Working directory for built-in coding tools."),
    ] = None,
    output: Annotated[
        PrintOutputMode,
        typer.Option("--output", "-o", help="Output mode for print mode."),
    ] = PrintOutputMode.text,
    resume: Annotated[
        str | None,
        typer.Option("--resume", help="Resume a session id in TUI mode."),
    ] = None,
    new_session: Annotated[
        bool,
        typer.Option("--new-session", help="Create a new session in TUI mode (default)."),
    ] = False,
    session_id: Annotated[
        str | None,
        typer.Option(
            "--session-id",
            help="Set the exact id for the newly created print-mode session.",
        ),
    ] = None,
    auto_compact_threshold: Annotated[
        int | None,
        typer.Option(
            "--auto-compact-threshold",
            help="Automatically compact TUI context above this rough token estimate.",
        ),
    ] = None,
    web: Annotated[
        bool,
        typer.Option("--web", help="Run the Textual TUI through Textual's web server."),
    ] = False,
    web_host: Annotated[
        str,
        typer.Option(
            "--web-host",
            "--web-address",
            "--host",
            help="Host/address for Textual or Tau web server mode.",
        ),
    ] = "127.0.0.1",
    web_port: Annotated[
        int,
        typer.Option("--web-port", help="Port for Textual web server mode."),
    ] = 8000,
    tau_web_port: Annotated[
        int,
        typer.Option("--port", help="Port for `tau web`."),
    ] = 8080,
    web_database: Annotated[
        Path | None,
        typer.Option("--database", help="SQLite database path for `tau web`."),
    ] = None,
    no_sandbox: Annotated[
        bool,
        typer.Option(
            "--no-sandbox",
            help="Disable the default macOS filesystem sandbox.",
        ),
    ] = False,
    version: Annotated[
        bool,
        typer.Option("--version", help="Show Tau's version and exit."),
    ] = False,
) -> None:
    """Run the Tau CLI."""
    if version:
        typer.echo(f"tau {__version__}")
        raise typer.Exit()

    if should_enter_macos_sandbox(disabled=no_sandbox):
        try:
            enter_macos_sandbox(argv=sys.argv, project_dir=(cwd or Path.cwd()).resolve())
        except MacOSSandboxError as exc:
            typer.echo(
                f"Could not establish the required macOS sandbox: {exc}\n"
                "Use --no-sandbox only if unsandboxed execution is intentional.",
                err=True,
            )
            raise typer.Exit(code=1) from exc

    if should_enter_linux_sandbox(disabled=no_sandbox):
        try:
            enter_linux_sandbox(argv=sys.argv, project_dir=(cwd or Path.cwd()).resolve())
        except LinuxSandboxError as exc:
            typer.echo(
                f"Could not establish the requested Linux sandbox: {exc}\n"
                "Use --no-sandbox only if unsandboxed execution is intentional.",
                err=True,
            )
            raise typer.Exit(code=1) from exc

    if ctx.invoked_subcommand is not None:
        return

    if session_id is not None:
        try:
            validate_session_id(session_id)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc

    positional_args = list(ctx.args)
    command = positional_args[0] if positional_args else None
    initial_prompt = " ".join(positional_args) if positional_args else None

    if prompt_option is None and command == "web":
        try:
            web_cwd, host, port, database_path = _parse_web_cli_args(
                positional_args[1:],
                cwd=cwd or Path.cwd(),
                host=web_host,
                port=tau_web_port,
                database_path=web_database,
            )
            run_tau_web_server(
                cwd=web_cwd,
                host=host,
                port=port,
                database_path=database_path,
            )
        except (RuntimeError, ValueError) as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc
        raise typer.Exit()

    if prompt_option is None and command == "sessions" and len(positional_args) == 1:
        render_session_list(SessionManager().list_sessions())
        raise typer.Exit()

    if prompt_option is None and command == "export":
        try:
            session_ref, output_path, export_format = _parse_export_cli_args(positional_args[1:])
        except RuntimeError as exc:
            raise typer.BadParameter(str(exc)) from exc
        try:
            exported_path = anyio.run(
                export_session_command,
                session_ref,
                output_path,
                export_format,
            )
        except (RuntimeError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc
        typer.echo(f"Exported session to {exported_path}")
        raise typer.Exit()

    if prompt_option is None and command == "providers" and len(positional_args) == 1:
        providers_command()
        raise typer.Exit()

    if prompt_option is None and command == "update" and len(positional_args) == 1:
        typer.echo(tau_prime_update_instructions())
        raise typer.Exit()

    if prompt_option is None and command == "setup" and len(positional_args) == 1:
        setup_command(
            provider_name=provider or DEFAULT_PROVIDER_NAME,
            base_url=setup_base_url,
            api_key_env=setup_api_key_env,
            model=model or DEFAULT_MODEL,
            timeout_seconds=setup_timeout_seconds,
            max_retries=setup_max_retries,
            max_retry_delay_seconds=setup_max_retry_delay_seconds,
            set_default=setup_default,
        )
        raise typer.Exit()

    if prompt_option is None:
        if session_id is not None:
            raise typer.BadParameter("--session-id is only supported in print mode")
        notice = _startup_update_notice()
        if _use_basic_repl():
            run_basic_repl(
                model=model,
                cwd=cwd or Path.cwd(),
                provider_name=provider,
                output=output,
                initial_prompt=initial_prompt,
                notice=notice,
            )
            raise typer.Exit()
        try:
            if web:
                anyio.run(
                    run_textual_web_tui,
                    model,
                    cwd or Path.cwd(),
                    resume,
                    new_session,
                    provider,
                    auto_compact_threshold,
                    initial_prompt,
                    web_host,
                    web_port,
                    notice,
                )
            else:
                resumable_session_id = anyio.run(
                    run_openai_tui,
                    model,
                    cwd or Path.cwd(),
                    resume,
                    new_session,
                    provider,
                    auto_compact_threshold,
                    initial_prompt,
                    notice,
                )
                if resumable_session_id is not None:
                    typer.echo(f"To resume this session: tau --resume {resumable_session_id}")
        except (RuntimeError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc
        raise typer.Exit()

    prompt = prompt_option
    if prompt is None:
        raise AssertionError("prompt option should be set outside TUI mode")

    notice = _startup_update_notice()
    if notice is not None and output is PrintOutputMode.text:
        typer.echo(notice.message, err=True)

    try:
        if session_id is None:
            ok = anyio.run(
                run_openai_print_mode,
                prompt,
                model,
                cwd or Path.cwd(),
                output,
                provider,
            )
        else:
            ok = anyio.run(
                run_openai_print_mode,
                prompt,
                model,
                cwd or Path.cwd(),
                output,
                provider,
                session_id,
            )
    except (RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    if not ok:
        raise typer.Exit(1)


async def run_openai_tui(
    model: str | None,
    cwd: Path,
    session_id: str | None = None,
    new_session: bool = False,
    provider_name: str | None = None,
    auto_compact_token_threshold: int | None = None,
    initial_prompt: str | None = None,
    update_notice: UpdateNotice | None = None,
) -> str | None:
    """Run the Textual TUI with the default OpenAI-compatible provider."""
    return await run_tui_app(
        model=model,
        cwd=cwd,
        session_id=session_id,
        new_session=new_session,
        provider_name=provider_name,
        auto_compact_token_threshold=auto_compact_token_threshold,
        initial_prompt=initial_prompt,
        startup_notice=update_notice.message if update_notice is not None else None,
    )


async def run_textual_web_tui(
    model: str | None,
    cwd: Path,
    session_id: str | None = None,
    new_session: bool = False,
    provider_name: str | None = None,
    auto_compact_token_threshold: int | None = None,
    initial_prompt: str | None = None,
    web_host: str = "127.0.0.1",
    web_port: int = 8000,
    update_notice: UpdateNotice | None = None,
) -> None:
    """Run the Textual TUI via Textual's optional web server command."""
    if not 1 <= web_port <= 65535:
        raise RuntimeError("--web-port must be between 1 and 65535")
    command = _textual_web_command(
        model=model,
        cwd=cwd,
        session_id=session_id,
        new_session=new_session,
        provider_name=provider_name,
        auto_compact_token_threshold=auto_compact_token_threshold,
        initial_prompt=initial_prompt,
        web_host=web_host,
        web_port=web_port,
        update_notice=update_notice,
    )
    result = await anyio.run_process(command, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Textual web server exited with status {result.returncode}")


def _textual_web_command(
    *,
    model: str | None,
    cwd: Path,
    session_id: str | None,
    new_session: bool,
    provider_name: str | None,
    auto_compact_token_threshold: int | None,
    initial_prompt: str | None,
    web_host: str,
    web_port: int,
    update_notice: UpdateNotice | None,
) -> list[str]:
    executable = shutil.which("textual-web") or shutil.which("textual-serve")
    if executable is None:
        raise RuntimeError(
            "Textual web server support requires the optional `textual-web` command. "
            "Install Textual's web server package, then run Tau with --web."
        )

    tau_command = [sys.executable, "-m", "tau_coding"]
    if model is not None:
        tau_command.extend(["--model", model])
    if provider_name is not None:
        tau_command.extend(["--provider", provider_name])
    if session_id is not None:
        tau_command.extend(["--resume", session_id])
    if new_session:
        tau_command.append("--new-session")
    if auto_compact_token_threshold is not None:
        tau_command.extend(["--auto-compact-threshold", str(auto_compact_token_threshold)])
    tau_command.extend(["--cwd", str(cwd)])
    del update_notice
    if initial_prompt is not None:
        tau_command.append(initial_prompt)

    return [
        executable,
        "--host",
        web_host,
        "--port",
        str(web_port),
        "--",
        *tau_command,
    ]


def _startup_update_notice() -> UpdateNotice | None:
    return startup_update_notice(__version__)


def _use_basic_repl() -> bool:
    """Return true when the user explicitly avoids the Textual TUI."""
    if environ.get("TAU_TEXTUAL") in {"1", "true", "yes"}:
        return False
    return environ.get("TAU_BASIC_REPL") in {"1", "true", "yes"}


def run_basic_repl(
    *,
    model: str | None,
    cwd: Path,
    provider_name: str | None,
    output: PrintOutputMode,
    initial_prompt: str | None = None,
    notice: UpdateNotice | None = None,
) -> None:
    """Run a minimal stdin/stdout prompt loop for terminals unsupported by Textual."""
    if notice is not None and output is PrintOutputMode.text:
        typer.echo(notice.message, err=True)
    typer.echo("Tau basic mode. Type a prompt and press Enter; /exit or Ctrl-D exits.")

    def run_one(prompt: str) -> None:
        try:
            ok = anyio.run(run_openai_print_mode, prompt, model, cwd, output, provider_name)
        except RuntimeError as exc:
            typer.echo(f"Error: {exc}", err=True)
            return
        if not ok:
            typer.echo("Prompt failed.", err=True)

    if initial_prompt:
        run_one(initial_prompt)

    while True:
        try:
            prompt = input("tau> ").strip()
        except EOFError:
            typer.echo("")
            return
        if not prompt:
            continue
        if prompt in {"/exit", "/quit", "exit", "quit"}:
            return
        run_one(prompt)


def render_session_list(records: list[CodingSessionRecord]) -> None:
    """Render indexed sessions for the CLI."""
    if not records:
        typer.echo("No sessions found.")
        return

    for record in records:
        title = record.title or "Untitled"
        typer.echo(f"{record.id}\t{title}\t{record.model}\t{record.cwd}")


async def export_session_command(
    session_ref: str,
    output_path: Path | None = None,
    export_format: str | None = None,
    session_manager: SessionManager | None = None,
) -> Path:
    """Export an indexed session id or JSONL file path."""
    session_path, title = _resolve_export_source(session_ref, session_manager)
    entries = await JsonlSessionStorage(session_path).read_all()
    normalized_format = normalize_export_format(
        export_format or (output_path.suffix.removeprefix(".") if output_path else "html")
    )
    destination = _resolve_export_destination(
        output_path,
        session_path=session_path,
        format=normalized_format,
    )
    return export_session_artifact(
        entries,
        destination,
        title=title,
        source=str(session_path),
        format=normalized_format,
    )


async def import_sqlite_session_command(
    source_path: Path,
    workspace_root: Path,
    provider_name: str | None,
    model: str | None,
    database_path: Path | None,
    session_id: str | None,
    agent_name: str | None,
    title: str | None,
    thinking_level: str | None,
) -> tuple[str, str, int, Path]:
    try:
        from tau_web.sqlite.connection import SqliteDatabase
        from tau_web.sqlite.interchange import JsonlImportOptions, SessionInterchange
    except ModuleNotFoundError as exc:
        raise RuntimeError("Install 'tau-prime[web]' to use SQLite session import/export") from exc

    resolved_source = source_path.expanduser().resolve()
    if not resolved_source.exists():
        raise ValueError(f"Session import source does not exist: {resolved_source}")
    if not resolved_source.is_file():
        raise ValueError(f"Session import source is not a file: {resolved_source}")

    settings = load_provider_settings()
    selection = resolve_provider_selection(settings, provider_name=provider_name, model=model)
    selected_database = _resolve_sqlite_database_path(database_path)
    selected_thinking_level = thinking_level or provider_default_thinking_level(
        selection.provider,
        model=selection.model,
    )
    async with SqliteDatabase(selected_database) as database:
        result = await SessionInterchange(database).import_jsonl_file(
            resolved_source,
            options=JsonlImportOptions(
                workspace_root=workspace_root,
                provider_name=selection.provider.name,
                model=selection.model,
                session_id=session_id,
                agent_name=agent_name,
                title=title,
                thinking_level=selected_thinking_level,
                metadata={"imported_via": "tau import-session"},
            ),
        )
    return result.session_id, result.agent_name, result.entry_count, selected_database


async def export_sqlite_session_command(
    session_ref: str,
    output_path: Path | None,
    export_format: str,
    overwrite: bool,
    database_path: Path | None,
) -> Path:
    if export_format.strip().casefold() != "jsonl":
        raise ValueError("`tau export-session` only supports --format jsonl")

    try:
        from tau_web.sqlite.connection import SqliteDatabase
        from tau_web.sqlite.interchange import SessionInterchange
        from tau_web.sqlite.sessions import SessionRepository
    except ModuleNotFoundError as exc:
        raise RuntimeError("Install 'tau-prime[web]' to use SQLite session import/export") from exc

    selected_database = _resolve_sqlite_database_path(database_path)
    async with SqliteDatabase(selected_database) as database:
        record = await SessionRepository(database).resolve(session_ref)
        if record is None:
            raise RuntimeError(f"Unknown session: {session_ref}")
        destination = _resolve_sqlite_session_export_destination(
            output_path,
            session_id=record.session_id,
        )
        return await SessionInterchange(database).export_jsonl_file(
            record.session_id,
            destination,
            overwrite=overwrite,
        )


def _resolve_sqlite_database_path(database_path: Path | None) -> Path:
    return (database_path or TauPaths().home / "tau.sqlite3").expanduser().resolve()


def _resolve_sqlite_session_export_destination(
    output_path: Path | None,
    *,
    session_id: str,
) -> Path:
    if output_path is None:
        return Path.cwd() / f"{session_id}.jsonl"
    candidate = output_path.expanduser()
    if candidate.exists() and candidate.is_dir():
        return candidate / f"{session_id}.jsonl"
    return candidate


def _parse_web_cli_args(
    args: list[str],
    *,
    cwd: Path,
    host: str,
    port: int,
    database_path: Path | None,
) -> tuple[Path, str, int, Path | None]:
    """Parse options following the callback-style ``tau web`` command token."""
    values: dict[str, str] = {}
    index = 0
    option_names = {"--cwd", "--host", "--port", "--database"}
    while index < len(args):
        option = args[index]
        if option not in option_names:
            raise RuntimeError(f"Unknown `tau web` argument: {option}")
        if index + 1 >= len(args):
            raise RuntimeError(f"Missing value for `tau web` option: {option}")
        values[option] = args[index + 1]
        index += 2

    selected_cwd = Path(values["--cwd"]) if "--cwd" in values else cwd
    selected_database = Path(values["--database"]) if "--database" in values else database_path
    try:
        selected_port = int(values["--port"]) if "--port" in values else port
    except ValueError as exc:
        raise RuntimeError("`tau web --port` must be an integer") from exc
    return selected_cwd, values.get("--host", host), selected_port, selected_database


def _parse_export_cli_args(args: list[str]) -> tuple[str, Path | None, str | None]:
    if not args:
        raise RuntimeError("Usage: tau export <session-id-or-jsonl> [--format html|jsonl] [output]")
    session_ref = args[0]
    output_path: Path | None = None
    export_format: str | None = None
    index = 1
    while index < len(args):
        arg = args[index]
        if arg == "--format":
            index += 1
            if index >= len(args):
                raise RuntimeError(
                    "Usage: tau export <session-id-or-jsonl> [--format html|jsonl] [output]"
                )
            export_format = args[index]
        elif arg.startswith("--format="):
            export_format = arg.partition("=")[2]
        elif arg.startswith("-"):
            raise RuntimeError(f"Unknown export option: {arg}")
        elif output_path is None:
            output_path = Path(arg).expanduser()
        else:
            raise RuntimeError(
                "Usage: tau export <session-id-or-jsonl> [--format html|jsonl] [output]"
            )
        index += 1
    return session_ref, output_path, export_format


def _resolve_export_destination(
    output_path: Path | None,
    *,
    session_path: Path,
    format: str,
) -> Path:
    if output_path is None:
        return default_session_export_artifact_path(
            session_path,
            destination_dir=Path.cwd(),
            format=format,
        )
    if output_path.suffix:
        return output_path
    return default_session_export_artifact_path(
        session_path,
        destination_dir=output_path,
        format=format,
    )


def _resolve_export_source(
    session_ref: str,
    session_manager: SessionManager | None = None,
) -> tuple[Path, str]:
    candidate_path = Path(session_ref).expanduser()
    if candidate_path.exists():
        if candidate_path.is_dir():
            raise RuntimeError(f"Session export source is a directory: {candidate_path}")
        return candidate_path, f"Tau session {candidate_path.stem}"

    manager = session_manager or SessionManager()
    record = manager.get_session(session_ref)
    if record is None:
        raise RuntimeError(f"Unknown session or file: {session_ref}")

    title = record.title or f"Tau session {record.id}"
    return record.path, title


def render_provider_settings(
    settings: ProviderSettings,
    *,
    credential_reader: CredentialReader | None = None,
) -> None:
    """Render configured providers for the CLI."""
    for provider in settings.providers:
        marker = "*" if provider.name == settings.default_provider else " "
        models = ",".join(provider.models)
        typer.echo(
            f"{marker}\t{provider.name}\t{provider_kind(provider)}\t"
            f"{provider.default_model}\t{models}\t{provider.api_key_env}\t"
            f"{_provider_credential_status(provider, credential_reader=credential_reader)}\t"
            f"{provider.base_url}\t{provider.timeout_seconds:g}s\t"
            f"retries={provider.max_retries}\t"
            f"retry_delay={provider.max_retry_delay_seconds:g}s"
        )


def _provider_credential_status(
    provider: ProviderConfig,
    *,
    credential_reader: CredentialReader | None,
) -> str:
    if provider.credential_name and credential_reader is not None:
        if provider_kind(provider) == "openai-codex" or provider.name == "github-copilot":
            get_oauth = getattr(credential_reader, "get_oauth", None)
            if get_oauth is not None and get_oauth(provider.credential_name) is not None:
                return f"stored:{provider.credential_name}"
        if credential_reader.get(provider.credential_name):
            return f"stored:{provider.credential_name}"
    if environ.get(provider.api_key_env):
        return f"env:{provider.api_key_env}"
    return "missing"


async def run_openai_print_mode(
    prompt: str,
    model: str | None,
    cwd: Path,
    output: PrintOutputMode = PrintOutputMode.text,
    provider_name: str | None = None,
    session_id: str | None = None,
    session_manager: SessionManager | None = None,
) -> bool:
    """Run print mode with the OpenAI-compatible provider configured from the environment."""
    settings = load_provider_settings()
    shell_settings = load_shell_settings()
    target_provider = provider_name or settings.default_provider
    settings = await ensure_dynamic_provider_models(settings, provider_name=target_provider)
    selection = resolve_provider_selection(settings, provider_name=provider_name, model=model)
    llm_observer = llm_observer_from_env()
    provider = create_model_provider(
        selection.provider,
        model=selection.model,
        thinking_level=provider_default_thinking_level(selection.provider, model=selection.model),
        llm_observer=llm_observer,
    )
    manager = session_manager or SessionManager()
    record = _create_print_session(manager, cwd=cwd, model=selection.model, session_id=session_id)
    try:
        return await run_print_mode(
            prompt=prompt,
            model=selection.model,
            cwd=record.cwd,
            provider=provider,
            output=output,
            storage=jsonl_session_storage(record.path),
            session_id=record.id,
            session_manager=manager,
            provider_name=selection.provider.name,
            provider_settings=settings,
            runtime_provider_config=selection.provider,
            shell_command_prefix=shell_settings.shell_command_prefix,
            llm_observer=llm_observer,
        )
    finally:
        await provider.aclose()


def _create_print_session(
    manager: SessionManager,
    *,
    cwd: Path,
    model: str,
    session_id: str | None,
) -> CodingSessionRecord:
    """Create a print-mode session without risking transcript collisions."""
    return manager.create_session_exclusive(cwd=cwd, model=model, session_id=session_id)


async def run_print_mode(
    *,
    prompt: str,
    model: str,
    cwd: Path,
    provider: ModelProvider,
    output: PrintOutputMode = PrintOutputMode.text,
    resource_paths: TauResourcePaths | None = None,
    storage: SessionStorage | None = None,
    session_id: str | None = None,
    session_manager: SessionManager | None = None,
    provider_name: str = DEFAULT_PROVIDER_NAME,
    provider_settings: ProviderSettings | None = None,
    runtime_provider_config: ProviderConfig | None = None,
    shell_command_prefix: str | None = None,
    llm_observer: LLMObserver | None = None,
) -> bool:
    """Run one non-interactive prompt and print streamed events.

    Returns False when the agent emits a non-recoverable error so CLI callers
    can fail non-interactive runs while still rendering the error message.
    """
    session = await CodingSession.load(
        CodingSessionConfig(
            provider=provider,
            model=model,
            cwd=cwd,
            storage=storage or _MemorySessionStorage(),
            resource_paths=resource_paths,
            session_id=session_id,
            session_manager=session_manager,
            provider_name=provider_name,
            provider_settings=provider_settings,
            runtime_provider_config=runtime_provider_config,
            shell_command_prefix=shell_command_prefix,
            llm_observer=llm_observer,
        )
    )
    renderer = create_event_renderer(output)
    try:
        terminal_command = parse_terminal_command(prompt)
        if terminal_command is not None:
            result = await session.run_terminal_command(
                terminal_command.command,
                add_to_context=terminal_command.add_to_context,
            )
            typer.echo(_format_terminal_command_result(result))
            return result.ok
        command = session.handle_command(prompt)
        if command.handled:
            if command.message:
                typer.echo(command.message)
            return True
        async for event in session.prompt(prompt):
            renderer.render(event)
        return renderer.finish()
    finally:
        await session.aclose()


class _MemorySessionStorage:
    """Append-only in-memory storage for direct print-mode tests."""

    def __init__(self) -> None:
        self.entries: list[SessionEntry] = []

    async def append(self, entry: SessionEntry) -> None:
        self.entries.append(entry)

    async def read_all(self) -> list[SessionEntry]:
        return list(self.entries)


def _format_terminal_command_result(result: TerminalCommandResult) -> str:
    context_status = "added to context" if result.added_to_context else "not added to context"
    return f"$ {result.command}\n[{context_status}]\n{result.output}"
