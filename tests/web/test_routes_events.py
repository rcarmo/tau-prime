from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, replace
from typing import cast
from uuid import UUID

import pytest
from aiohttp import ClientResponse, web
from aiohttp.test_utils import TestClient, TestServer

from tau_agent import AgentEvent, MessageDeltaEvent
from tau_agent.types import JSONObject
from tau_web.app import SERVICES_KEY, create_app
from tau_web.config import WebConfig
from tau_web.events import WebEventEnvelope, build_web_event_envelope
from tau_web.services import TauWebServices


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@dataclass(frozen=True, slots=True)
class _SSEFrame:
    event_id: str | None
    event: str | None
    data: JSONObject | None
    comment: str | None


async def _start_client(app: web.Application) -> TestClient:
    client = TestClient(TestServer(app))
    await client.start_server()
    return client


def _services(client: TestClient) -> TauWebServices:
    return cast(TauWebServices, client.app[SERVICES_KEY])


async def _create_session(client: TestClient, session_id: str) -> str:
    record = await _services(client).sessions.create(
        workspace_root=_services(client).config.cwd,
        provider_name="test",
        model="model",
        agent_name=session_id,
        session_id=session_id,
    )
    return record.session_id


def _envelope(
    event: AgentEvent,
    *,
    session_id: str,
    run_id: str = "run-1",
    sequence: int,
) -> WebEventEnvelope:
    return build_web_event_envelope(
        session_id=session_id,
        run_id=run_id,
        sequence=sequence,
        event=event,
        event_id=UUID(int=sequence),
        created_at=f"2025-01-01T00:00:{sequence:02d}+00:00",
    )


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
    comment: str | None = None
    data_lines: list[str] = []
    for line in lines:
        if line.startswith(":"):
            comment = line[1:].strip() or None
            continue
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

    return _SSEFrame(event_id=event_id, event=event, data=data, comment=comment)


async def _read_next_event(response: ClientResponse, *, timeout: float = 1.0) -> _SSEFrame:
    async with asyncio.timeout(timeout):
        while True:
            frame = await _read_sse_frame(response, timeout=timeout)
            if frame.event is not None:
                return frame


@pytest.mark.anyio
async def test_events_route_streams_snapshot_then_live_event(web_config: WebConfig) -> None:
    client = await _start_client(create_app(web_config))
    try:
        session_id = await _create_session(client, "alpha")
        services = _services(client)

        async with client.get("/api/events", params={"session_id": session_id}) as response:
            assert response.status == 200
            assert response.headers["Content-Type"].startswith("text/event-stream")

            snapshot = await _read_sse_frame(response)

            assert snapshot.event_id == "0"
            assert snapshot.event == "tau.snapshot"
            assert snapshot.comment is None
            assert snapshot.data is not None
            assert snapshot.data["cursor"] == 0
            assert snapshot.data["timeline"] == []
            assert snapshot.data["runs"] == []
            assert snapshot.data["queue"] == []
            sessions = cast(list[JSONObject], snapshot.data["sessions"])
            assert [session["session_id"] for session in sessions] == [session_id]

            envelope = _envelope(
                MessageDeltaEvent(delta="hello"),
                session_id=session_id,
                sequence=1,
            )
            await services.broker.publish(envelope)

            live = await _read_sse_frame(response)

            assert live.event_id == "1"
            assert live.event == "tau.agent.message_delta"
            assert live.data == {
                "event_id": str(envelope.event_id),
                "type": envelope.type,
                "session_id": session_id,
                "run_id": envelope.run_id,
                "sequence": envelope.sequence,
                "payload": {"type": "message_delta", "delta": "hello"},
                "created_at": envelope.created_at,
            }
    finally:
        await client.close()


@pytest.mark.anyio
async def test_events_route_resume_replays_retained_events_without_snapshot(
    web_config: WebConfig,
) -> None:
    client = await _start_client(create_app(web_config))
    try:
        session_id = await _create_session(client, "alpha")
        envelope = _envelope(MessageDeltaEvent(delta="retained"), session_id=session_id, sequence=1)
        await _services(client).broker.publish(envelope)

        async with client.get(
            "/api/events",
            params={"session_id": session_id},
            headers={"Last-Event-ID": "0"},
        ) as response:
            frame = await _read_sse_frame(response)

            assert frame.event == "tau.agent.message_delta"
            assert frame.event != "tau.snapshot"
            assert frame.event_id == "1"
            assert frame.data is not None
            assert frame.data["event_id"] == str(envelope.event_id)
            assert frame.data["session_id"] == session_id
            assert frame.data["payload"] == {"type": "message_delta", "delta": "retained"}
    finally:
        await client.close()


@pytest.mark.anyio
async def test_events_route_stale_cursor_falls_back_to_snapshot(web_config: WebConfig) -> None:
    client = await _start_client(create_app(replace(web_config, sse_replay_capacity=1)))
    try:
        session_id = await _create_session(client, "alpha")
        services = _services(client)
        await services.broker.publish(
            _envelope(MessageDeltaEvent(delta="one"), session_id=session_id, sequence=1)
        )
        await services.broker.publish(
            _envelope(MessageDeltaEvent(delta="two"), session_id=session_id, sequence=2)
        )

        async with client.get(
            "/api/events",
            params={"session_id": session_id},
            headers={"Last-Event-ID": "0"},
        ) as response:
            frame = await _read_sse_frame(response)

            assert frame.event_id == "2"
            assert frame.event == "tau.snapshot"
            assert frame.data is not None
            assert frame.data["cursor"] == 2
            assert frame.data["timeline"] == []
    finally:
        await client.close()


@pytest.mark.anyio
async def test_events_route_session_filter_ignores_other_sessions_but_delivers_own(
    web_config: WebConfig,
) -> None:
    client = await _start_client(create_app(replace(web_config, sse_heartbeat_seconds=0.05)))
    try:
        alpha = await _create_session(client, "alpha")
        beta = await _create_session(client, "beta")
        services = _services(client)

        async with client.get("/api/events", params={"session_id": alpha}) as response:
            await _read_sse_frame(response)

            await services.broker.publish(
                _envelope(
                    MessageDeltaEvent(delta="beta"),
                    session_id=beta,
                    run_id="run-2",
                    sequence=1,
                )
            )
            heartbeat = await _read_sse_frame(response, timeout=0.5)

            assert heartbeat.event is None
            assert heartbeat.comment == "heartbeat"

            await services.broker.publish(
                _envelope(MessageDeltaEvent(delta="alpha"), session_id=alpha, sequence=2)
            )
            own_event = await _read_next_event(response, timeout=1.0)

            assert own_event.event == "tau.agent.message_delta"
            assert own_event.data is not None
            assert own_event.data["session_id"] == alpha
            assert own_event.data["payload"] == {"type": "message_delta", "delta": "alpha"}
    finally:
        await client.close()


@pytest.mark.anyio
@pytest.mark.parametrize("last_event_id", ["nope", "-1"])
async def test_events_route_rejects_malformed_or_negative_last_event_id(
    web_config: WebConfig,
    last_event_id: str,
) -> None:
    client = await _start_client(create_app(web_config))
    try:
        async with client.get("/api/events", headers={"Last-Event-ID": last_event_id}) as response:
            assert response.status == 400
            body = await response.json()

        assert body["error"]["code"] == "bad_request"
        assert body["error"]["message"] == "Last-Event-ID must be a non-negative integer."
    finally:
        await client.close()


@pytest.mark.anyio
async def test_events_route_rejects_unknown_session(web_config: WebConfig) -> None:
    client = await _start_client(create_app(web_config))
    try:
        async with client.get("/api/events", params={"session_id": "missing"}) as response:
            assert response.status == 404
            body = await response.json()

        assert body["error"]["code"] == "not_found"
        assert body["error"]["message"] == "Unknown session: missing"
    finally:
        await client.close()


@pytest.mark.anyio
async def test_events_route_open_stream_does_not_block_client_shutdown(
    web_config: WebConfig,
) -> None:
    client = await _start_client(create_app(replace(web_config, sse_heartbeat_seconds=60.0)))
    closed = False
    try:
        session_id = await _create_session(client, "alpha")
        response = await client.get("/api/events", params={"session_id": session_id})
        snapshot = await _read_sse_frame(response)

        assert snapshot.event == "tau.snapshot"

        async with asyncio.timeout(1.0):
            await client.close()
        closed = True
    finally:
        if not closed:
            await client.close()
