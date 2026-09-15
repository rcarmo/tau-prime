from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest
from aiohttp import ClientResponse, web
from aiohttp.test_utils import TestClient, TestServer

from tau_agent import AgentTool, SimpleCancellationToken, ToolCall
from tau_agent.types import JSONObject, JSONValue
from tau_web.app import SERVICES_KEY, create_app
from tau_web.approvals import ToolApprovalManager, ToolApprovalRequest
from tau_web.config import WebConfig
from tau_web.services import TauWebServices
from tau_web.sqlite.connection import SqliteDatabase
from tau_web.sqlite.repositories import AuditRepository
from tau_web.sqlite.sessions import SessionRepository
from tau_web.sse import EventBroker


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@dataclass(frozen=True, slots=True)
class _SSEFrame:
    event_id: str | None
    event: str | None
    data: JSONObject | None


async def _unused_executor(
    arguments: dict[str, JSONValue],
    signal: object | None = None,
) -> JSONValue:
    del arguments, signal
    raise AssertionError("Tool executor should not run during approval tests")


def _tool() -> AgentTool:
    return AgentTool(
        name="write",
        description="Write a file.",
        input_schema={"type": "object"},
        executor=_unused_executor,  # type: ignore[arg-type]
    )


async def _wait_for_pending(
    manager: ToolApprovalManager,
    *,
    session_id: str,
    timeout: float = 1.0,
) -> ToolApprovalRequest:
    async with asyncio.timeout(timeout):
        while True:
            pending = manager.list_pending(session_id=session_id)
            if pending:
                return pending[0]
            await asyncio.sleep(0)


async def _start_client(app: web.Application) -> TestClient:
    client = TestClient(TestServer(app))
    await client.start_server()
    return client


def _services(client: TestClient) -> TauWebServices:
    return cast(TauWebServices, client.app[SERVICES_KEY])


async def _create_database_session(
    database: SqliteDatabase, workspace_root: Path, session_id: str
) -> None:
    await SessionRepository(database).create(
        workspace_root=workspace_root,
        provider_name="test",
        model="model",
        agent_name=session_id,
        session_id=session_id,
    )


async def _create_session(client: TestClient, session_id: str) -> str:
    record = await _services(client).sessions.create(
        workspace_root=_services(client).config.cwd,
        provider_name="test",
        model="model",
        agent_name=session_id,
        session_id=session_id,
    )
    return record.session_id


async def _read_sse_frame(response: ClientResponse, *, timeout: float = 1.0) -> _SSEFrame:
    lines: list[str] = []
    async with asyncio.timeout(timeout):
        while True:
            raw_line = await response.content.readline()
            if raw_line == b"":
                raise AssertionError("SSE stream closed before the next frame was received")
            line = raw_line.decode("utf-8").rstrip("\r\n")
            if not line:
                break
            lines.append(line)

    event_id: str | None = None
    event: str | None = None
    data_lines: list[str] = []
    for line in lines:
        field, _, raw_value = line.partition(":")
        value = raw_value[1:] if raw_value.startswith(" ") else raw_value
        if field == "id":
            event_id = value
        elif field == "event":
            event = value
        elif field == "data":
            data_lines.append(value)

    data: JSONObject | None = None
    if data_lines:
        parsed = json.loads("\n".join(data_lines))
        assert isinstance(parsed, dict)
        data = cast(JSONObject, parsed)
    return _SSEFrame(event_id=event_id, event=event, data=data)


@pytest.mark.anyio
async def test_tool_approval_manager_tracks_pending_requests_and_redacts_audit_trail(
    tmp_path: Path,
) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        await _create_database_session(database, tmp_path, "alpha")
        audit = AuditRepository(database)
        broker = EventBroker(replay_capacity=8, subscriber_capacity=8)
        manager = ToolApprovalManager(audit, broker)
        subscription, _ = broker.subscribe(session_id="alpha")
        tool_call = ToolCall(
            id="call-1",
            name="write",
            arguments={
                "path": "notes.txt",
                "api_key": "sk-secret-token",
                "prompt": "Authorization: Bearer top-secret",
            },
        )

        request_task = asyncio.create_task(manager.request("alpha", tool_call, _tool()))
        pending = await _wait_for_pending(manager, session_id="alpha")

        assert manager.list_pending(session_id="alpha") == (pending,)
        assert pending.tool_call_id == "call-1"
        assert pending.arguments == {
            "path": "notes.txt",
            "api_key": "[REDACTED]",
            "prompt": "Authorization: Bearer [REDACTED]",
        }

        requested = await subscription.next(timeout=1.0)
        assert requested is not None
        assert requested.envelope.type == "tau.approval.requested"
        assert requested.envelope.payload["approval_id"] == pending.approval_id
        assert requested.envelope.payload["arguments"] == pending.arguments

        resolved = await manager.resolve(
            pending.approval_id,
            "allow",
            actor_id="browser-1",
            request_id="request-1",
        )
        assert resolved == pending
        assert await request_task is True
        assert manager.list_pending(session_id="alpha") == ()

        resolved_event = await subscription.next(timeout=1.0)
        assert resolved_event is not None
        assert resolved_event.envelope.type == "tau.approval.resolved"
        assert resolved_event.envelope.payload["approval_id"] == pending.approval_id
        assert resolved_event.envelope.payload["decision"] == "allow"

        records = await audit.list(session_id="alpha", limit=10)
        requested_record = next(
            record for record in records if record.event_type == "tool.approval.requested"
        )
        resolved_record = next(
            record for record in records if record.event_type == "tool.approval.resolved"
        )
        assert requested_record.details["arguments"] == pending.arguments
        assert resolved_record.actor_type == "browser"
        assert resolved_record.actor_id == "browser-1"
        assert resolved_record.request_id == "request-1"
        assert resolved_record.details["decision"] == "allow"


@pytest.mark.anyio
async def test_tool_approval_manager_cancel_and_shutdown_deny_requests(tmp_path: Path) -> None:
    async with SqliteDatabase(tmp_path / "tau.sqlite3") as database:
        await _create_database_session(database, tmp_path, "alpha")
        audit = AuditRepository(database)
        manager = ToolApprovalManager(audit, EventBroker())
        tool_call = ToolCall(id="call-1", name="write", arguments={"path": "notes.txt"})

        timeout_manager = ToolApprovalManager(audit, EventBroker(), timeout_seconds=0.01)
        assert await timeout_manager.request("alpha", tool_call, _tool()) is False
        timeout_record = next(
            record
            for record in await audit.list(session_id="alpha", limit=10)
            if record.actor_id == "runtime-timeout"
        )
        assert timeout_record.details["decision"] == "deny"

        signal = SimpleCancellationToken()
        signal_task = asyncio.create_task(
            manager.request("alpha", tool_call, _tool(), signal=signal)
        )
        await _wait_for_pending(manager, session_id="alpha")
        signal.cancel()
        assert await signal_task is False

        first_task = asyncio.create_task(manager.request("alpha", tool_call, _tool()))
        first_pending = await _wait_for_pending(manager, session_id="alpha")

        cancelled = await manager.cancel(first_pending.approval_id)
        assert cancelled == first_pending
        assert await first_task is False
        assert manager.list_pending(session_id="alpha") == ()

        second_task = asyncio.create_task(manager.request("alpha", tool_call, _tool()))
        second_pending = await _wait_for_pending(manager, session_id="alpha")

        await manager.shutdown()
        assert await second_task is False
        assert manager.list_pending(session_id="alpha") == ()
        assert second_pending.approval_id != first_pending.approval_id
        assert await manager.request("alpha", tool_call, _tool()) is False


@pytest.mark.anyio
async def test_approval_routes_stream_sse_and_expose_redacted_audit_records(
    web_config: WebConfig,
) -> None:
    client = await _start_client(create_app(web_config))
    try:
        session_id = await _create_session(client, "alpha")
        services = _services(client)
        tool_call = ToolCall(
            id="call-1",
            name="write",
            arguments={
                "path": "notes.txt",
                "token": "sk-secret-token",
            },
        )

        async with client.get("/api/events", params={"session_id": session_id}) as response:
            snapshot = await _read_sse_frame(response)
            assert snapshot.event == "tau.snapshot"

            request_task = asyncio.create_task(
                services.approvals.request(session_id, tool_call, _tool())
            )
            pending = await _wait_for_pending(services.approvals, session_id=session_id)

            requested = await _read_sse_frame(response)
            assert requested.event_id == "1"
            assert requested.event == "tau.approval.requested"
            assert requested.data is not None
            assert requested.data["session_id"] == session_id
            assert requested.data["payload"]["approval_id"] == pending.approval_id
            assert requested.data["payload"]["arguments"] == {
                "path": "notes.txt",
                "token": "[REDACTED]",
            }

            pending_response = await client.get(f"/api/sessions/{session_id}/approvals")
            assert pending_response.status == 200
            assert (await pending_response.json())["approvals"] == [
                {
                    "approval_id": pending.approval_id,
                    "session_id": session_id,
                    "tool_call_id": "call-1",
                    "tool_name": "write",
                    "description": "Write a file.",
                    "arguments": {"path": "notes.txt", "token": "[REDACTED]"},
                    "created_at": pending.created_at,
                }
            ]

            resolved_response = await client.post(
                f"/api/approvals/{pending.approval_id}",
                json={"decision": "allow"},
                headers={"X-Request-ID": "approval-route-1"},
            )
            assert resolved_response.status == 200
            assert await resolved_response.json() == {
                "approval_id": pending.approval_id,
                "decision": "allow",
            }
            assert await request_task is True

            resolved = await _read_sse_frame(response)
            assert resolved.event_id == "2"
            assert resolved.event == "tau.approval.resolved"
            assert resolved.data is not None
            assert resolved.data["payload"]["approval_id"] == pending.approval_id
            assert resolved.data["payload"]["decision"] == "allow"

        empty_response = await client.get(f"/api/sessions/{session_id}/approvals")
        assert empty_response.status == 200
        assert (await empty_response.json()) == {"approvals": []}

        audit_response = await client.get("/api/audit", params={"session_id": session_id})
        assert audit_response.status == 200
        records = (await audit_response.json())["records"]
        requested_record = next(
            record for record in records if record["event_type"] == "tool.approval.requested"
        )
        resolved_record = next(
            record for record in records if record["event_type"] == "tool.approval.resolved"
        )
        assert requested_record["details"]["arguments"] == {
            "path": "notes.txt",
            "token": "[REDACTED]",
        }
        assert resolved_record["details"]["decision"] == "allow"
        assert resolved_record["request_id"] == "approval-route-1"
    finally:
        await client.close()
