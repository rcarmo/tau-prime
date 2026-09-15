from __future__ import annotations

import asyncio
import re

import pytest

from tau_extensions.runtime import DisposalHandle
from tau_extensions.web import (
    MAX_ACTION_PAYLOAD_BYTES,
    ActionDefinition,
    ActionError,
    ActionExecutor,
    ActionRegistry,
    ActionRequest,
    ActionResult,
    Invalidation,
    PatchBuffer,
    PropertyPatch,
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def _ok_handler(_context: object) -> ActionResult:
    return ActionResult(data={"ok": True})


def _request(**overrides: object) -> ActionRequest:
    payload = {
        "request_id": "req-1",
        "extension_id": "com.example.demo",
        "action_id": "refresh-status",
        "view_id": "status-view",
        "payload": {"value": 1},
        "idempotency_key": None,
    }
    payload.update(overrides)
    return ActionRequest(**payload)


def _expect_action_error(factory: object, code: str, message: str | None = None) -> ActionError:
    with pytest.raises(ActionError) as excinfo:
        factory()
    assert excinfo.value.code == code
    if message is not None:
        assert re.search(message, str(excinfo.value))
    return excinfo.value


def test_action_models_and_registry_validate_and_dispose() -> None:
    request = _request(payload={"meta": {"ok": True}, "items": [1, None, False]})
    patch = PropertyPatch(
        view_id="status-view",
        path="/components/0/text",
        value={"label": "done"},
        sequence=2,
    )
    result = ActionResult(
        data={"status": "ok"},
        invalidations=(
            Invalidation(target="view", key="status-view"),
            Invalidation(target="usage"),
        ),
        patches=(patch,),
    )
    definition = ActionDefinition(id="refresh-status", handler=_ok_handler, concurrency=2)
    registry = ActionRegistry()

    handle = registry.register("com.example.demo", definition)

    assert isinstance(handle, DisposalHandle)
    assert request.payload["items"] == (1, None, False)
    assert request.payload["meta"] == {"ok": True}
    assert result.invalidations == (
        Invalidation(target="view", key="status-view"),
        Invalidation(target="usage"),
    )
    assert result.patches == (patch,)
    assert registry.get("com.example.demo", "refresh-status") == definition

    duplicate = _expect_action_error(
        lambda: registry.register("com.example.demo", definition),
        "duplicate_action",
        "duplicate action",
    )
    assert "refresh-status" in str(duplicate)

    handle.dispose()
    handle.dispose()

    assert handle.disposed is True
    assert registry.get("com.example.demo", "refresh-status") is None


@pytest.mark.parametrize(
    ("factory", "code", "message"),
    [
        (
            lambda: _request(request_id="bad space"),
            "invalid_request",
            r"request_id must be a safe identifier",
        ),
        (
            lambda: _request(payload={"bad": float("nan")}),
            "invalid_request",
            r"payload\.bad contains a non-finite number",
        ),
        (
            lambda: _request(payload={"blob": "x" * MAX_ACTION_PAYLOAD_BYTES}),
            "invalid_request",
            r"payload JSON exceeds",
        ),
        (
            lambda: PropertyPatch(view_id="status-view", path="not/a/pointer", value=1, sequence=0),
            "invalid_patch",
            r"path must be a JSON pointer-like path",
        ),
        (
            lambda: PropertyPatch(
                view_id="status-view", path="/value", value=float("inf"), sequence=0
            ),
            "invalid_patch",
            r"value contains a non-finite number",
        ),
        (
            lambda: ActionResult(data={"bad": float("nan")}),
            "invalid_result",
            r"data\.bad contains a non-finite number",
        ),
    ],
)
def test_action_models_reject_invalid_payloads_and_types(
    factory: object,
    code: str,
    message: str,
) -> None:
    _expect_action_error(factory, code, message)


@pytest.mark.anyio
async def test_action_executor_allows_sync_approval_and_returns_invalidations_and_patches() -> None:
    seen: list[tuple[str, str]] = []
    approvals: list[tuple[str, str]] = []

    async def handler(context: object) -> ActionResult:
        request = context.request
        seen.append((request.request_id, request.action_id))
        return ActionResult(
            data={"status": "ok"},
            invalidations=(
                Invalidation(target="view", key=request.view_id),
                Invalidation(target="usage"),
            ),
            patches=(
                PropertyPatch(
                    view_id=request.view_id,
                    path="/components/0/text",
                    value="ready",
                    sequence=1,
                ),
            ),
        )

    registry = ActionRegistry()
    registry.register(
        "com.example.demo",
        ActionDefinition(
            id="refresh-status",
            handler=handler,
            requires_approval=True,
            timeout_seconds=1.0,
            concurrency=2,
        ),
    )
    executor = ActionExecutor(
        registry,
        approval_callback=lambda request, definition: (
            approvals.append((request.request_id, definition.id)) or True
        ),
    )

    result = await executor.execute(_request())

    assert seen == [("req-1", "refresh-status")]
    assert approvals == [("req-1", "refresh-status")]
    assert result == ActionResult(
        data={"status": "ok"},
        invalidations=(
            Invalidation(target="view", key="status-view"),
            Invalidation(target="usage"),
        ),
        patches=(
            PropertyPatch(
                view_id="status-view",
                path="/components/0/text",
                value="ready",
                sequence=1,
            ),
        ),
    )


@pytest.mark.anyio
async def test_action_executor_denies_async_approval_without_running_handler() -> None:
    called = False

    async def handler(_context: object) -> ActionResult:
        nonlocal called
        called = True
        return ActionResult(data={"ok": True})

    async def deny(_request: ActionRequest, _definition: ActionDefinition) -> bool:
        return False

    registry = ActionRegistry()
    registry.register(
        "com.example.demo",
        ActionDefinition(id="refresh-status", handler=handler, requires_approval=True),
    )
    executor = ActionExecutor(registry, approval_callback=deny)

    with pytest.raises(ActionError) as excinfo:
        await executor.execute(_request())

    assert excinfo.value.code == "approval_denied"
    assert called is False
    assert executor.active_request_ids == ()


@pytest.mark.anyio
async def test_action_executor_times_out_handlers() -> None:
    async def handler(_context: object) -> ActionResult:
        await asyncio.sleep(0.2)
        return ActionResult(data={"ok": True})

    registry = ActionRegistry()
    registry.register(
        "com.example.demo",
        ActionDefinition(id="refresh-status", handler=handler, timeout_seconds=0.05),
    )
    executor = ActionExecutor(registry)

    with pytest.raises(ActionError) as excinfo:
        await executor.execute(_request())

    assert excinfo.value.code == "timeout"
    assert executor.active_request_ids == ()


@pytest.mark.anyio
async def test_action_executor_cancellation_sets_event_and_cleans_up() -> None:
    started = asyncio.Event()
    observed = asyncio.Event()

    async def handler(context: object) -> ActionResult:
        started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            observed.set()
            context.raise_if_cancelled()
        raise AssertionError("unreachable")

    registry = ActionRegistry()
    registry.register("com.example.demo", ActionDefinition(id="refresh-status", handler=handler))
    executor = ActionExecutor(registry)
    request = _request()

    task = asyncio.create_task(executor.execute(request))
    await started.wait()

    assert executor.cancel(request.request_id) is True

    with pytest.raises(ActionError) as excinfo:
        await task

    await observed.wait()
    assert excinfo.value.code == "cancelled"
    assert executor.active_request_ids == ()
    assert executor.cancel(request.request_id) is False


@pytest.mark.anyio
async def test_action_executor_enforces_global_concurrency() -> None:
    entered_one = asyncio.Event()
    entered_two = asyncio.Event()
    release_one = asyncio.Event()
    release_two = asyncio.Event()

    async def handler_one(_context: object) -> ActionResult:
        entered_one.set()
        await release_one.wait()
        return ActionResult(data={"action": 1})

    async def handler_two(_context: object) -> ActionResult:
        entered_two.set()
        await release_two.wait()
        return ActionResult(data={"action": 2})

    registry = ActionRegistry()
    registry.register(
        "com.example.demo",
        ActionDefinition(id="refresh-status", handler=handler_one, concurrency=2),
    )
    registry.register(
        "com.example.demo", ActionDefinition(id="rebuild-cache", handler=handler_two, concurrency=2)
    )
    executor = ActionExecutor(registry, max_concurrency=1)

    first = asyncio.create_task(executor.execute(_request()))
    await entered_one.wait()

    second = asyncio.create_task(
        executor.execute(
            _request(request_id="req-2", action_id="rebuild-cache", payload={"value": 2})
        )
    )
    await asyncio.sleep(0.01)

    assert entered_two.is_set() is False

    release_one.set()
    await entered_two.wait()
    release_two.set()

    first_result, second_result = await asyncio.gather(first, second)
    assert first_result.data == {"action": 1}
    assert second_result.data == {"action": 2}


@pytest.mark.anyio
async def test_action_executor_enforces_per_action_concurrency() -> None:
    entered_first = asyncio.Event()
    entered_second = asyncio.Event()
    release_first = asyncio.Event()
    order: list[str] = []

    async def handler(context: object) -> ActionResult:
        order.append(context.request.request_id)
        if context.request.request_id == "req-1":
            entered_first.set()
            await release_first.wait()
        else:
            entered_second.set()
        return ActionResult(data={"request_id": context.request.request_id})

    registry = ActionRegistry()
    registry.register(
        "com.example.demo",
        ActionDefinition(id="refresh-status", handler=handler, concurrency=1),
    )
    executor = ActionExecutor(registry, max_concurrency=2)

    first = asyncio.create_task(executor.execute(_request(request_id="req-1")))
    await entered_first.wait()

    second = asyncio.create_task(executor.execute(_request(request_id="req-2")))
    await asyncio.sleep(0.01)
    assert entered_second.is_set() is False

    release_first.set()
    await entered_second.wait()

    first_result, second_result = await asyncio.gather(first, second)
    assert first_result.data == {"request_id": "req-1"}
    assert second_result.data == {"request_id": "req-2"}
    assert order == ["req-1", "req-2"]


@pytest.mark.anyio
async def test_action_executor_dedupes_concurrent_idempotent_requests_and_caches_results() -> None:
    calls = 0
    started = asyncio.Event()
    release = asyncio.Event()

    async def handler(_context: object) -> ActionResult:
        nonlocal calls
        calls += 1
        started.set()
        await release.wait()
        return ActionResult(data={"ok": True})

    registry = ActionRegistry()
    registry.register(
        "com.example.demo",
        ActionDefinition(id="refresh-status", handler=handler, idempotent=True),
    )
    executor = ActionExecutor(registry)

    first = asyncio.create_task(
        executor.execute(_request(idempotency_key="same-key", payload={"a": 1, "b": 2}))
    )
    await started.wait()
    second = asyncio.create_task(
        executor.execute(
            _request(request_id="req-2", idempotency_key="same-key", payload={"b": 2, "a": 1})
        )
    )
    await asyncio.sleep(0.01)

    assert calls == 1

    release.set()
    first_result, second_result = await asyncio.gather(first, second)
    cached_result = await executor.execute(
        _request(request_id="req-3", idempotency_key="same-key", payload={"b": 2, "a": 1})
    )

    assert first_result is second_result
    assert cached_result is first_result
    assert calls == 1


@pytest.mark.anyio
async def test_action_executor_requires_idempotency_keys_and_rejects_conflicts() -> None:
    started = asyncio.Event()
    release = asyncio.Event()

    async def handler(_context: object) -> ActionResult:
        started.set()
        await release.wait()
        return ActionResult(data={"ok": True})

    registry = ActionRegistry()
    registry.register(
        "com.example.demo",
        ActionDefinition(id="refresh-status", handler=handler, idempotent=True),
    )
    executor = ActionExecutor(registry)

    with pytest.raises(ActionError) as missing_key:
        await executor.execute(_request())
    assert missing_key.value.code == "idempotency_required"

    leader = asyncio.create_task(
        executor.execute(_request(idempotency_key="same-key", payload={"value": 1}))
    )
    await started.wait()

    with pytest.raises(ActionError) as inflight_conflict:
        await executor.execute(
            _request(request_id="req-2", idempotency_key="same-key", payload={"value": 2})
        )
    assert inflight_conflict.value.code == "idempotency_conflict"

    release.set()
    await leader

    with pytest.raises(ActionError) as cached_conflict:
        await executor.execute(
            _request(request_id="req-3", idempotency_key="same-key", payload={"value": 3})
        )
    assert cached_conflict.value.code == "idempotency_conflict"


@pytest.mark.anyio
async def test_action_executor_uses_lru_bound_for_completed_idempotent_results() -> None:
    calls: list[str] = []

    async def handler(context: object) -> ActionResult:
        calls.append(context.request.idempotency_key or "")
        return ActionResult(data={"key": context.request.idempotency_key})

    registry = ActionRegistry()
    registry.register(
        "com.example.demo",
        ActionDefinition(id="refresh-status", handler=handler, idempotent=True),
    )
    executor = ActionExecutor(registry, completed_idempotency_capacity=2)

    result_a = await executor.execute(_request(idempotency_key="key-a"))
    result_b = await executor.execute(_request(request_id="req-2", idempotency_key="key-b"))
    assert await executor.execute(_request(request_id="req-3", idempotency_key="key-a")) is result_a

    result_c = await executor.execute(_request(request_id="req-4", idempotency_key="key-c"))
    result_b_again = await executor.execute(_request(request_id="req-5", idempotency_key="key-b"))

    assert result_b_again is not result_b
    assert result_c.data == {"key": "key-c"}
    assert calls == ["key-a", "key-b", "key-c", "key-b"]


@pytest.mark.anyio
async def test_action_executor_isolates_handler_exceptions() -> None:
    async def handler(_context: object) -> ActionResult:
        raise RuntimeError("boom")

    registry = ActionRegistry()
    registry.register("com.example.demo", ActionDefinition(id="refresh-status", handler=handler))
    executor = ActionExecutor(registry)

    with pytest.raises(ActionError) as excinfo:
        await executor.execute(_request())

    assert excinfo.value.code == "internal"
    assert "boom" in str(excinfo.value)
    assert executor.active_request_ids == ()


def test_patch_buffer_coalesces_latest_sequence_rejects_stale_and_drains_deterministically() -> (
    None
):
    buffer = PatchBuffer(max_entries=2)
    initial = PropertyPatch(
        view_id="status-view", path="/components/0/text", value="one", sequence=1
    )
    replacement = PropertyPatch(
        view_id="status-view", path="/components/0/text", value="two", sequence=3
    )
    sibling = PropertyPatch(
        view_id="status-view", path="/components/1/text", value="other", sequence=0
    )

    buffer.add(initial)
    buffer.add(sibling)
    buffer.add(replacement)

    stale = _expect_action_error(
        lambda: buffer.add(
            PropertyPatch(
                view_id="status-view", path="/components/0/text", value="stale", sequence=2
            )
        ),
        "stale_patch",
        r"patch sequence must be greater",
    )
    assert "previous sequence" in str(stale)

    assert buffer.drain() == (sibling, replacement)
    assert buffer.drain() == ()

    buffer.add(initial)
    buffer.add(sibling)
    overflow = _expect_action_error(
        lambda: buffer.add(
            PropertyPatch(
                view_id="status-view", path="/components/2/text", value="extra", sequence=4
            )
        ),
        "patch_buffer_full",
        r"patch buffer exceeds 2 unique entries",
    )
    assert overflow.code == "patch_buffer_full"
