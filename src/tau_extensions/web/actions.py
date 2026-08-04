"""Portable async action contracts for Tau web extensions."""

from __future__ import annotations

import asyncio
import inspect
import json
import math
import re
from collections import OrderedDict, defaultdict
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal, cast

from tau_agent.types import JSONObject, JSONValue
from tau_extensions.runtime import DisposalHandle
from tau_extensions.web.components import (
    MAX_ACTION_PAYLOAD_BYTES,
    FrozenJSONObject,
    FrozenJSONValue,
)

MAX_ACTION_RESULT_BYTES = 32 * 1024
MAX_ACTION_RESULT_INVALIDATIONS = 32
MAX_ACTION_RESULT_PATCHES = 128
MAX_ACTION_TIMEOUT_SECONDS = 120.0
MAX_EXECUTOR_CONCURRENCY = 128
MAX_EXTENSION_ID_BYTES = 128
MAX_IDEMPOTENCY_CACHE_ENTRIES = 256
MAX_IDEMPOTENCY_KEY_BYTES = 128
MAX_INVALIDATION_KEY_BYTES = 256
MAX_PATCH_BUFFER_ENTRIES = 256
MAX_PROPERTY_PATCH_PATH_BYTES = 512
MAX_PROPERTY_PATCH_VALUE_BYTES = 8 * 1024
MAX_REQUEST_ID_BYTES = 128
MAX_SAFE_SLUG_BYTES = 64
MIN_ACTION_TIMEOUT_SECONDS = 0.05


type ActionErrorCode = Literal[
    "action_not_found",
    "approval_denied",
    "cancelled",
    "duplicate_action",
    "duplicate_request",
    "idempotency_conflict",
    "idempotency_required",
    "internal",
    "invalid_definition",
    "invalid_patch",
    "invalid_request",
    "invalid_result",
    "patch_buffer_full",
    "stale_patch",
    "timeout",
]
type ActionHandler = Callable[["ActionContext"], Awaitable["ActionResult"]]
type ApprovalCallback = Callable[["ActionRequest", "ActionDefinition"], bool | Awaitable[bool]]
type InflightKey = tuple[str, str, str]

_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")
_SAFE_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
_POINTER_RE = re.compile(r"^/(?:[^/\x00]+)(?:/[^/\x00]+)*$")
_INVALIDATION_TARGETS: tuple[str, ...] = ("view", "session", "queue", "usage", "search")


class ActionError(ValueError):
    """Stable error raised for action validation and execution failures."""

    def __init__(self, code: ActionErrorCode, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class ActionRequest:
    """One validated extension action request."""

    request_id: str
    extension_id: str
    action_id: str
    view_id: str
    payload: FrozenJSONObject
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "request_id",
            _require_safe_name(
                self.request_id,
                field_name="request_id",
                max_bytes=MAX_REQUEST_ID_BYTES,
                code="invalid_request",
            ),
        )
        object.__setattr__(
            self,
            "extension_id",
            _require_safe_name(
                self.extension_id,
                field_name="extension_id",
                max_bytes=MAX_EXTENSION_ID_BYTES,
                code="invalid_request",
            ),
        )
        object.__setattr__(
            self,
            "action_id",
            _require_slug(
                self.action_id,
                field_name="action_id",
                max_bytes=MAX_SAFE_SLUG_BYTES,
                code="invalid_request",
            ),
        )
        object.__setattr__(
            self,
            "view_id",
            _require_slug(
                self.view_id,
                field_name="view_id",
                max_bytes=MAX_SAFE_SLUG_BYTES,
                code="invalid_request",
            ),
        )
        if self.idempotency_key is not None:
            object.__setattr__(
                self,
                "idempotency_key",
                _require_safe_name(
                    self.idempotency_key,
                    field_name="idempotency_key",
                    max_bytes=MAX_IDEMPOTENCY_KEY_BYTES,
                    code="invalid_request",
                ),
            )
        object.__setattr__(
            self,
            "payload",
            _freeze_json_object(self.payload, path="payload", code="invalid_request"),
        )
        _validate_json_size(
            self.payload,
            path="payload",
            limit=MAX_ACTION_PAYLOAD_BYTES,
            code="invalid_request",
        )


@dataclass(frozen=True, slots=True)
class ActionContext:
    """Runtime request context passed to one async action handler."""

    request: ActionRequest
    cancellation: asyncio.Event = field(default_factory=asyncio.Event)

    def __post_init__(self) -> None:
        if not isinstance(self.request, ActionRequest):
            raise ActionError("invalid_request", "request must be an ActionRequest")
        if not isinstance(self.cancellation, asyncio.Event):
            raise ActionError("invalid_request", "cancellation must be an asyncio.Event")

    def raise_if_cancelled(self) -> None:
        """Raise a stable cancellation error once this action has been cancelled."""
        if self.cancellation.is_set():
            raise ActionError(
                "cancelled",
                f"action request {self.request.request_id!r} was cancelled",
            )


@dataclass(frozen=True, slots=True)
class Invalidation:
    """One frontend invalidation request produced by an action."""

    target: Literal["view", "session", "queue", "usage", "search"]
    key: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "target",
            cast(
                Literal["view", "session", "queue", "usage", "search"],
                _require_literal(
                    self.target,
                    field_name="target",
                    allowed=_INVALIDATION_TARGETS,
                    code="invalid_result",
                ),
            ),
        )
        if self.key is not None:
            object.__setattr__(
                self,
                "key",
                _require_bounded_string(
                    self.key,
                    field_name="key",
                    max_bytes=MAX_INVALIDATION_KEY_BYTES,
                    non_blank=True,
                    code="invalid_result",
                ),
            )


@dataclass(frozen=True, slots=True)
class PropertyPatch:
    """One property-level patch for a contributed view."""

    view_id: str
    path: str
    value: FrozenJSONValue
    sequence: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "view_id",
            _require_slug(
                self.view_id,
                field_name="view_id",
                max_bytes=MAX_SAFE_SLUG_BYTES,
                code="invalid_patch",
            ),
        )
        object.__setattr__(
            self,
            "path",
            _require_pointer_path(self.path, field_name="path", code="invalid_patch"),
        )
        object.__setattr__(
            self,
            "value",
            _freeze_json_value(self.value, path="value", code="invalid_patch"),
        )
        _validate_json_size(
            self.value,
            path="value",
            limit=MAX_PROPERTY_PATCH_VALUE_BYTES,
            code="invalid_patch",
        )
        object.__setattr__(
            self,
            "sequence",
            _require_nonnegative_int(self.sequence, field_name="sequence", code="invalid_patch"),
        )


@dataclass(frozen=True, slots=True)
class ActionResult:
    """One validated action result."""

    data: FrozenJSONObject
    invalidations: tuple[Invalidation, ...] = ()
    patches: tuple[PropertyPatch, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "data",
            _freeze_json_object(self.data, path="data", code="invalid_result"),
        )
        _validate_json_size(
            self.data,
            path="data",
            limit=MAX_ACTION_RESULT_BYTES,
            code="invalid_result",
        )
        invalidations = tuple(self.invalidations)
        if len(invalidations) > MAX_ACTION_RESULT_INVALIDATIONS:
            raise ActionError(
                "invalid_result",
                f"invalidations must contain at most {MAX_ACTION_RESULT_INVALIDATIONS} items",
            )
        if not all(isinstance(item, Invalidation) for item in invalidations):
            raise ActionError(
                "invalid_result", "invalidations must contain only Invalidation values"
            )
        patches = tuple(self.patches)
        if len(patches) > MAX_ACTION_RESULT_PATCHES:
            raise ActionError(
                "invalid_result",
                f"patches must contain at most {MAX_ACTION_RESULT_PATCHES} items",
            )
        if not all(isinstance(item, PropertyPatch) for item in patches):
            raise ActionError("invalid_result", "patches must contain only PropertyPatch values")
        object.__setattr__(self, "invalidations", invalidations)
        object.__setattr__(self, "patches", patches)


@dataclass(frozen=True, slots=True)
class ActionDefinition:
    """One registered action handler and its execution policy."""

    id: str
    handler: ActionHandler
    requires_approval: bool = False
    timeout_seconds: float = 30.0
    concurrency: int = 1
    idempotent: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "id",
            _require_slug(
                self.id,
                field_name="id",
                max_bytes=MAX_SAFE_SLUG_BYTES,
                code="invalid_definition",
            ),
        )
        if not _is_async_callable(self.handler):
            raise ActionError("invalid_definition", "handler must be an async callable")
        object.__setattr__(
            self,
            "requires_approval",
            _require_bool(
                self.requires_approval,
                field_name="requires_approval",
                code="invalid_definition",
            ),
        )
        object.__setattr__(
            self,
            "timeout_seconds",
            _require_bounded_number(
                self.timeout_seconds,
                field_name="timeout_seconds",
                minimum=MIN_ACTION_TIMEOUT_SECONDS,
                maximum=MAX_ACTION_TIMEOUT_SECONDS,
                code="invalid_definition",
            ),
        )
        object.__setattr__(
            self,
            "concurrency",
            _require_bounded_int(
                self.concurrency,
                field_name="concurrency",
                minimum=1,
                maximum=32,
                code="invalid_definition",
            ),
        )
        object.__setattr__(
            self,
            "idempotent",
            _require_bool(self.idempotent, field_name="idempotent", code="invalid_definition"),
        )


class ActionRegistry:
    """Registry of extension-scoped action definitions."""

    def __init__(self) -> None:
        self._by_extension: dict[str, dict[str, ActionDefinition]] = defaultdict(dict)

    def register(self, extension_id: str, definition: ActionDefinition) -> DisposalHandle:
        """Register one action definition for one extension."""
        extension_name = _require_safe_name(
            extension_id,
            field_name="extension_id",
            max_bytes=MAX_EXTENSION_ID_BYTES,
            code="invalid_definition",
        )
        if not isinstance(definition, ActionDefinition):
            raise ActionError("invalid_definition", "definition must be an ActionDefinition")
        extension_actions = self._by_extension[extension_name]
        if definition.id in extension_actions:
            raise ActionError(
                "duplicate_action",
                f"duplicate action {definition.id!r} already registered for {extension_name!r}",
            )
        extension_actions[definition.id] = definition
        return DisposalHandle(lambda: self._remove(extension_name, definition.id))

    def get(self, extension_id: str, action_id: str) -> ActionDefinition | None:
        """Return one registered action definition, if present."""
        extension_name = _require_safe_name(
            extension_id,
            field_name="extension_id",
            max_bytes=MAX_EXTENSION_ID_BYTES,
            code="invalid_definition",
        )
        action_name = _require_slug(
            action_id,
            field_name="action_id",
            max_bytes=MAX_SAFE_SLUG_BYTES,
            code="invalid_definition",
        )
        return self._by_extension.get(extension_name, {}).get(action_name)

    def actions(self, extension_id: str) -> tuple[ActionDefinition, ...]:
        """Return deterministic registered actions for one extension."""
        extension_name = _require_safe_name(
            extension_id,
            field_name="extension_id",
            max_bytes=MAX_EXTENSION_ID_BYTES,
            code="invalid_definition",
        )
        actions = self._by_extension.get(extension_name, {})
        return tuple(actions[action_id] for action_id in sorted(actions))

    def dispose_extension(self, extension_id: str) -> None:
        """Dispose every action registered for one extension."""
        extension_name = _require_safe_name(
            extension_id,
            field_name="extension_id",
            max_bytes=MAX_EXTENSION_ID_BYTES,
            code="invalid_definition",
        )
        self._by_extension.pop(extension_name, None)

    def _remove(self, extension_id: str, action_id: str) -> None:
        actions = self._by_extension.get(extension_id)
        if actions is None:
            return
        actions.pop(action_id, None)
        if not actions:
            self._by_extension.pop(extension_id, None)


class PatchBuffer:
    """Bounded patch buffer that coalesces the latest patch for each path."""

    def __init__(self, *, max_entries: int = MAX_PATCH_BUFFER_ENTRIES) -> None:
        self._max_entries = _require_bounded_int(
            max_entries,
            field_name="max_entries",
            minimum=1,
            maximum=MAX_PATCH_BUFFER_ENTRIES,
            code="invalid_patch",
        )
        self._by_target: dict[tuple[str, str], PropertyPatch] = {}

    def __len__(self) -> int:
        return len(self._by_target)

    def add(self, patch: PropertyPatch) -> None:
        """Add one patch, replacing older entries for the same target."""
        if not isinstance(patch, PropertyPatch):
            raise ActionError("invalid_patch", "patch must be a PropertyPatch")
        key = (patch.view_id, patch.path)
        previous = self._by_target.get(key)
        if previous is not None:
            if patch.sequence <= previous.sequence:
                raise ActionError(
                    "stale_patch",
                    "patch sequence must be greater than the previous sequence "
                    "for the same view path",
                )
            self._by_target[key] = patch
            return
        if len(self._by_target) >= self._max_entries:
            raise ActionError(
                "patch_buffer_full",
                f"patch buffer exceeds {self._max_entries} unique entries",
            )
        self._by_target[key] = patch

    def extend(self, patches: Sequence[PropertyPatch]) -> None:
        """Add multiple patches in order."""
        for patch in patches:
            self.add(patch)

    def drain(self) -> tuple[PropertyPatch, ...]:
        """Return buffered patches in deterministic order and empty the buffer."""
        drained = tuple(
            sorted(
                self._by_target.values(),
                key=lambda patch: (patch.sequence, patch.view_id, patch.path),
            )
        )
        self._by_target.clear()
        return drained


@dataclass(slots=True)
class _ActiveRequest:
    cancellation: asyncio.Event
    task: asyncio.Task[ActionResult]


@dataclass(slots=True)
class _CompletedAction:
    payload_fingerprint: bytes
    result: ActionResult


@dataclass(slots=True)
class _InflightAction:
    payload_fingerprint: bytes
    future: asyncio.Future[ActionResult]


class ActionExecutor:
    """Execute registered actions with bounded concurrency and idempotency."""

    def __init__(
        self,
        registry: ActionRegistry,
        *,
        max_concurrency: int = 16,
        approval_callback: ApprovalCallback | None = None,
        completed_idempotency_capacity: int = MAX_IDEMPOTENCY_CACHE_ENTRIES,
    ) -> None:
        if not isinstance(registry, ActionRegistry):
            raise ActionError("invalid_definition", "registry must be an ActionRegistry")
        self._registry = registry
        self._max_concurrency = _require_bounded_int(
            max_concurrency,
            field_name="max_concurrency",
            minimum=1,
            maximum=MAX_EXECUTOR_CONCURRENCY,
            code="invalid_definition",
        )
        if approval_callback is not None and not callable(approval_callback):
            raise ActionError("invalid_definition", "approval_callback must be callable")
        self._approval_callback = approval_callback
        self._completed_capacity = _require_bounded_int(
            completed_idempotency_capacity,
            field_name="completed_idempotency_capacity",
            minimum=1,
            maximum=MAX_IDEMPOTENCY_CACHE_ENTRIES,
            code="invalid_definition",
        )
        self._global_semaphore = asyncio.Semaphore(self._max_concurrency)
        self._action_semaphores: dict[tuple[str, str], asyncio.Semaphore] = {}
        self._active_requests: dict[str, _ActiveRequest] = {}
        self._inflight: dict[InflightKey, _InflightAction] = {}
        self._completed: OrderedDict[InflightKey, _CompletedAction] = OrderedDict()

    @property
    def active_request_ids(self) -> tuple[str, ...]:
        """Return deterministic active request ids."""
        return tuple(sorted(self._active_requests))

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Execute one validated request against the registered action definition."""
        if not isinstance(request, ActionRequest):
            raise ActionError("invalid_request", "request must be an ActionRequest")
        definition = self._registry.get(request.extension_id, request.action_id)
        if definition is None:
            raise ActionError(
                "action_not_found",
                f"action {request.extension_id!r}/{request.action_id!r} is not registered",
            )
        if request.request_id in self._active_requests:
            raise ActionError(
                "duplicate_request",
                f"action request {request.request_id!r} is already active",
            )

        scope: InflightKey | None = None
        payload_fingerprint = _encode_canonical_json(request.payload)
        if definition.idempotent:
            if request.idempotency_key is None:
                raise ActionError(
                    "idempotency_required",
                    f"action {definition.id!r} requires an idempotency_key",
                )
            scope = (request.extension_id, request.action_id, request.idempotency_key)
            cached = self._completed.get(scope)
            if cached is not None:
                if cached.payload_fingerprint != payload_fingerprint:
                    raise ActionError(
                        "idempotency_conflict",
                        f"idempotency key {request.idempotency_key!r} was already used "
                        "with a different payload",
                    )
                self._completed.move_to_end(scope)
                return cached.result
            inflight = self._inflight.get(scope)
            if inflight is not None:
                if inflight.payload_fingerprint != payload_fingerprint:
                    raise ActionError(
                        "idempotency_conflict",
                        f"idempotency key {request.idempotency_key!r} is already in use "
                        "with a different payload",
                    )
                return await self._await_shared(request, inflight.future)

        context = ActionContext(request=request)
        shared_future: asyncio.Future[ActionResult] | None = None
        if scope is not None:
            shared_future = asyncio.get_running_loop().create_future()
            self._inflight[scope] = _InflightAction(
                payload_fingerprint=payload_fingerprint,
                future=shared_future,
            )
        task = asyncio.create_task(
            self._run_request(definition, context, scope=scope, shared_future=shared_future),
            name=f"tau-action:{request.extension_id}:{request.action_id}:{request.request_id}",
        )
        self._active_requests[request.request_id] = _ActiveRequest(
            cancellation=context.cancellation,
            task=task,
        )
        try:
            return await task
        finally:
            self._active_requests.pop(request.request_id, None)

    def cancel(self, request_id: str) -> bool:
        """Cancel one active request by id and return whether it was found."""
        request_name = _require_safe_name(
            request_id,
            field_name="request_id",
            max_bytes=MAX_REQUEST_ID_BYTES,
            code="invalid_request",
        )
        active = self._active_requests.get(request_name)
        if active is None:
            return False
        active.cancellation.set()
        active.task.cancel()
        return True

    async def _await_shared(
        self,
        request: ActionRequest,
        future: asyncio.Future[ActionResult],
    ) -> ActionResult:
        context = ActionContext(request=request)
        task = asyncio.create_task(
            self._await_shared_future(context, future),
            name=f"tau-action-wait:{request.extension_id}:{request.action_id}:{request.request_id}",
        )
        self._active_requests[request.request_id] = _ActiveRequest(
            cancellation=context.cancellation,
            task=task,
        )
        try:
            return await task
        finally:
            self._active_requests.pop(request.request_id, None)

    async def _await_shared_future(
        self,
        context: ActionContext,
        future: asyncio.Future[ActionResult],
    ) -> ActionResult:
        try:
            result = await future
        except asyncio.CancelledError as exc:
            context.cancellation.set()
            raise ActionError(
                "cancelled",
                f"action request {context.request.request_id!r} was cancelled",
            ) from exc
        context.raise_if_cancelled()
        return result

    async def _run_request(
        self,
        definition: ActionDefinition,
        context: ActionContext,
        *,
        scope: InflightKey | None,
        shared_future: asyncio.Future[ActionResult] | None,
    ) -> ActionResult:
        try:
            context.raise_if_cancelled()
            await self._require_approval(context.request, definition)
            context.raise_if_cancelled()
            action_semaphore = self._action_semaphore(context.request.extension_id, definition)
            async with self._global_semaphore, action_semaphore:
                context.raise_if_cancelled()
                result = await asyncio.wait_for(
                    self._call_handler(definition, context),
                    timeout=definition.timeout_seconds,
                )
            context.raise_if_cancelled()
        except ActionError as exc:
            if shared_future is not None and not shared_future.done():
                shared_future.set_exception(exc)
            raise
        except TimeoutError as exc:
            error = ActionError(
                "timeout",
                f"action {definition.id!r} timed out after {definition.timeout_seconds:g} seconds",
            )
            if shared_future is not None and not shared_future.done():
                shared_future.set_exception(error)
            raise error from exc
        except asyncio.CancelledError as exc:
            context.cancellation.set()
            error = ActionError(
                "cancelled",
                f"action request {context.request.request_id!r} was cancelled",
            )
            if shared_future is not None and not shared_future.done():
                shared_future.set_exception(error)
            raise error from exc
        except Exception as exc:  # noqa: BLE001 - extension isolation boundary
            error = ActionError(
                "internal",
                f"action {definition.id!r} failed: {exc}",
            )
            if shared_future is not None and not shared_future.done():
                shared_future.set_exception(error)
            raise error from exc
        else:
            if shared_future is not None and not shared_future.done():
                shared_future.set_result(result)
            if scope is not None:
                self._store_completed(scope, context.request.payload, result)
            return result
        finally:
            if scope is not None:
                current = self._inflight.get(scope)
                if current is not None and current.future is shared_future:
                    self._inflight.pop(scope, None)

    async def _require_approval(
        self,
        request: ActionRequest,
        definition: ActionDefinition,
    ) -> None:
        if not definition.requires_approval:
            return
        if self._approval_callback is None:
            raise ActionError(
                "approval_denied",
                f"action {definition.id!r} requires approval",
            )
        try:
            decision = self._approval_callback(request, definition)
            approved = await decision if inspect.isawaitable(decision) else decision
        except ActionError:
            raise
        except Exception as exc:  # noqa: BLE001 - approval isolation boundary
            raise ActionError(
                "internal", f"approval for action {definition.id!r} failed: {exc}"
            ) from exc
        if not isinstance(approved, bool):
            raise ActionError("internal", "approval_callback must return a bool")
        if not approved:
            raise ActionError(
                "approval_denied",
                f"action {definition.id!r} was denied approval",
            )

    async def _call_handler(
        self,
        definition: ActionDefinition,
        context: ActionContext,
    ) -> ActionResult:
        awaitable_result = definition.handler(context)
        if not inspect.isawaitable(awaitable_result):
            raise ActionError("internal", "handler must return an awaitable ActionResult")
        result = await cast(Awaitable[object], awaitable_result)
        if not isinstance(result, ActionResult):
            raise ActionError("invalid_result", "handler must return an ActionResult")
        return result

    def _action_semaphore(
        self,
        extension_id: str,
        definition: ActionDefinition,
    ) -> asyncio.Semaphore:
        key = (extension_id, definition.id)
        semaphore = self._action_semaphores.get(key)
        if semaphore is None:
            semaphore = asyncio.Semaphore(definition.concurrency)
            self._action_semaphores[key] = semaphore
        return semaphore

    def _store_completed(
        self,
        scope: InflightKey,
        payload: FrozenJSONObject,
        result: ActionResult,
    ) -> None:
        self._completed[scope] = _CompletedAction(
            payload_fingerprint=_encode_canonical_json(payload),
            result=result,
        )
        self._completed.move_to_end(scope)
        while len(self._completed) > self._completed_capacity:
            self._completed.popitem(last=False)


def _require_literal(
    value: object,
    *,
    field_name: str,
    allowed: tuple[str, ...],
    code: ActionErrorCode,
) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise ActionError(code, f"{field_name} must be one of: {', '.join(allowed)}")
    return value


def _require_bool(value: object, *, field_name: str, code: ActionErrorCode) -> bool:
    if not isinstance(value, bool):
        raise ActionError(code, f"{field_name} must be a boolean")
    return value


def _require_bounded_string(
    value: object,
    *,
    field_name: str,
    max_bytes: int,
    non_blank: bool = False,
    code: ActionErrorCode,
) -> str:
    if not isinstance(value, str):
        raise ActionError(code, f"{field_name} must be a string")
    if non_blank and not value.strip():
        raise ActionError(code, f"{field_name} must be non-blank")
    if len(value.encode("utf-8")) > max_bytes:
        raise ActionError(code, f"{field_name} exceeds {max_bytes} bytes")
    return value


def _require_safe_name(
    value: object,
    *,
    field_name: str,
    max_bytes: int,
    code: ActionErrorCode,
) -> str:
    text = _require_bounded_string(value, field_name=field_name, max_bytes=max_bytes, code=code)
    if _SAFE_NAME_RE.fullmatch(text) is None:
        raise ActionError(code, f"{field_name} must be a safe identifier")
    return text


def _require_slug(
    value: object,
    *,
    field_name: str,
    max_bytes: int,
    code: ActionErrorCode,
) -> str:
    text = _require_bounded_string(value, field_name=field_name, max_bytes=max_bytes, code=code)
    if _SAFE_SLUG_RE.fullmatch(text) is None:
        raise ActionError(code, f"{field_name} must be a lowercase slug")
    return text


def _require_pointer_path(value: object, *, field_name: str, code: ActionErrorCode) -> str:
    text = _require_bounded_string(
        value,
        field_name=field_name,
        max_bytes=MAX_PROPERTY_PATCH_PATH_BYTES,
        non_blank=True,
        code=code,
    )
    if _POINTER_RE.fullmatch(text) is None:
        raise ActionError(code, f"{field_name} must be a JSON pointer-like path")
    return text


def _require_nonnegative_int(value: object, *, field_name: str, code: ActionErrorCode) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ActionError(code, f"{field_name} must be a non-negative int")
    return value


def _require_bounded_int(
    value: object,
    *,
    field_name: str,
    minimum: int,
    maximum: int,
    code: ActionErrorCode,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ActionError(code, f"{field_name} must be an int between {minimum} and {maximum}")
    if value < minimum or value > maximum:
        raise ActionError(code, f"{field_name} must be an int between {minimum} and {maximum}")
    return value


def _require_bounded_number(
    value: object,
    *,
    field_name: str,
    minimum: float,
    maximum: float,
    code: ActionErrorCode,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ActionError(
            code, f"{field_name} must be a finite number between {minimum:g} and {maximum:g}"
        )
    number = float(value)
    if not math.isfinite(number) or number < minimum or number > maximum:
        raise ActionError(
            code, f"{field_name} must be a finite number between {minimum:g} and {maximum:g}"
        )
    return number


def _freeze_json_object(
    value: object,
    *,
    path: str,
    code: ActionErrorCode,
) -> FrozenJSONObject:
    if not isinstance(value, Mapping):
        raise ActionError(code, f"{path} must be a JSON object")
    frozen: dict[str, FrozenJSONValue] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ActionError(code, f"{path} contains a non-string key")
        frozen[key] = _freeze_json_value(item, path=f"{path}.{key}", code=code)
    return cast(FrozenJSONObject, MappingProxyType(frozen))


def _freeze_json_value(
    value: object,
    *,
    path: str,
    code: ActionErrorCode,
) -> FrozenJSONValue:
    if value is None or isinstance(value, (str, bool)):
        return cast(FrozenJSONValue, value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ActionError(code, f"{path} contains a non-finite number")
        return value
    if isinstance(value, Mapping):
        return _freeze_json_object(value, path=path, code=code)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray, Mapping)):
        return tuple(_freeze_json_value(item, path=f"{path}[]", code=code) for item in value)
    raise ActionError(code, f"{path} contains a non-JSON value")


def _plain_json_value(value: FrozenJSONValue | JSONValue | JSONObject) -> JSONValue:
    if value is None or isinstance(value, (str, bool, int)):
        return cast(JSONValue, value)
    if isinstance(value, float):
        return value
    if isinstance(value, Mapping):
        return {key: _plain_json_value(value[key]) for key in sorted(value)}
    return [_plain_json_value(item) for item in value]


def _encode_canonical_json(value: FrozenJSONValue | JSONValue | JSONObject) -> bytes:
    return json.dumps(
        _plain_json_value(value),
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
        sort_keys=True,
    ).encode("utf-8")


def _validate_json_size(
    value: FrozenJSONValue | JSONValue | JSONObject,
    *,
    path: str,
    limit: int,
    code: ActionErrorCode,
) -> None:
    encoded = _encode_canonical_json(value)
    if len(encoded) > limit:
        raise ActionError(code, f"{path} JSON exceeds {limit} bytes")


def _is_async_callable(value: object) -> bool:
    if not callable(value):
        return False
    call_method = getattr(value, "__call__", None)  # noqa: B004 -- inspect bound call
    return inspect.iscoroutinefunction(value) or (
        callable(call_method) and inspect.iscoroutinefunction(call_method)
    )


__all__ = [
    "ActionContext",
    "ActionDefinition",
    "ActionError",
    "ActionErrorCode",
    "ActionExecutor",
    "ActionHandler",
    "ActionRegistry",
    "ActionRequest",
    "ActionResult",
    "ApprovalCallback",
    "Invalidation",
    "MAX_ACTION_RESULT_BYTES",
    "MAX_ACTION_RESULT_INVALIDATIONS",
    "MAX_ACTION_RESULT_PATCHES",
    "MAX_ACTION_TIMEOUT_SECONDS",
    "MAX_EXECUTOR_CONCURRENCY",
    "MAX_IDEMPOTENCY_CACHE_ENTRIES",
    "MAX_IDEMPOTENCY_KEY_BYTES",
    "MAX_PATCH_BUFFER_ENTRIES",
    "MAX_PROPERTY_PATCH_VALUE_BYTES",
    "MIN_ACTION_TIMEOUT_SECONDS",
    "PatchBuffer",
    "PropertyPatch",
]
