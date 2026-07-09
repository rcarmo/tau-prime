"""Built-in filesystem and shell tools for Tau coding sessions.

The module exposes factory functions that create provider-neutral `AgentTool`
objects plus richer `ToolDefinition` objects for callers that need prompt
metadata and JSON schemas. The tools operate relative to a configurable working
directory, return structured `AgentToolResult` values, and keep local
filesystem/shell behavior outside the reusable `tau_agent` package.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import mimetypes
import os
import signal
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from time import monotonic
from typing import Any

from tau_agent.tools import AgentTool, AgentToolResult, ToolCancellationToken, ToolExecutor
from tau_agent.types import JSONValue

DEFAULT_MAX_OUTPUT_BYTES = 50 * 1024
DEFAULT_MAX_OUTPUT_LINES = 2_000
STREAMING_EDIT_MIN_BYTES = 512 * 1024
STREAMING_EDIT_CHUNK_BYTES = 64 * 1024
SUPPORTED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
UTF8_BOM = "\ufeff"


class ToolInputError(ValueError):
    """Raised when a tool receives invalid structured arguments."""


@dataclass(frozen=True, slots=True)
class TruncationResult:
    """Metadata describing how a tool output was shortened.

    `content` contains the returned slice. The remaining fields record whether
    truncation happened, whether the line or byte limit was responsible, the
    total size of the original output, the size of the returned output, and
    edge cases such as partial-line output or a first line that is too large to
    display safely.
    """

    content: str
    truncated: bool
    truncated_by: str | None
    total_lines: int
    total_bytes: int
    output_lines: int
    output_bytes: int
    last_line_partial: bool
    first_line_exceeds_limit: bool
    max_lines: int
    max_bytes: int

    def to_json(self) -> dict[str, JSONValue]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """Complete definition for a coding tool before provider conversion.

    A definition contains the tool name, user-facing description, prompt
    metadata, JSON input schema, and async executor. `to_agent_tool()` converts
    it into the smaller `AgentTool` type consumed by the provider-neutral agent
    loop while preserving prompt metadata for clients that render tool guidance.
    """

    name: str
    description: str
    prompt_snippet: str
    prompt_guidelines: tuple[str, ...]
    input_schema: Mapping[str, JSONValue]
    executor: ToolExecutor

    def to_agent_tool(self) -> AgentTool:
        return AgentTool(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            executor=self.executor,
            prompt_snippet=self.prompt_snippet,
            prompt_guidelines=self.prompt_guidelines,
        )


_file_locks: dict[Path, asyncio.Lock] = {}
_python_process_limiter: asyncio.Semaphore | None = None
_python_process_limiter_limit: int | None = None
DEFAULT_MAX_PYTHON_PROCESSES = 2


def create_coding_tools(
    *,
    cwd: str | Path | None = None,
    shell_command_prefix: str | None = None,
) -> list[AgentTool]:
    """Create the default coding-tool set for a local project.

    The returned tools are ordered as `read`, `write`, `edit`, `python`, `sh`, and `pytest`.
    Relative paths used with those tools are resolved against `cwd`; when `cwd`
    is omitted, the process current working directory at factory-call time is
    used. The tools share per-path write/edit locks within this process so
    concurrent mutations of the same file do not interleave. When configured,
    `shell_command_prefix` is prepended to every sh tool command.
    """
    root = Path.cwd() if cwd is None else Path(cwd)
    return [
        create_read_tool(cwd=root),
        create_write_tool(cwd=root),
        create_edit_tool(cwd=root),
        create_python_tool(cwd=root),
        create_sh_tool(cwd=root, shell_command_prefix=shell_command_prefix),
        create_pytest_tool(cwd=root),
    ]


def create_read_tool_definition(*, cwd: str | Path | None = None) -> ToolDefinition:
    """Create a definition for the `read` tool.

    The tool reads a file resolved relative to `cwd` unless an absolute path is
    supplied. Text files are decoded as UTF-8 and may be sliced with optional
    1-indexed `offset` and positive integer `limit` arguments. Returned text is
    truncated to `DEFAULT_MAX_OUTPUT_LINES` lines or `DEFAULT_MAX_OUTPUT_BYTES`
    bytes, whichever comes first, and continuation hints are appended when more
    lines remain. Supported image paths (`jpg`, `png`, `gif`, and `webp`) are
    detected by MIME type and returned as base64 metadata instead of text.

    The executor raises `ToolInputError` for invalid arguments, missing files,
    directories, and offsets beyond the end of the file. Successful results
    include the resolved path and truncation metadata in `data`.
    """
    root = Path.cwd() if cwd is None else Path(cwd)

    async def execute(
        arguments: Mapping[str, JSONValue],
        signal: ToolCancellationToken | None = None,
    ) -> AgentToolResult:
        del signal
        raw_path = _str_arg(arguments, "path")
        path = _path_arg(arguments, "path", cwd=root)
        offset = _optional_int_arg(arguments, "offset")
        limit = _optional_int_arg(arguments, "limit")

        if offset is not None and offset < 0:
            raise ToolInputError("offset must be at least 0")
        if limit is not None and limit < 1:
            raise ToolInputError("limit must be at least 1")
        if not path.exists():
            raise ToolInputError(f"File not found: {path}")
        if path.is_dir():
            raise ToolInputError(f"Path is a directory: {path}")

        mime_type = _detect_supported_image_mime_type(path)
        if mime_type is not None:
            data = await _read_bytes(path)
            return AgentToolResult(
                tool_call_id="",
                name="read",
                ok=True,
                content=f"Read image file [{mime_type}]",
                data={
                    "path": str(path),
                    "mime_type": mime_type,
                    "bytes": len(data),
                    "image_base64": _base64_text(data),
                },
            )

        text = await _read_text(path)
        all_lines = text.split("\n")
        start_line = 0 if offset is None or offset == 0 else offset - 1
        if start_line >= len(all_lines):
            raise ToolInputError(
                f"Offset {offset} is beyond end of file ({len(all_lines)} lines total)"
            )

        user_limited_lines: int | None = None
        if limit is not None:
            end_line = min(start_line + limit, len(all_lines))
            selected = "\n".join(all_lines[start_line:end_line])
            user_limited_lines = end_line - start_line
        else:
            selected = "\n".join(all_lines[start_line:])

        truncation = truncate_head(selected)
        start_display = start_line + 1
        details: dict[str, JSONValue] = {"path": str(path), "truncation": truncation.to_json()}

        if truncation.first_line_exceeds_limit:
            first_line_size = format_size(len(all_lines[start_line].encode()))
            output = (
                f"[Line {start_display} is {first_line_size}, exceeds "
                f"{format_size(DEFAULT_MAX_OUTPUT_BYTES)} limit. Use read with a narrower "
                f"offset/limit range, or use a simple POSIX sh command such as sed only if needed.]"
            )
        elif truncation.truncated:
            end_display = start_display + truncation.output_lines - 1
            next_offset = end_display + 1
            output = truncation.content
            if truncation.truncated_by == "lines":
                output += (
                    f"\n\n[Showing lines {start_display}-{end_display} of {len(all_lines)}. "
                    f"Use offset={next_offset} to continue.]"
                )
            else:
                output += (
                    f"\n\n[Showing lines {start_display}-{end_display} of {len(all_lines)} "
                    f"({format_size(DEFAULT_MAX_OUTPUT_BYTES)} limit). "
                    f"Use offset={next_offset} to continue.]"
                )
        elif user_limited_lines is not None and start_line + user_limited_lines < len(all_lines):
            remaining = len(all_lines) - (start_line + user_limited_lines)
            next_offset = start_line + user_limited_lines + 1
            output = (
                f"{truncation.content}\n\n[{remaining} more lines in file. "
                f"Use offset={next_offset} to continue.]"
            )
        else:
            output = truncation.content

        return AgentToolResult(
            tool_call_id="",
            name="read",
            ok=True,
            content=output,
            data=details,
        )

    return ToolDefinition(
        name="read",
        description=(
            "Read the contents of a file. Supports text files and images (jpg, png, gif, webp). "
            "Images are returned as base64 metadata. For text files, output is truncated to "
            f"{DEFAULT_MAX_OUTPUT_LINES} lines or {DEFAULT_MAX_OUTPUT_BYTES // 1024}KB "
            "(whichever is hit first). Use offset/limit for large files. When you need the "
            "full file, continue with offset until complete."
        ),
        prompt_snippet="Read file contents",
        prompt_guidelines=(
            "Use read to examine files instead of cat, sed, awk, or shell redirection.",
            "For large files, continue with offset/limit rather than switching to shell commands.",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to read"},
                "offset": {"type": "integer", "description": "Line number to start reading from"},
                "limit": {"type": "integer", "description": "Maximum number of lines to read"},
            },
            "required": ["path"],
        },
        executor=execute,
    )


def create_read_tool(*, cwd: str | Path | None = None) -> AgentTool:
    """Create an `AgentTool` for reading UTF-8 text files and supported images."""
    return create_read_tool_definition(cwd=cwd).to_agent_tool()


def create_write_tool_definition(*, cwd: str | Path | None = None) -> ToolDefinition:
    """Create a definition for the `write` tool.

    The tool writes the supplied string `content` to `path`, resolving relative
    paths against `cwd`. Parent directories are created automatically and any
    existing file is overwritten. Writes use UTF-8 text encoding and are guarded
    by a per-path async lock so multiple writes/edits to the same resolved file
    are serialized within this process.

    The executor raises `ToolInputError` when `path` or `content` has the wrong
    type. Successful results include the resolved path and number of characters
    written in `data`.
    """
    root = Path.cwd() if cwd is None else Path(cwd)

    async def execute(
        arguments: Mapping[str, JSONValue],
        signal: ToolCancellationToken | None = None,
    ) -> AgentToolResult:
        del signal
        path = _path_arg(arguments, "path", cwd=root)
        content = _str_arg(arguments, "content")

        async with _file_lock(path):
            await _write_text(path, content)

        return AgentToolResult(
            tool_call_id="",
            name="write",
            ok=True,
            content=f"Successfully wrote to {path}.",
            data={"path": str(path), "characters": len(content)},
        )

    return ToolDefinition(
        name="write",
        description=(
            "Write content to a file. Creates the file if it doesn't exist, overwrites if it does. "
            "Automatically creates parent directories."
        ),
        prompt_snippet="Create or overwrite files",
        prompt_guidelines=("Use write only for new files or complete rewrites.",),
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to write"},
                "content": {"type": "string", "description": "Content to write to the file"},
            },
            "required": ["path", "content"],
        },
        executor=execute,
    )


def create_write_tool(*, cwd: str | Path | None = None) -> AgentTool:
    """Create an `AgentTool` for creating or overwriting UTF-8 text files."""
    return create_write_tool_definition(cwd=cwd).to_agent_tool()


def create_edit_tool_definition(*, cwd: str | Path | None = None) -> ToolDefinition:
    """Create a definition for the `edit` tool.

    The tool applies one or more exact text replacements to a single UTF-8 file
    resolved relative to `cwd`. Each edit item contains `oldText` and `newText`.
    Every `oldText` must be non-empty, must occur exactly once in the original
    file, and must not overlap another edit span. All replacements are validated
    before writing, so the file is left unchanged if any edit fails.

    File content and edit text are normalized to LF for matching, then the
    original file's dominant line ending is restored after replacement. UTF-8
    byte-order marks are preserved. The executor also accepts legacy top-level
    `oldText`/`newText` arguments and JSON-string `edits` values by normalizing
    them into the canonical edits list.

    Successful results include the resolved path, edit count, an ndiff-style
    diff, a unified patch, and the first changed line in `data`.
    """
    root = Path.cwd() if cwd is None else Path(cwd)

    async def execute(
        arguments: Mapping[str, JSONValue],
        signal: ToolCancellationToken | None = None,
    ) -> AgentToolResult:
        del signal
        prepared = _prepare_edit_arguments(arguments)
        path = _path_arg(prepared, "path", cwd=root)
        edits = _edits_arg(prepared)

        if not path.exists():
            raise ToolInputError(f"Could not edit file: {path}. File not found.")
        if path.is_dir():
            raise ToolInputError(f"Could not edit file: {path}. Path is a directory.")

        async with _file_lock(path):
            streaming_result = await _try_streaming_edit(path, edits)
            if streaming_result is None:
                raw_content = await _read_text(path)
                bom, content = _strip_bom(raw_content)
                original_ending = detect_line_ending(content)
                normalized = normalize_to_lf(content)
                base_content, new_content, edit_spans = apply_edits_to_normalized_content(
                    normalized, edits, str(path)
                )
                final_content = bom + restore_line_endings(new_content, original_ending)
                await _write_text(path, final_content)

                first_changed_line = _line_number_at_offset(base_content, edit_spans[0][0])
            else:
                first_changed_line = streaming_result["first_changed_line"]
        return AgentToolResult(
            tool_call_id="",
            name="edit",
            ok=True,
            content=f"Successfully replaced {len(edits)} block(s) in {path}.",
            data={
                "path": str(path),
                "edits": len(edits),
                "first_changed_line": first_changed_line,
            },
        )

    return ToolDefinition(
        name="edit",
        description=(
            "Edit a single file using exact text replacement. Every edits[].oldText must match "
            "a unique, non-overlapping region of the original file. If two changes affect the "
            "same block or nearby lines, merge them into one edit instead of emitting overlapping "
            "edits. Do not include large unchanged regions just to connect distant changes."
        ),
        prompt_snippet=(
            "Make precise file edits with exact text replacement, including multiple disjoint "
            "edits in one call"
        ),
        prompt_guidelines=(
            "Use edit for precise file changes instead of shell commands, here-docs, perl, or sed -i.",
            "Before using edit, read the relevant file contents so edits[].oldText can match exactly.",
            "Use edit for precise changes (edits[].oldText must match exactly)",
            "When changing multiple separate locations in one file, use one edit call with "
            "multiple entries in edits[] instead of multiple edit calls",
            "Each edits[].oldText is matched against the original file, not after earlier "
            "edits are applied. Do not emit overlapping or nested edits. Merge nearby "
            "changes into one edit.",
            "Keep edits[].oldText as small as possible while still being unique in the file. "
            "Do not pad with large unchanged regions.",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file to edit"},
                "edits": {
                    "type": "array",
                    "description": "One or more targeted replacements.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "oldText": {"type": "string"},
                            "newText": {"type": "string"},
                        },
                        "required": ["oldText", "newText"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["path", "edits"],
            "additionalProperties": False,
        },
        executor=execute,
    )


def create_edit_tool(*, cwd: str | Path | None = None) -> AgentTool:
    """Create an `AgentTool` for exact, validated text replacement in one file."""
    return create_edit_tool_definition(cwd=cwd).to_agent_tool()


def create_python_tool_definition(*, cwd: str | Path | None = None) -> ToolDefinition:
    """Create a definition for the `python` tool."""
    root = Path.cwd() if cwd is None else Path(cwd)

    async def execute(
        arguments: Mapping[str, JSONValue],
        signal: ToolCancellationToken | None = None,
    ) -> AgentToolResult:
        code = _str_arg(arguments, "code")
        raw_args = arguments.get("args", [])
        if raw_args is None:
            raw_args = []
        if not isinstance(raw_args, list) or not all(isinstance(item, str) for item in raw_args):
            raise ToolInputError("args must be a list of strings")
        timeout = _optional_float_arg(arguments, "timeout")
        if timeout is not None and timeout <= 0:
            raise ToolInputError("timeout must be greater than 0")
        if signal is not None and signal.is_cancelled():
            raise ToolInputError("Python execution cancelled")

        start = monotonic()
        limiter = _python_process_semaphore()
        async with limiter:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-c",
                code,
                *raw_args,
                cwd=root,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                start_new_session=os.name == "posix",
            )
            output_bytes, _stderr, timed_out, cancelled = await _communicate_with_cancellation(
                process,
                timeout=timeout,
                signal=signal,
            )

        output = output_bytes.decode(errors="replace")
        truncation = truncate_tail(output)
        full_output_path: str | None = None
        output_text = truncation.content or "(no output)"
        if truncation.truncated:
            full_output_path = _write_temp_output(output, prefix="tau-python-")
            start_line = truncation.total_lines - truncation.output_lines + 1
            end_line = truncation.total_lines
            if truncation.last_line_partial:
                output_text += (
                    f"\n\n[Showing last {format_size(truncation.output_bytes)} of line {end_line}. "
                    f"Full output: {full_output_path}]"
                )
            elif truncation.truncated_by == "lines":
                output_text += (
                    f"\n\n[Showing lines {start_line}-{end_line} of {truncation.total_lines}. "
                    f"Full output: {full_output_path}]"
                )
            else:
                output_text += (
                    f"\n\n[Showing lines {start_line}-{end_line} of {truncation.total_lines} "
                    f"({format_size(DEFAULT_MAX_OUTPUT_BYTES)} limit). "
                    f"Full output: {full_output_path}]"
                )

        exit_code = process.returncode
        status: str | None = None
        if timed_out:
            status = (
                f"Python execution timed out after {timeout:g} seconds"
                if timeout
                else "Python execution timed out"
            )
        elif cancelled:
            status = "Python execution cancelled"
        elif exit_code not in (0, None):
            status = f"Python exited with code {exit_code}"
        if status:
            output_text = append_status_block(output_text, status)

        ok = exit_code == 0 and not timed_out and not cancelled
        return AgentToolResult(
            tool_call_id="",
            name="python",
            ok=ok,
            content=output_text,
            error=None if ok else status,
            data={
                "exit_code": exit_code,
                "timed_out": timed_out,
                "cancelled": cancelled,
                "duration_seconds": round(monotonic() - start, 3),
                "truncation": truncation.to_json(),
                "full_output_path": full_output_path,
                "args": raw_args,
            },
        )

    return ToolDefinition(
        name="python",
        description=(
            "Execute Python code using the current Python interpreter without going through sh. "
            "Use this instead of shell heredocs or complex shell quoting for small scripts, JSON/text processing, "
            "and portable file transformations. Code is passed directly to python -c, stdin is closed, and "
            f"output is truncated to last {DEFAULT_MAX_OUTPUT_LINES} lines or "
            f"{DEFAULT_MAX_OUTPUT_BYTES // 1024}KB (whichever is hit first)."
        ),
        prompt_snippet="Execute Python code directly without shell heredocs",
        prompt_guidelines=(
            "Use python for inline scripts instead of sh heredocs, python <<EOF, or complex shell quoting.",
            "Use read/edit/write for simple file inspection and edits; use python when structured parsing or transformation is clearer.",
            "Keep code self-contained and portable; do not rely on shell expansion or stdin.",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute with python -c"},
                "args": {
                    "type": "array",
                    "description": "Optional argv strings available as sys.argv[1:]",
                    "items": {"type": "string"},
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds (optional, no default timeout)",
                },
            },
            "required": ["code"],
        },
        executor=execute,
    )


def create_python_tool(*, cwd: str | Path | None = None) -> AgentTool:
    """Create an `AgentTool` for executing Python code without invoking a shell."""
    return create_python_tool_definition(cwd=cwd).to_agent_tool()


def create_pytest_tool_definition(*, cwd: str | Path | None = None) -> ToolDefinition:
    """Create a definition for running pytest through the active interpreter, serially."""
    root = Path.cwd() if cwd is None else Path(cwd)

    async def execute(
        arguments: Mapping[str, JSONValue],
        signal: ToolCancellationToken | None = None,
    ) -> AgentToolResult:
        raw_args = arguments.get("args", [])
        if raw_args is None:
            raw_args = []
        if not isinstance(raw_args, list) or not all(isinstance(item, str) for item in raw_args):
            raise ToolInputError("args must be a list of strings")
        timeout = _optional_float_arg(arguments, "timeout")
        if timeout is not None and timeout <= 0:
            raise ToolInputError("timeout must be greater than 0")
        if signal is not None and signal.is_cancelled():
            raise ToolInputError("pytest execution cancelled")

        pytest_args = _linear_pytest_args(tuple(raw_args))
        start = monotonic()
        limiter = _python_process_semaphore()
        async with limiter:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "pytest",
                *pytest_args,
                cwd=root,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                start_new_session=os.name == "posix",
                env=_linear_pytest_env(),
            )
            output_bytes, _stderr, timed_out, cancelled = await _communicate_with_cancellation(
                process,
                timeout=timeout,
                signal=signal,
            )

        output = output_bytes.decode(errors="replace")
        truncation = truncate_tail(output)
        full_output_path: str | None = None
        output_text = truncation.content or "(no output)"
        if truncation.truncated:
            full_output_path = _write_temp_output(output, prefix="tau-pytest-")
            start_line = truncation.total_lines - truncation.output_lines + 1
            end_line = truncation.total_lines
            output_text += (
                f"\n\n[Showing lines {start_line}-{end_line} of {truncation.total_lines}. "
                f"Full output: {full_output_path}]"
            )

        exit_code = process.returncode
        status: str | None = None
        if timed_out:
            status = f"pytest timed out after {timeout:g} seconds" if timeout else "pytest timed out"
        elif cancelled:
            status = "pytest execution cancelled"
        elif exit_code not in (0, None):
            status = f"pytest exited with code {exit_code}"
        if status:
            output_text = append_status_block(output_text, status)

        ok = exit_code == 0 and not timed_out and not cancelled
        return AgentToolResult(
            tool_call_id="",
            name="pytest",
            ok=ok,
            content=output_text,
            error=None if ok else status,
            data={
                "exit_code": exit_code,
                "timed_out": timed_out,
                "cancelled": cancelled,
                "duration_seconds": round(monotonic() - start, 3),
                "truncation": truncation.to_json(),
                "full_output_path": full_output_path,
                "args": list(pytest_args),
                "linear": True,
                "max_python_processes": _max_python_processes(),
            },
        )

    return ToolDefinition(
        name="pytest",
        description=(
            "Run pytest with the current Python interpreter in a serialized, agent-safe way. "
            "This avoids shell quoting, disables common pytest parallelism, and shares Tau's Python process limiter."
        ),
        prompt_snippet="Run pytest linearly with python -m pytest",
        prompt_guidelines=(
            "Use pytest instead of sh for Python test runs.",
            "Pass test paths and pytest flags as args; do not wrap them in a shell command string.",
            "Runs are serialized by Tau's Python process limiter and force pytest-xdist to -n 0 when available.",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "args": {
                    "type": "array",
                    "description": "pytest arguments, for example ['-q', 'tests/test_file.py']",
                    "items": {"type": "string"},
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds (optional, no default timeout)",
                },
            },
        },
        executor=execute,
    )


def create_pytest_tool(*, cwd: str | Path | None = None) -> AgentTool:
    """Create an `AgentTool` for serialized pytest execution."""
    return create_pytest_tool_definition(cwd=cwd).to_agent_tool()


def create_sh_tool_definition(
    *,
    cwd: str | Path | None = None,
    shell_command_prefix: str | None = None,
) -> ToolDefinition:
    """Create a definition for the `sh` tool.

    The tool runs a shell command with `cwd` as the subprocess working
    directory and combines stdout and stderr into one UTF-8 decoded output
    stream. The optional `timeout` argument must be positive when supplied. On
    timeout, POSIX commands are started in a new session and the entire process
    group is killed so shell children from pipelines or compound commands do
    not continue running; non-POSIX platforms fall back to killing the direct
    subprocess.

    Output is tail-truncated to `DEFAULT_MAX_OUTPUT_LINES` lines or
    `DEFAULT_MAX_OUTPUT_BYTES` bytes. When truncation occurs, the full output is
    written to a temporary log file and that path is reported in `data`.
    Successful and failed command results both include exit code, timeout state,
    duration, truncation metadata, and full-output path metadata.
    """
    root = Path.cwd() if cwd is None else Path(cwd)
    prefix = shell_command_prefix.strip() if shell_command_prefix else None

    async def execute(
        arguments: Mapping[str, JSONValue],
        signal: ToolCancellationToken | None = None,
    ) -> AgentToolResult:
        command = _str_arg(arguments, "command")
        shell_command = _prefixed_shell_command(command, prefix)
        timeout = _optional_float_arg(arguments, "timeout")
        if timeout is not None and timeout <= 0:
            raise ToolInputError("timeout must be greater than 0")
        if signal is not None and signal.is_cancelled():
            raise ToolInputError("Command cancelled")

        start = monotonic()
        if os.name == "posix":
            process = await asyncio.create_subprocess_shell(
                shell_command,
                cwd=root,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                start_new_session=True,
            )
        else:
            process = await asyncio.create_subprocess_shell(
                shell_command,
                cwd=root,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        output_bytes, _stderr, timed_out, cancelled = await _communicate_with_cancellation(
            process,
            timeout=timeout,
            signal=signal,
        )

        output = output_bytes.decode(errors="replace")
        truncation = truncate_tail(output)
        full_output_path: str | None = None
        output_text = truncation.content or "(no output)"
        if truncation.truncated:
            full_output_path = _write_temp_output(output)
            start_line = truncation.total_lines - truncation.output_lines + 1
            end_line = truncation.total_lines
            if truncation.last_line_partial:
                output_text += (
                    f"\n\n[Showing last {format_size(truncation.output_bytes)} of line {end_line}. "
                    f"Full output: {full_output_path}]"
                )
            elif truncation.truncated_by == "lines":
                output_text += (
                    f"\n\n[Showing lines {start_line}-{end_line} of {truncation.total_lines}. "
                    f"Full output: {full_output_path}]"
                )
            else:
                output_text += (
                    f"\n\n[Showing lines {start_line}-{end_line} of {truncation.total_lines} "
                    f"({format_size(DEFAULT_MAX_OUTPUT_BYTES)} limit). "
                    f"Full output: {full_output_path}]"
                )

        exit_code = process.returncode
        status: str | None = None
        if timed_out:
            status = (
                f"Command timed out after {timeout:g} seconds" if timeout else "Command timed out"
            )
        elif cancelled:
            status = "Command cancelled"
        elif exit_code not in (0, None):
            status = f"Command exited with code {exit_code}"
        if status:
            output_text = append_status_block(output_text, status)

        ok = exit_code == 0 and not timed_out and not cancelled
        return AgentToolResult(
            tool_call_id="",
            name="sh",
            ok=ok,
            content=output_text,
            error=None if ok else status,
            data={
                "command": command,
                "exit_code": exit_code,
                "timed_out": timed_out,
                "cancelled": cancelled,
                "duration_seconds": round(monotonic() - start, 3),
                "truncation": truncation.to_json(),
                "full_output_path": full_output_path,
                "shell_command_prefix_applied": prefix is not None,
            },
        )

    return ToolDefinition(
        name="sh",
        description=(
            "Execute one non-interactive shell command in the current working directory. "
            "Assume only basic POSIX sh is available (for example a-Shell on iOS); "
            "do not assume non-POSIX syntax, job control, a persistent session, or a full desktop toolchain. "
            "Returns stdout and stderr. "
            f"Output is truncated to last {DEFAULT_MAX_OUTPUT_LINES} lines or "
            f"{DEFAULT_MAX_OUTPUT_BYTES // 1024}KB (whichever is hit first). If truncated, "
            "full output is saved to a temp file. Optionally provide a timeout in seconds."
        ),
        prompt_snippet="Execute a single non-interactive shell command (basic sh may be all that is available)",
        prompt_guidelines=(
            "Use sh only for simple non-interactive commands; it may be basic POSIX sh on constrained systems such as a-Shell/iOS.",
            "Do not use non-POSIX shell features like arrays, [[ ... ]], process substitution, pipefail, brace expansion, or a persistent shell session.",
            "Prefer read/edit/write for file inspection and modification instead of shelling out with cat, sed, here-docs, or redirection.",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Single non-interactive shell command to execute; prefer POSIX sh syntax"},
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds (optional, no default timeout)",
                },
            },
            "required": ["command"],
        },
        executor=execute,
    )


def create_sh_tool(
    *,
    cwd: str | Path | None = None,
    shell_command_prefix: str | None = None,
) -> AgentTool:
    """Create an `AgentTool` for executing shell commands with captured output."""
    return create_sh_tool_definition(
        cwd=cwd,
        shell_command_prefix=shell_command_prefix,
    ).to_agent_tool()


def create_bash_tool_definition(
    *,
    cwd: str | Path | None = None,
    shell_command_prefix: str | None = None,
) -> ToolDefinition:
    """Deprecated compatibility alias for :func:`create_sh_tool_definition`."""
    return create_sh_tool_definition(cwd=cwd, shell_command_prefix=shell_command_prefix)


def create_bash_tool(
    *,
    cwd: str | Path | None = None,
    shell_command_prefix: str | None = None,
) -> AgentTool:
    """Deprecated compatibility alias for :func:`create_sh_tool`."""
    return create_sh_tool(cwd=cwd, shell_command_prefix=shell_command_prefix)


def _prefixed_shell_command(command: str, prefix: str | None) -> str:
    """Return a shell command with an opt-in setup prefix applied."""
    if prefix is None:
        return command
    return f"{prefix}\n{command}"


def format_size(bytes_count: int) -> str:
    if bytes_count < 1024:
        return f"{bytes_count}B"
    if bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f}KB"
    return f"{bytes_count / (1024 * 1024):.1f}MB"


def append_status_block(text: str, status: str) -> str:
    """Append command status text after a blank line when output already exists."""
    return f"{text}\n\n{status}" if text else status


async def _read_text(path: Path) -> str:
    return await asyncio.to_thread(path.read_text, encoding="utf-8")


async def _read_bytes(path: Path) -> bytes:
    return await asyncio.to_thread(path.read_bytes)


async def _write_text(path: Path, content: str) -> None:
    def write() -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    await asyncio.to_thread(write)


def _max_python_processes() -> int:
    raw = os.environ.get("TAU_MAX_PYTHON_PROCESSES")
    if raw is None or not raw.strip():
        return DEFAULT_MAX_PYTHON_PROCESSES
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_MAX_PYTHON_PROCESSES
    return max(1, value)


def _python_process_semaphore() -> asyncio.Semaphore:
    global _python_process_limiter, _python_process_limiter_limit
    limit = _max_python_processes()
    if _python_process_limiter is None or _python_process_limiter_limit != limit:
        _python_process_limiter = asyncio.Semaphore(limit)
        _python_process_limiter_limit = limit
    return _python_process_limiter


def _linear_pytest_args(args: tuple[str, ...]) -> tuple[str, ...]:
    if _pytest_args_disable_xdist(args) or importlib.util.find_spec("xdist") is None:
        return args
    return ("-n", "0", *args)


def _pytest_args_disable_xdist(args: tuple[str, ...]) -> bool:
    for index, arg in enumerate(args):
        if arg in {"-n", "--numprocesses"}:
            return True
        if arg.startswith("-n") and len(arg) > 2:
            return True
        if arg.startswith("--numprocesses="):
            return True
        if arg == "-p" and index + 1 < len(args) and args[index + 1] == "no:xdist":
            return True
    return False


def _linear_pytest_env() -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("PYTHONHASHSEED", "0")
    env.setdefault("OMP_NUM_THREADS", "1")
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    env.setdefault("MKL_NUM_THREADS", "1")
    env.setdefault("NUMEXPR_NUM_THREADS", "1")
    return env


async def _communicate_with_cancellation(
    process: asyncio.subprocess.Process,
    *,
    timeout: float | None,
    signal: ToolCancellationToken | None,
) -> tuple[bytes, bytes | None, bool, bool]:
    communicate = asyncio.create_task(process.communicate())
    cancel_watch: asyncio.Task[None] | None = None
    try:
        wait_for: set[asyncio.Task[Any]] = {communicate}
        if signal is not None:
            cancel_watch = asyncio.create_task(_wait_for_cancel(signal))
            wait_for.add(cancel_watch)

        done, _pending = await asyncio.wait(
            wait_for,
            timeout=timeout,
            return_when=asyncio.FIRST_COMPLETED,
        )
        if communicate in done:
            output_bytes, stderr = communicate.result()
            return output_bytes, stderr, False, False

        cancelled = cancel_watch is not None and cancel_watch in done
        _kill_process_tree(process)
        try:
            output_bytes, stderr = await communicate
        except asyncio.CancelledError:
            output_bytes = b""
            stderr_result: bytes | None = None
        else:
            stderr_result = stderr
        return output_bytes, stderr_result, not cancelled, cancelled
    except asyncio.CancelledError:
        _kill_process_tree(process)
        if not communicate.done():
            communicate.cancel()
        raise
    finally:
        if cancel_watch is not None:
            cancel_watch.cancel()


async def _wait_for_cancel(signal: ToolCancellationToken) -> None:
    while not signal.is_cancelled():
        await asyncio.sleep(0.05)


def truncate_head(
    content: str,
    *,
    max_lines: int = DEFAULT_MAX_OUTPUT_LINES,
    max_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> TruncationResult:
    lines = _split_lines_for_counting(content)
    total_lines = len(lines)
    total_bytes = len(content.encode())
    if total_lines <= max_lines and total_bytes <= max_bytes:
        return _truncation_result(
            content, False, None, total_lines, total_bytes, total_lines, total_bytes
        )

    first_line_bytes = len(lines[0].encode()) if lines else 0
    if first_line_bytes > max_bytes:
        return _truncation_result(
            "", True, "bytes", total_lines, total_bytes, 0, 0, first_line=True
        )

    output_lines: list[str] = []
    output_bytes = 0
    truncated_by = "lines"
    for index, line in enumerate(lines[:max_lines]):
        line_bytes = len(line.encode()) + (1 if index > 0 else 0)
        if output_bytes + line_bytes > max_bytes:
            truncated_by = "bytes"
            break
        output_lines.append(line)
        output_bytes += line_bytes

    output = "\n".join(output_lines)
    return _truncation_result(
        output,
        True,
        truncated_by,
        total_lines,
        total_bytes,
        len(output_lines),
        len(output.encode()),
    )


def truncate_tail(
    content: str,
    *,
    max_lines: int = DEFAULT_MAX_OUTPUT_LINES,
    max_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> TruncationResult:
    lines = _split_lines_for_counting(content)
    total_lines = len(lines)
    total_bytes = len(content.encode())
    if total_lines <= max_lines and total_bytes <= max_bytes:
        return _truncation_result(
            content, False, None, total_lines, total_bytes, total_lines, total_bytes
        )

    output_lines: list[str] = []
    output_bytes = 0
    truncated_by = "lines"
    last_line_partial = False
    for line in reversed(lines):
        line_bytes = len(line.encode()) + (1 if output_lines else 0)
        if len(output_lines) >= max_lines:
            truncated_by = "lines"
            break
        if output_bytes + line_bytes > max_bytes:
            truncated_by = "bytes"
            if not output_lines:
                clipped = _truncate_string_to_bytes_from_end(line, max_bytes)
                output_lines.insert(0, clipped)
                output_bytes = len(clipped.encode())
                last_line_partial = True
            break
        output_lines.insert(0, line)
        output_bytes += line_bytes

    output = "\n".join(output_lines)
    return _truncation_result(
        output,
        True,
        truncated_by,
        total_lines,
        total_bytes,
        len(output_lines),
        len(output.encode()),
        last_line_partial=last_line_partial,
    )


def detect_line_ending(content: str) -> str:
    crlf_index = content.find("\r\n")
    lf_index = content.find("\n")
    if lf_index == -1 or crlf_index == -1:
        return "\n"
    return "\r\n" if crlf_index < lf_index else "\n"


def normalize_to_lf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def restore_line_endings(text: str, ending: str) -> str:
    return text.replace("\n", "\r\n") if ending == "\r\n" else text


async def _try_streaming_edit(
    path: Path,
    edits: list[dict[str, str]],
) -> dict[str, JSONValue] | None:
    """Apply a simple large-file edit with bounded memory.

    This is intentionally conservative: it handles the common large-file case of
    one exact replacement whose texts are UTF-8 encodable and do not require the
    LF-normalization compatibility path. Validation still happens before writing:
    a first streaming pass counts matches and finds the first changed line, then a
    second pass writes to a temporary file and atomically replaces the original.
    """
    if len(edits) != 1:
        return None
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if size < STREAMING_EDIT_MIN_BYTES:
        return None

    old_text = edits[0]["oldText"]
    new_text = edits[0]["newText"]
    if not old_text:
        raise ToolInputError(_empty_old_text_error(str(path), 0, 1))
    if "\r" in old_text or "\r" in new_text:
        return None
    old_bytes = old_text.encode("utf-8")
    new_bytes = new_text.encode("utf-8")
    if not old_bytes:
        raise ToolInputError(_empty_old_text_error(str(path), 0, 1))

    count, first_offset = await asyncio.to_thread(_count_streaming_matches, path, old_bytes)
    if count == 0:
        raise ToolInputError(_not_found_error(str(path), 0, 1))
    if count > 1:
        raise ToolInputError(_duplicate_error(str(path), 0, 1, count))
    if old_bytes == new_bytes:
        raise ToolInputError(_no_change_error(str(path), 1))

    await asyncio.to_thread(_stream_replace_file, path, old_bytes, new_bytes)
    first_changed_line = await asyncio.to_thread(_line_number_for_byte_offset, path, first_offset)
    return {"first_changed_line": first_changed_line}


def _count_streaming_matches(path: Path, needle: bytes) -> tuple[int, int]:
    overlap = max(len(needle) - 1, 0)
    tail = b""
    count = 0
    first_offset = -1
    processed = 0
    with path.open("rb") as handle:
        while chunk := handle.read(STREAMING_EDIT_CHUNK_BYTES):
            data = tail + chunk
            search_start = 0
            safe_end = len(data) if not overlap else max(0, len(data) - overlap)
            while True:
                index = data.find(needle, search_start)
                if index < 0 or index >= safe_end:
                    break
                absolute = processed - len(tail) + index
                if first_offset < 0:
                    first_offset = absolute
                count += 1
                search_start = index + 1
            processed += len(chunk)
            tail = data[-overlap:] if overlap else b""
    if tail:
        search_start = 0
        while True:
            index = tail.find(needle, search_start)
            if index < 0:
                break
            absolute = processed - len(tail) + index
            if first_offset < 0:
                first_offset = absolute
            count += 1
            search_start = index + 1
    return count, first_offset


def _stream_replace_file(path: Path, old_bytes: bytes, new_bytes: bytes) -> None:
    overlap = max(len(old_bytes) - 1, 0)
    replaced = False
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        with path.open("rb") as source, os.fdopen(fd, "wb") as target:
            tail = b""
            while chunk := source.read(STREAMING_EDIT_CHUNK_BYTES):
                data = tail + chunk
                if not replaced:
                    index = data.find(old_bytes)
                    if index >= 0:
                        target.write(data[:index])
                        target.write(new_bytes)
                        target.write(data[index + len(old_bytes) :])
                        replaced = True
                        tail = b""
                        continue
                safe_end = len(data) if not overlap else max(0, len(data) - overlap)
                target.write(data[:safe_end])
                tail = data[safe_end:]
            if tail:
                if not replaced:
                    index = tail.find(old_bytes)
                    if index >= 0:
                        target.write(tail[:index])
                        target.write(new_bytes)
                        target.write(tail[index + len(old_bytes) :])
                        replaced = True
                    else:
                        target.write(tail)
                else:
                    target.write(tail)
        os.replace(tmp_path, path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def _line_number_for_byte_offset(path: Path, byte_offset: int) -> int:
    remaining = max(0, byte_offset)
    line = 1
    with path.open("rb") as handle:
        while remaining > 0:
            chunk = handle.read(min(STREAMING_EDIT_CHUNK_BYTES, remaining))
            if not chunk:
                break
            line += chunk.count(b"\n")
            remaining -= len(chunk)
    return line



def apply_edits_to_normalized_content(
    normalized_content: str,
    edits: list[dict[str, str]],
    path: str,
) -> tuple[str, str, list[tuple[int, int, str]]]:
    normalized_edits = [
        {"oldText": normalize_to_lf(edit["oldText"]), "newText": normalize_to_lf(edit["newText"])}
        for edit in edits
    ]
    for index, edit in enumerate(normalized_edits):
        if not edit["oldText"]:
            raise ToolInputError(_empty_old_text_error(path, index, len(normalized_edits)))

    matches: list[tuple[int, int, str]] = []
    for index, edit in enumerate(normalized_edits):
        old_text = edit["oldText"]
        start = normalized_content.find(old_text)
        if start < 0:
            raise ToolInputError(_not_found_error(path, index, len(normalized_edits)))
        if normalized_content.find(old_text, start + 1) >= 0:
            raise ToolInputError(_duplicate_error(path, index, len(normalized_edits), 2))
        matches.append((start, start + len(old_text), edit["newText"]))

    _validate_non_overlapping(matches)
    sorted_matches = sorted(matches)
    new_content = _apply_replacements(normalized_content, sorted_matches)
    if new_content == normalized_content:
        raise ToolInputError(_no_change_error(path, len(normalized_edits)))
    return normalized_content, new_content, sorted_matches


def _apply_replacements(content: str, matches: list[tuple[int, int, str]]) -> str:
    pieces: list[str] = []
    cursor = 0
    for start, end, new_text in matches:
        pieces.append(content[cursor:start])
        pieces.append(new_text)
        cursor = end
    pieces.append(content[cursor:])
    return "".join(pieces)


def _line_number_at_offset(content: str, offset: int) -> int:
    return content.count("\n", 0, max(0, offset)) + 1

def _truncation_result(
    content: str,
    truncated: bool,
    truncated_by: str | None,
    total_lines: int,
    total_bytes: int,
    output_lines: int,
    output_bytes: int,
    *,
    last_line_partial: bool = False,
    first_line: bool = False,
) -> TruncationResult:
    return TruncationResult(
        content=content,
        truncated=truncated,
        truncated_by=truncated_by,
        total_lines=total_lines,
        total_bytes=total_bytes,
        output_lines=output_lines,
        output_bytes=output_bytes,
        last_line_partial=last_line_partial,
        first_line_exceeds_limit=first_line,
        max_lines=DEFAULT_MAX_OUTPUT_LINES,
        max_bytes=DEFAULT_MAX_OUTPUT_BYTES,
    )


def _split_lines_for_counting(content: str) -> list[str]:
    if not content:
        return []
    lines = content.split("\n")
    if content.endswith("\n"):
        lines.pop()
    return lines


def _truncate_string_to_bytes_from_end(text: str, max_bytes: int) -> str:
    encoded = text.encode()
    if len(encoded) <= max_bytes:
        return text
    clipped = encoded[-max_bytes:]
    return clipped.decode(errors="ignore")


def _str_arg(arguments: Mapping[str, JSONValue], name: str) -> str:
    value = arguments.get(name)
    if not isinstance(value, str):
        raise ToolInputError(f"{name} must be a string")
    return value


def _path_arg(arguments: Mapping[str, JSONValue], name: str, *, cwd: Path) -> Path:
    value = _str_arg(arguments, name)
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = cwd / path
    return path


def _optional_int_arg(arguments: Mapping[str, JSONValue], name: str) -> int | None:
    value = arguments.get(name)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ToolInputError(f"{name} must be an integer")
    return value


def _optional_float_arg(arguments: Mapping[str, JSONValue], name: str) -> float | None:
    value = arguments.get(name)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ToolInputError(f"{name} must be a number")
    return float(value)


def _prepare_edit_arguments(arguments: Mapping[str, JSONValue]) -> Mapping[str, JSONValue]:
    prepared = dict(arguments)
    edits_value = prepared.get("edits")
    if isinstance(edits_value, str):
        try:
            parsed = json.loads(edits_value)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            prepared["edits"] = parsed

    old_text = prepared.get("oldText")
    new_text = prepared.get("newText")
    if isinstance(old_text, str) and isinstance(new_text, str):
        edits = prepared.get("edits")
        edit_list = edits if isinstance(edits, list) else []
        prepared["edits"] = [*edit_list, {"oldText": old_text, "newText": new_text}]
        prepared.pop("oldText", None)
        prepared.pop("newText", None)
    return prepared


def _edits_arg(arguments: Mapping[str, JSONValue]) -> list[dict[str, str]]:
    value = arguments.get("edits")
    if not isinstance(value, list) or not value:
        raise ToolInputError(
            "Edit tool input is invalid. edits must contain at least one replacement."
        )

    edits: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ToolInputError(f"edits[{index}] must be an object")
        old_text = item.get("oldText")
        new_text = item.get("newText")
        if not isinstance(old_text, str) or not isinstance(new_text, str):
            raise ToolInputError(
                f"edits[{index}].oldText and edits[{index}].newText must be strings"
            )
        edits.append({"oldText": old_text, "newText": new_text})
    return edits


def _validate_non_overlapping(spans: list[tuple[int, int, str]]) -> None:
    previous_end = -1
    for start, end, _new_text in sorted(spans):
        if start < previous_end:
            raise ToolInputError("Edits must not overlap")
        previous_end = end


def _strip_bom(content: str) -> tuple[str, str]:
    return (UTF8_BOM, content[1:]) if content.startswith(UTF8_BOM) else ("", content)


def _not_found_error(path: str, edit_index: int, total_edits: int) -> str:
    if total_edits == 1:
        return (
            f"Could not find the exact text in {path}. The old text must match exactly "
            "including all whitespace and newlines."
        )
    return (
        f"Could not find edits[{edit_index}] in {path}. The oldText must match exactly "
        "including all whitespace and newlines."
    )


def _duplicate_error(path: str, edit_index: int, total_edits: int, occurrences: int) -> str:
    if total_edits == 1:
        return (
            f"Found {occurrences} occurrences of the text in {path}. The text must be unique. "
            "Please provide more context to make it unique."
        )
    return (
        f"Found {occurrences} occurrences of edits[{edit_index}] in {path}. "
        "Each oldText must be unique. Please provide more context to make it unique."
    )


def _empty_old_text_error(path: str, edit_index: int, total_edits: int) -> str:
    if total_edits == 1:
        return f"oldText must not be empty in {path}."
    return f"edits[{edit_index}].oldText must not be empty in {path}."


def _no_change_error(path: str, total_edits: int) -> str:
    if total_edits == 1:
        return (
            f"No changes made to {path}. The replacement produced identical content. "
            "This might indicate an issue with special characters or the text not existing "
            "as expected."
        )
    return f"No changes made to {path}. The replacements produced identical content."


def _detect_supported_image_mime_type(path: Path) -> str | None:
    mime_type, _encoding = mimetypes.guess_type(path)
    return mime_type if mime_type in SUPPORTED_IMAGE_MIME_TYPES else None


def _base64_text(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode("ascii")


def _kill_process_tree(process: asyncio.subprocess.Process) -> None:
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
    else:
        try:
            process.kill()
        except ProcessLookupError:
            return


def _write_temp_output(output: str, *, prefix: str = "tau-sh-") -> str:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix=prefix,
        suffix=".log",
        delete=False,
    ) as handle:
        handle.write(output)
        return handle.name


class _FileLockContext:
    def __init__(self, path: Path) -> None:
        self._path = path.resolve()
        self._lock: asyncio.Lock | None = None

    async def __aenter__(self) -> None:
        lock = _file_locks.setdefault(self._path, asyncio.Lock())
        self._lock = lock
        await lock.acquire()

    async def __aexit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        if self._lock is not None:
            self._lock.release()


def _file_lock(path: Path) -> _FileLockContext:
    return _FileLockContext(path)
