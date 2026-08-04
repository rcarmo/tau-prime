from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from tau_agent import AgentEndEvent, AgentEvent, AgentStartEvent, ErrorEvent, QueueUpdateEvent
from tau_web.app import SERVICES_KEY, create_app
from tau_web.config import WebConfig
from tau_web.services import TauWebServices
from tau_web.sqlite.repositories import RunRecord

_TERMINAL_RUN_STATUSES = frozenset({"completed", "cancelled", "failed", "interrupted"})


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@dataclass(slots=True)
class _Script:
    events: tuple[AgentEvent, ...] = ()
    started: asyncio.Event | None = None
    release: asyncio.Event | None = None
    exception: BaseException | None = None


class _FakeSession:
    def __init__(
        self,
        *,
        prompt_scripts: Sequence[_Script] = (),
        continue_scripts: Sequence[_Script] = (),
        queue_message_scripts: Sequence[_Script] = (),
        cooperative_cancel: bool = True,
    ) -> None:
        self._prompt_scripts: deque[_Script] = deque(prompt_scripts)
        self._continue_scripts: deque[_Script] = deque(continue_scripts)
        self._queue_message_scripts: deque[_Script] = deque(queue_message_scripts)
        self._cooperative_cancel = cooperative_cancel
        self._active_release: asyncio.Event | None = None
        self._active_run_token: int | None = None
        self._next_run_token = 0
        self.prompt_calls: list[str] = []
        self.continue_calls = 0
        self.queue_message_calls: list[tuple[str, str]] = []
        self.queued_steering: tuple[str, ...] = ()
        self.queued_follow_up: tuple[str, ...] = ()
        self.cancel_calls = 0
        self.close_calls = 0

    def prompt(
        self,
        content: str,
        *,
        streaming_behavior: str | None = None,
    ) -> AsyncIterator[AgentEvent]:
        assert streaming_behavior is None
        self.prompt_calls.append(content)
        return self._run_script(self._next_prompt_script())

    def continue_(self) -> AsyncIterator[AgentEvent]:
        self.continue_calls += 1
        return self._run_script(self._next_continue_script())

    async def queue_message(self, content: str, *, behavior: str) -> QueueUpdateEvent:
        active_run_token = self._active_run_token
        if active_run_token is None:
            raise RuntimeError("Session is idle; cannot queue a message.")
        self.queue_message_calls.append((content, behavior))
        script = self._queue_message_scripts.popleft() if self._queue_message_scripts else _Script()
        if script.started is not None:
            script.started.set()
        if script.release is not None:
            await script.release.wait()
        if script.exception is not None:
            raise script.exception
        if self._active_run_token != active_run_token:
            raise RuntimeError("Session active run changed while queueing a message.")
        if behavior == "steer":
            self.queued_steering = (*self.queued_steering, content)
        elif behavior == "follow_up":
            self.queued_follow_up = (*self.queued_follow_up, content)
        else:
            raise AssertionError(f"Unexpected queue behavior: {behavior!r}")
        return QueueUpdateEvent(
            steering=self.queued_steering,
            follow_up=self.queued_follow_up,
        )

    def cancel(self) -> None:
        self.cancel_calls += 1
        if self._cooperative_cancel and self._active_release is not None:
            self._active_release.set()

    async def aclose(self) -> None:
        self.close_calls += 1

    def _next_prompt_script(self) -> _Script:
        if not self._prompt_scripts:
            raise AssertionError("No prompt script was queued.")
        return self._prompt_scripts.popleft()

    def _next_continue_script(self) -> _Script:
        if not self._continue_scripts:
            raise AssertionError("No continue script was queued.")
        return self._continue_scripts.popleft()

    async def _run_script(self, script: _Script) -> AsyncIterator[AgentEvent]:
        self._active_release = script.release
        self._next_run_token += 1
        self._active_run_token = self._next_run_token
        try:
            if script.started is not None:
                script.started.set()
            if script.release is not None:
                await script.release.wait()
            for event in script.events:
                yield event
            if script.exception is not None:
                raise script.exception
        finally:
            self._active_run_token = None
            self._active_release = None


async def _start_client(app: web.Application) -> TestClient:
    client = TestClient(TestServer(app))
    await client.start_server()
    return client


def _services(app: web.Application) -> TauWebServices:
    return cast(TauWebServices, app[SERVICES_KEY])


async def _register_session(
    services: TauWebServices,
    *,
    session_id: str,
    session: _FakeSession,
) -> None:
    await services.sessions.create(
        workspace_root=Path(services.config.cwd),
        provider_name="test",
        model="model",
        agent_name=session_id,
        session_id=session_id,
    )
    services.runtime.register_session(session_id, session)


async def _create_durable_session(services: TauWebServices, *, session_id: str) -> None:
    await services.sessions.create(
        workspace_root=Path(services.config.cwd),
        provider_name="test",
        model="model",
        agent_name=session_id,
        session_id=session_id,
    )


async def _wait_for_run(
    services: TauWebServices,
    run_id: str,
    *,
    timeout: float = 1.0,
) -> RunRecord:
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        record = await services.runs.get(run_id)
        assert record is not None
        if record.status in _TERMINAL_RUN_STATUSES:
            return record
        if asyncio.get_running_loop().time() >= deadline:
            raise TimeoutError(f"Timed out waiting for run {run_id!r} to finish.")
        await asyncio.sleep(0.01)


@pytest.mark.anyio
async def test_run_routes_submit_continue_list_filter_and_get(
    web_config: WebConfig,
) -> None:
    app = create_app(web_config)
    client = await _start_client(app)
    services = _services(app)
    prompt_started = asyncio.Event()
    prompt_release = asyncio.Event()
    continue_started = asyncio.Event()
    continue_release = asyncio.Event()
    session = _FakeSession(
        prompt_scripts=(
            _Script(
                events=(AgentStartEvent(), AgentEndEvent()),
                started=prompt_started,
                release=prompt_release,
            ),
        ),
        continue_scripts=(
            _Script(
                events=(AgentStartEvent(), AgentEndEvent()),
                started=continue_started,
                release=continue_release,
            ),
        ),
    )
    await _register_session(services, session_id="alpha", session=session)

    try:
        async with client.post(
            "/api/sessions/alpha/runs",
            json={"content": "hello", "run_id": "prompt-run"},
        ) as response:
            assert response.status == 202
            prompt_current = await response.json()

        assert prompt_current["run_id"] == "prompt-run"
        assert prompt_current["session_id"] == "alpha"
        assert prompt_current["status"] in {"pending", "running"}

        await asyncio.wait_for(prompt_started.wait(), timeout=1.0)
        assert session.prompt_calls == ["hello"]

        async with client.get("/api/runs/prompt-run") as response:
            assert response.status == 200
            prompt_live = await response.json()

        assert prompt_live["run_id"] == "prompt-run"
        assert prompt_live["status"] in {"pending", "running"}

        prompt_release.set()
        prompt_done = await _wait_for_run(services, "prompt-run")
        assert prompt_done.status == "completed"

        async with client.post(
            "/api/sessions/alpha/runs",
            json={"continue": True, "run_id": "continue-run"},
        ) as response:
            assert response.status == 202
            continued_current = await response.json()

        assert continued_current["run_id"] == "continue-run"
        assert continued_current["session_id"] == "alpha"
        assert continued_current["status"] in {"pending", "running"}

        await asyncio.wait_for(continue_started.wait(), timeout=1.0)
        assert session.continue_calls == 1

        continue_release.set()
        continued_done = await _wait_for_run(services, "continue-run")
        assert continued_done.status == "completed"

        async with client.get("/api/sessions/alpha/runs") as response:
            assert response.status == 200
            listed = await response.json()

        assert {run["run_id"] for run in listed["runs"]} == {"prompt-run", "continue-run"}
        assert {run["status"] for run in listed["runs"]} == {"completed"}

        async with client.get("/api/sessions/alpha/runs?status=completed") as response:
            assert response.status == 200
            filtered = await response.json()

        assert {run["run_id"] for run in filtered["runs"]} == {"prompt-run", "continue-run"}

        async with client.get("/api/runs/continue-run") as response:
            assert response.status == 200
            fetched = await response.json()

        assert fetched["run_id"] == "continue-run"
        assert fetched["status"] == "completed"
        assert fetched["last_event_type"] == "agent_end"
    finally:
        prompt_release.set()
        continue_release.set()
        await client.close()


@pytest.mark.anyio
async def test_run_routes_cancel_abort_and_retry(web_config: WebConfig) -> None:
    app = create_app(web_config)
    client = await _start_client(app)
    services = _services(app)
    cancel_started = asyncio.Event()
    abort_started = asyncio.Event()
    cancel_session = _FakeSession(
        prompt_scripts=(_Script(started=cancel_started, release=asyncio.Event()),),
        continue_scripts=(_Script(events=(AgentStartEvent(), AgentEndEvent())),),
    )
    abort_session = _FakeSession(
        prompt_scripts=(_Script(started=abort_started, release=asyncio.Event()),),
        cooperative_cancel=False,
    )
    failed_session = _FakeSession(
        prompt_scripts=(
            _Script(events=(AgentStartEvent(), ErrorEvent(message="boom", recoverable=False))),
        ),
        continue_scripts=(_Script(events=(AgentStartEvent(), AgentEndEvent())),),
    )
    await _register_session(services, session_id="cancelled", session=cancel_session)
    await _register_session(services, session_id="aborted", session=abort_session)
    await _register_session(services, session_id="failed", session=failed_session)

    try:
        async with client.post(
            "/api/sessions/cancelled/runs",
            json={"content": "cancel", "run_id": "cancel-run"},
        ) as response:
            assert response.status == 202

        await asyncio.wait_for(cancel_started.wait(), timeout=1.0)

        async with client.post("/api/runs/cancel-run/cancel") as response:
            assert response.status == 202
            cancelled_current = await response.json()

        assert cancelled_current["accepted"] is True
        cancelled = await _wait_for_run(services, "cancel-run")
        assert cancelled.status == "cancelled"

        async with client.post("/api/runs/cancel-run/retry") as response:
            assert response.status == 202
            cancelled_retry = await response.json()

        cancelled_retry_id = str(cancelled_retry["run"]["run_id"])
        retried_cancelled = await _wait_for_run(services, cancelled_retry_id)
        assert cancelled_retry["retry_of"] == "cancel-run"
        assert cancelled_retry["run"]["status"] in {"pending", "running"}
        assert cancelled_retry_id != "cancel-run"
        assert retried_cancelled.status == "completed"
        assert cancel_session.continue_calls == 1

        async with client.post(
            "/api/sessions/aborted/runs",
            json={"content": "abort", "run_id": "abort-run"},
        ) as response:
            assert response.status == 202

        await asyncio.wait_for(abort_started.wait(), timeout=1.0)

        async with client.post("/api/runs/abort-run/abort") as response:
            assert response.status == 202
            aborted_current = await response.json()

        assert aborted_current["accepted"] is True
        aborted = await _wait_for_run(services, "abort-run")
        assert aborted.status == "interrupted"
        assert abort_session.cancel_calls == 1

        async with client.post(
            "/api/sessions/failed/runs",
            json={"content": "fail", "run_id": "failed-run"},
        ) as response:
            assert response.status == 202
            failed_current = await response.json()

        assert failed_current["status"] in {"pending", "running", "failed"}
        failed = await _wait_for_run(services, "failed-run")
        assert failed.status == "failed"

        async with client.post("/api/runs/failed-run/retry") as response:
            assert response.status == 202
            failed_retry = await response.json()

        failed_retry_id = str(failed_retry["run"]["run_id"])
        retried_failed = await _wait_for_run(services, failed_retry_id)
        assert failed_retry["retry_of"] == "failed-run"
        assert failed_retry["run"]["status"] in {"pending", "running", "completed"}
        assert failed_retry_id != "failed-run"
        assert retried_failed.status == "completed"
        assert failed_session.continue_calls == 1
    finally:
        await client.close()


@pytest.mark.anyio
async def test_run_routes_enqueue_list_messages_and_dispatch(web_config: WebConfig) -> None:
    app = create_app(web_config)
    client = await _start_client(app)
    services = _services(app)
    run_started = asyncio.Event()
    run_release = asyncio.Event()
    session = _FakeSession(
        prompt_scripts=(
            _Script(
                events=(AgentStartEvent(), AgentEndEvent()),
                started=run_started,
                release=run_release,
            ),
        )
    )
    await _register_session(services, session_id="queue", session=session)

    try:
        async with client.post(
            "/api/sessions/queue/runs",
            json={"content": "work", "run_id": "queue-run"},
        ) as response:
            assert response.status == 202

        await asyncio.wait_for(run_started.wait(), timeout=1.0)

        async with client.post(
            "/api/sessions/queue/queue",
            json={"content": "backlog", "kind": "follow_up"},
        ) as response:
            assert response.status == 201
            backlog = await response.json()

        assert backlog["queue_kind"] == "follow_up"
        assert backlog["consumed_at"] is None

        async with client.post(
            "/api/runs/queue-run/messages",
            json={"content": "steer-now", "kind": "steer"},
        ) as response:
            assert response.status == 200
            steer_now = await response.json()

        assert steer_now["queue_kind"] == "steer"
        assert steer_now["consumed_at"] is not None
        assert session.queue_message_calls == [("steer-now", "steer")]

        async with client.post(
            "/api/runs/queue-run/messages",
            json={"content": "follow-later", "kind": "follow_up"},
        ) as response:
            assert response.status == 202
            follow_later = await response.json()

        assert follow_later["queue_kind"] == "follow_up"
        assert follow_later["consumed_at"] is None
        assert session.queue_message_calls == [("steer-now", "steer")]

        async with client.get("/api/sessions/queue/queue?kind=follow_up") as response:
            assert response.status == 200
            pending_follow_up = await response.json()

        assert [record["queue_id"] for record in pending_follow_up["queue"]] == [
            backlog["queue_id"],
            follow_later["queue_id"],
        ]

        async with client.post("/api/runs/queue-run/queue/follow_up/dispatch") as response:
            assert response.status == 200
            first_dispatch = await response.json()

        assert first_dispatch["queue_id"] == backlog["queue_id"]
        assert first_dispatch["consumed_at"] is not None
        assert session.queue_message_calls == [
            ("steer-now", "steer"),
            ("backlog", "follow_up"),
        ]

        async with client.get("/api/sessions/queue/queue?kind=follow_up") as response:
            assert response.status == 200
            remaining_follow_up = await response.json()

        assert [record["queue_id"] for record in remaining_follow_up["queue"]] == [
            follow_later["queue_id"],
        ]

        async with client.post("/api/runs/queue-run/queue/follow_up/dispatch") as response:
            assert response.status == 200
            second_dispatch = await response.json()

        assert second_dispatch["queue_id"] == follow_later["queue_id"]
        assert second_dispatch["consumed_at"] is not None
        assert session.queue_message_calls == [
            ("steer-now", "steer"),
            ("backlog", "follow_up"),
            ("follow-later", "follow_up"),
        ]

        async with client.post("/api/runs/queue-run/queue/follow_up/dispatch") as response:
            assert response.status == 204

        async with client.get(
            "/api/sessions/queue/queue?kind=follow_up&include_consumed=true"
        ) as response:
            assert response.status == 200
            all_follow_up = await response.json()

        assert [record["queue_id"] for record in all_follow_up["queue"]] == [
            backlog["queue_id"],
            follow_later["queue_id"],
        ]
        assert all(record["consumed_at"] is not None for record in all_follow_up["queue"])

        async with client.get(
            "/api/sessions/queue/queue?kind=steer&include_consumed=true"
        ) as response:
            assert response.status == 200
            all_steer = await response.json()

        assert [record["queue_id"] for record in all_steer["queue"]] == [steer_now["queue_id"]]
        assert all_steer["queue"][0]["consumed_at"] is not None
    finally:
        run_release.set()
        await _wait_for_run(services, "queue-run")
        await client.close()


@pytest.mark.anyio
async def test_run_routes_validate_requests_and_report_missing_or_unregistered_resources(
    web_config: WebConfig,
) -> None:
    app = create_app(web_config)
    client = await _start_client(app)
    services = _services(app)
    run_started = asyncio.Event()
    run_release = asyncio.Event()
    session = _FakeSession(
        prompt_scripts=(
            _Script(
                events=(AgentStartEvent(), AgentEndEvent()),
                started=run_started,
                release=run_release,
            ),
        )
    )
    await _register_session(services, session_id="alpha", session=session)
    await _create_durable_session(services, session_id="orphan")

    try:
        async with client.post(
            "/api/sessions/alpha/runs",
            json={"content": "hello", "run_id": "validation-run"},
        ) as response:
            assert response.status == 202

        await asyncio.wait_for(run_started.wait(), timeout=1.0)

        async with client.post(
            "/api/sessions/alpha/runs",
            json={"content": "hello", "extra": True},
        ) as response:
            assert response.status == 400
            unknown_field = await response.json()

        assert unknown_field["error"]["code"] == "bad_request"
        assert unknown_field["error"]["message"] == "Unknown field(s): extra."

        async with client.post(
            "/api/sessions/alpha/runs",
            json={"continue": "yes"},
        ) as response:
            assert response.status == 400
            bad_continue = await response.json()

        assert bad_continue["error"]["code"] == "bad_request"
        assert bad_continue["error"]["message"] == "Field 'continue' must be a boolean."

        async with client.get("/api/sessions/alpha/runs?status=bogus") as response:
            assert response.status == 400
            bad_status = await response.json()

        assert bad_status["error"]["code"] == "bad_request"
        assert bad_status["error"]["message"] == "Unknown run status: bogus"

        async with client.get("/api/sessions/alpha/queue?include_consumed=maybe") as response:
            assert response.status == 400
            bad_bool = await response.json()

        assert bad_bool["error"]["code"] == "bad_request"
        assert bad_bool["error"]["message"] == (
            "Query parameter 'include_consumed' must be a boolean."
        )

        async with client.post(
            "/api/runs/validation-run/messages",
            json={"content": "hello", "kind": "later"},
        ) as response:
            assert response.status == 400
            bad_kind = await response.json()

        assert bad_kind["error"]["code"] == "bad_request"
        assert bad_kind["error"]["message"] == "Queue kind must be 'steer' or 'follow_up'."

        async with client.get("/api/sessions/missing/runs") as response:
            assert response.status == 404
            missing_session = await response.json()

        assert missing_session["error"]["code"] == "not_found"
        assert missing_session["error"]["message"] == "Unknown session: missing"

        async with client.get("/api/runs/missing") as response:
            assert response.status == 404
            missing_run = await response.json()

        assert missing_run["error"]["code"] == "not_found"
        assert missing_run["error"]["message"] == "Unknown run: missing"

        async with client.post("/api/sessions/orphan/runs", json={"content": "hello"}) as response:
            assert response.status == 409
            unregistered = await response.json()

        assert unregistered["error"]["code"] == "conflict"
        assert "not registered" in unregistered["error"]["message"]
    finally:
        run_release.set()
        await _wait_for_run(services, "validation-run")
        await client.close()
