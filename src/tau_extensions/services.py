"""Portable public runtime services for Tau extensions.

This module intentionally depends only on Tau's portable extension contracts and
standard-library primitives. It does not import Tau Web, aiohttp, SQLite, or
Tau Coding runtime modules.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import re
from collections import defaultdict
from collections.abc import Awaitable, Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Literal, Protocol, TypeVar, cast, runtime_checkable

from tau_extensions.manifest import Permission
from tau_extensions.runtime import DisposalHandle, RegistryError, RuntimeDiagnostic
from tau_extensions.types import JSONObject, JSONValue

MAX_STORAGE_VALUE_BYTES = 64 * 1024
MAX_ASSET_BYTES = 2 * 1024 * 1024
MAX_EXTENSION_ASSET_BYTES = 16 * 1024 * 1024
GLOBAL_SCOPE_ID = "global"

type StorageScope = Literal["global", "workspace", "session"]
type CommandHandler = Callable[..., object | Awaitable[object]]
type ToolHandler = Callable[[JSONObject], object | Awaitable[object]]
type RouteHandler = Callable[["RouteRequest"], object | Awaitable[object]]
type EventListener = Callable[..., object | Awaitable[object]]

_T = TypeVar("_T")
_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")
_HEADER_NAME_RE = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
_MIME_RE = re.compile(r"^[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+$")
_ALLOWED_MIME_TOP_LEVELS = frozenset(
    {"application", "audio", "font", "image", "model", "text", "video"}
)
_ALLOWED_ROUTE_METHODS = frozenset({"DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"})
_ALLOWED_PERMISSIONS = frozenset(
    {
        "storage",
        "background_tasks",
        "assets",
        "commands",
        "tools",
        "routes",
        "events",
        "views",
        "actions",
    }
)


class PermissionDeniedError(PermissionError):
    """Raised when an extension uses a service without the required permission."""


class RevisionConflictError(ValueError):
    """Raised when an optimistic storage update uses a stale revision."""

    def __init__(self, identity: str, *, expected: int | None, actual: int | None) -> None:
        self.identity = identity
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"revision conflict for {identity!r}: expected {expected!r}, actual {actual!r}"
        )


@dataclass(frozen=True, slots=True)
class StoredValue:
    """One revisioned JSON value stored for an extension scope key."""

    value: JSONValue
    revision: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_json_value(
                self.value,
                field_name="value",
                max_bytes=MAX_STORAGE_VALUE_BYTES,
            ),
        )
        object.__setattr__(
            self,
            "revision",
            _validate_revision(self.revision, field_name="revision"),
        )


@dataclass(frozen=True, slots=True)
class RouteRequest:
    """One validated portable request passed to an extension route handler."""

    method: str
    path: str
    query: Mapping[str, str] = field(default_factory=dict)
    headers: Mapping[str, str] = field(default_factory=dict)
    body: JSONValue | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "method", _validate_route_method(self.method))
        object.__setattr__(self, "path", _validate_route_path(self.path))
        object.__setattr__(
            self,
            "query",
            _normalize_string_mapping(self.query, field_name="query"),
        )
        object.__setattr__(
            self,
            "headers",
            _normalize_header_mapping(self.headers, field_name="headers"),
        )
        if self.body is not None:
            object.__setattr__(
                self,
                "body",
                _normalize_json_value(self.body, field_name="body"),
            )


@dataclass(frozen=True, slots=True)
class RouteResponse:
    """One validated portable response returned by an extension route handler."""

    status: int
    body: JSONValue | bytes | str | None = None
    headers: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", _validate_response_status(self.status))
        object.__setattr__(
            self,
            "headers",
            _normalize_header_mapping(self.headers, field_name="headers"),
        )
        if isinstance(self.body, bytes | bytearray | memoryview):
            object.__setattr__(self, "body", bytes(self.body))
        elif isinstance(self.body, str) or self.body is None:
            return
        else:
            object.__setattr__(
                self,
                "body",
                _normalize_json_value(cast(JSONValue, self.body), field_name="body"),
            )


@runtime_checkable
class StorageBackend(Protocol):
    """Portable async backend for extension storage state."""

    async def get(
        self,
        extension_id: str,
        *,
        scope: StorageScope,
        scope_id: str,
        key: str,
    ) -> StoredValue | None:
        """Return the stored value for one key or ``None`` when absent."""

    async def list(
        self,
        extension_id: str,
        *,
        scope: StorageScope,
        scope_id: str,
    ) -> Mapping[str, StoredValue]:
        """Return every stored value for one extension scope."""

    async def save(
        self,
        extension_id: str,
        *,
        scope: StorageScope,
        scope_id: str,
        key: str,
        value: JSONValue,
        expected_revision: int | None,
    ) -> StoredValue:
        """Create or replace one stored value using optimistic revisions."""

    async def delete(
        self,
        extension_id: str,
        *,
        scope: StorageScope,
        scope_id: str,
        key: str,
        expected_revision: int,
    ) -> StoredValue | None:
        """Delete one stored value using an exact expected revision."""


class _ServiceContext:
    __slots__ = ("diagnostics", "extension_id", "permissions")

    def __init__(self, extension_id: str, permissions: frozenset[Permission]) -> None:
        self.extension_id = extension_id
        self.permissions = permissions
        self.diagnostics: list[RuntimeDiagnostic] = []

    def require_permission(self, permission: Permission) -> None:
        if permission not in self.permissions:
            raise PermissionDeniedError(
                f"extension {self.extension_id!r} lacks permission {permission!r}"
            )

    def record_exception(self, phase: str, exc: Exception) -> None:
        self.diagnostics.append(
            RuntimeDiagnostic(
                extension_id=self.extension_id,
                phase=phase,
                message=_format_exception(exc),
                severity="error",
            )
        )


class StorageService:
    """Factory for extension-owned storage scopes."""

    def __init__(self, context: _ServiceContext, backend: StorageBackend) -> None:
        self._context = context
        self._backend = backend

    def global_(self) -> ScopedStorage:
        """Return the extension-global storage scope."""
        return self.scope("global")

    def workspace(self, workspace_id: str) -> ScopedStorage:
        """Return one workspace storage scope."""
        return self.scope("workspace", workspace_id)

    def session(self, session_id: str) -> ScopedStorage:
        """Return one session storage scope."""
        return self.scope("session", session_id)

    def scope(self, scope: StorageScope, scope_id: str | None = None) -> ScopedStorage:
        """Return one validated scoped storage wrapper."""
        selected_scope = _validate_scope(scope)
        if selected_scope == "global":
            if scope_id not in (None, GLOBAL_SCOPE_ID):
                raise RegistryError("global scope does not accept a custom scope_id")
            selected_scope_id = GLOBAL_SCOPE_ID
        else:
            if scope_id is None:
                raise RegistryError(f"{selected_scope} scope requires a scope_id")
            selected_scope_id = _validate_storage_key(scope_id, field_name=f"{selected_scope}_id")
        return ScopedStorage(self._context, self._backend, selected_scope, selected_scope_id)


class ScopedStorage:
    """Storage helper bound to one extension scope identity."""

    __slots__ = ("_backend", "_context", "scope", "scope_id")

    def __init__(
        self,
        context: _ServiceContext,
        backend: StorageBackend,
        scope: StorageScope,
        scope_id: str,
    ) -> None:
        self._context = context
        self._backend = backend
        self.scope = scope
        self.scope_id = scope_id

    async def get(self, key: str) -> StoredValue | None:
        """Return one stored value for this scope."""
        self._context.require_permission("storage")
        record = await self._backend.get(
            self._context.extension_id,
            scope=self.scope,
            scope_id=self.scope_id,
            key=_validate_storage_key(key),
        )
        return _copy_stored_value(record) if record is not None else None

    async def list(self) -> dict[str, StoredValue]:
        """Return every stored value for this scope ordered by key."""
        self._context.require_permission("storage")
        records = await self._backend.list(
            self._context.extension_id,
            scope=self.scope,
            scope_id=self.scope_id,
        )
        normalized: dict[str, StoredValue] = {}
        for key, value in sorted(records.items()):
            normalized[_validate_storage_key(key)] = _copy_stored_value(value)
        return normalized

    async def save(
        self,
        key: str,
        value: JSONValue,
        *,
        expected_revision: int | None = None,
    ) -> StoredValue:
        """Create or replace one stored value using optimistic revisions."""
        self._context.require_permission("storage")
        record = await self._backend.save(
            self._context.extension_id,
            scope=self.scope,
            scope_id=self.scope_id,
            key=_validate_storage_key(key),
            value=_normalize_json_value(
                value,
                field_name="value",
                max_bytes=MAX_STORAGE_VALUE_BYTES,
            ),
            expected_revision=_validate_expected_revision(expected_revision),
        )
        return _copy_stored_value(record)

    async def delete(self, key: str, *, expected_revision: int) -> StoredValue | None:
        """Delete one stored value using an exact expected revision."""
        self._context.require_permission("storage")
        record = await self._backend.delete(
            self._context.extension_id,
            scope=self.scope,
            scope_id=self.scope_id,
            key=_validate_storage_key(key),
            expected_revision=_validate_revision(expected_revision, field_name="expected_revision"),
        )
        return _copy_stored_value(record) if record is not None else None


class OwnedTaskService:
    """Track extension-owned background tasks and clean them up deterministically."""

    def __init__(self, context: _ServiceContext) -> None:
        self._context = context
        self._tasks: set[asyncio.Task[object]] = set()

    @property
    def task_count(self) -> int:
        """Return the number of currently tracked tasks."""
        return len(self._tasks)

    def spawn(self, coroutine: Awaitable[_T], name: str) -> asyncio.Task[_T]:
        """Spawn one tracked background task for this extension."""
        try:
            self._context.require_permission("background_tasks")
            task_name = _validate_safe_name(name, field_name="name")
            if not inspect.isawaitable(coroutine):
                raise RegistryError("coroutine must be awaitable")
        except Exception:
            _close_awaitable(coroutine)
            raise

        async def runner() -> _T:
            try:
                return await coroutine
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self._context.record_exception(f"task:{task_name}", exc)
                raise

        task = asyncio.create_task(
            runner(),
            name=f"tau-extension:{self._context.extension_id}:{task_name}",
        )
        tracked_task = cast(asyncio.Task[object], task)
        self._tasks.add(tracked_task)
        tracked_task.add_done_callback(self._on_task_done)
        return task

    async def cancel_all(self) -> None:
        """Cancel every tracked task and await their cleanup."""
        pending = tuple(self._tasks)
        if not pending:
            return
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

    async def dispose(self) -> None:
        """Cancel every tracked task and await their cleanup."""
        await self.cancel_all()

    def _on_task_done(self, task: asyncio.Task[object]) -> None:
        self._tasks.discard(task)
        try:
            task.exception()
        except asyncio.CancelledError:
            return


@dataclass(frozen=True, slots=True)
class AssetRecord:
    """Immutable in-memory asset registered by one extension."""

    extension_id: str
    path: str
    content: bytes
    mime_type: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "extension_id", _validate_extension_id(self.extension_id))
        object.__setattr__(self, "path", _validate_asset_path(self.path))
        object.__setattr__(self, "content", bytes(self.content))
        object.__setattr__(self, "mime_type", _validate_mime_type(self.mime_type))
        if len(self.content) > MAX_ASSET_BYTES:
            raise RegistryError(f"asset content must be at most {MAX_ASSET_BYTES} bytes")

    @property
    def size(self) -> int:
        """Return the asset size in bytes."""
        return len(self.content)


class AssetRegistry:
    """In-memory immutable asset registry owned by one extension."""

    def __init__(self, context: _ServiceContext) -> None:
        self._context = context
        self._assets: dict[str, AssetRecord] = {}
        self._total_bytes = 0

    @property
    def total_bytes(self) -> int:
        """Return the total bytes registered by this extension."""
        return self._total_bytes

    def register(
        self,
        path: str,
        content: bytes | bytearray | memoryview,
        *,
        mime_type: str,
    ) -> DisposalHandle:
        """Register one immutable asset and return its disposal handle."""
        self._context.require_permission("assets")
        normalized_path = _validate_asset_path(path)
        if normalized_path in self._assets:
            raise RegistryError(f"duplicate asset path {normalized_path!r}")
        asset = AssetRecord(
            extension_id=self._context.extension_id,
            path=normalized_path,
            content=bytes(content),
            mime_type=mime_type,
        )
        if self._total_bytes + asset.size > MAX_EXTENSION_ASSET_BYTES:
            raise RegistryError(
                f"extension assets must total at most {MAX_EXTENSION_ASSET_BYTES} bytes"
            )
        self._assets[normalized_path] = asset
        self._total_bytes += asset.size
        return DisposalHandle(lambda: self._remove(normalized_path))

    def lookup(self, path: str) -> AssetRecord | None:
        """Return one registered asset within this extension namespace."""
        return self._assets.get(_validate_asset_path(path))

    def items(self) -> tuple[AssetRecord, ...]:
        """Return registered assets ordered by path."""
        return tuple(self._assets[path] for path in sorted(self._assets))

    def dispose(self) -> None:
        """Remove every registered asset owned by this extension."""
        self._assets.clear()
        self._total_bytes = 0

    def _remove(self, path: str) -> None:
        asset = self._assets.pop(path, None)
        if asset is None:
            return
        self._total_bytes -= asset.size


@dataclass(frozen=True, slots=True)
class CommandSpec:
    """Portable command contribution declared by one extension."""

    name: str
    title: str
    handler: CommandHandler

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _validate_safe_name(self.name, field_name="name"))
        object.__setattr__(self, "title", _validate_text(self.title, field_name="title"))
        if not callable(self.handler):
            raise RegistryError("command handler must be callable")


class CommandRegistry:
    """Command contributions owned by one extension."""

    def __init__(self, context: _ServiceContext) -> None:
        self._context = context
        self._commands: dict[str, CommandSpec] = {}

    def register(self, spec: CommandSpec) -> DisposalHandle:
        """Register one command contribution."""
        self._context.require_permission("commands")
        if not isinstance(spec, CommandSpec):
            raise RegistryError("spec must be a CommandSpec")
        if spec.name in self._commands:
            raise RegistryError(f"duplicate command name {spec.name!r}")
        self._commands[spec.name] = spec

        def dispose() -> None:
            self._commands.pop(spec.name, None)

        return DisposalHandle(dispose)

    def get(self, name: str) -> CommandSpec | None:
        """Return one registered command by name."""
        return self._commands.get(_validate_safe_name(name, field_name="name"))

    def items(self) -> tuple[CommandSpec, ...]:
        """Return registered commands in registration order."""
        return tuple(self._commands.values())

    def dispose(self) -> None:
        """Remove every registered command."""
        self._commands.clear()


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """Portable tool contribution declared by one extension."""

    name: str
    description: str
    input_schema: JSONObject
    handler: ToolHandler

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _validate_safe_name(self.name, field_name="name"))
        object.__setattr__(
            self,
            "description",
            _validate_text(self.description, field_name="description"),
        )
        object.__setattr__(
            self,
            "input_schema",
            _normalize_json_object(self.input_schema, field_name="input_schema"),
        )
        if not callable(self.handler):
            raise RegistryError("tool handler must be callable")


class ToolRegistry:
    """Tool contributions owned by one extension."""

    def __init__(self, context: _ServiceContext) -> None:
        self._context = context
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> DisposalHandle:
        """Register one tool contribution."""
        self._context.require_permission("tools")
        if not isinstance(spec, ToolSpec):
            raise RegistryError("spec must be a ToolSpec")
        if spec.name in self._tools:
            raise RegistryError(f"duplicate tool name {spec.name!r}")
        self._tools[spec.name] = spec

        def dispose() -> None:
            self._tools.pop(spec.name, None)

        return DisposalHandle(dispose)

    def get(self, name: str) -> ToolSpec | None:
        """Return one registered tool by name."""
        return self._tools.get(_validate_safe_name(name, field_name="name"))

    def items(self) -> tuple[ToolSpec, ...]:
        """Return registered tools in registration order."""
        return tuple(self._tools.values())

    def dispose(self) -> None:
        """Remove every registered tool."""
        self._tools.clear()


@dataclass(frozen=True, slots=True)
class RouteSpec:
    """Portable route contribution declared by one extension."""

    method: str
    path: str
    handler: RouteHandler

    def __post_init__(self) -> None:
        object.__setattr__(self, "method", _validate_route_method(self.method))
        object.__setattr__(self, "path", _validate_route_path(self.path))
        if not callable(self.handler):
            raise RegistryError("route handler must be callable")


class RouteRegistry:
    """Route contributions owned by one extension."""

    def __init__(self, context: _ServiceContext) -> None:
        self._context = context
        self._routes: dict[tuple[str, str], RouteSpec] = {}

    def register(self, spec: RouteSpec) -> DisposalHandle:
        """Register one route contribution."""
        self._context.require_permission("routes")
        if not isinstance(spec, RouteSpec):
            raise RegistryError("spec must be a RouteSpec")
        key = (spec.method, spec.path)
        if key in self._routes:
            raise RegistryError(f"duplicate route {spec.method} {spec.path}")
        self._routes[key] = spec

        def dispose() -> None:
            self._routes.pop(key, None)

        return DisposalHandle(dispose)

    def get(self, method: str, path: str) -> RouteSpec | None:
        """Return one registered route by method and path."""
        return self._routes.get((_validate_route_method(method), _validate_route_path(path)))

    def items(self) -> tuple[RouteSpec, ...]:
        """Return registered routes in registration order."""
        return tuple(self._routes.values())

    def dispose(self) -> None:
        """Remove every registered route."""
        self._routes.clear()


@dataclass(frozen=True, slots=True)
class _EventSubscription:
    event: str
    listener: EventListener
    registration_index: int


class EventBus:
    """Deterministic extension-local async event bus."""

    def __init__(self, context: _ServiceContext) -> None:
        self._context = context
        self._subscriptions_by_event: dict[str, dict[int, _EventSubscription]] = defaultdict(dict)
        self._subscriptions_by_index: dict[int, _EventSubscription] = {}
        self._next_registration_index = 0

    def subscribe(self, event: str, listener: EventListener) -> DisposalHandle:
        """Subscribe one sync or async listener and return its disposal handle."""
        self._context.require_permission("events")
        event_name = _validate_safe_name(event, field_name="event")
        if not callable(listener):
            raise RegistryError("listener must be callable")
        registration_index = self._next_registration_index
        self._next_registration_index += 1
        subscription = _EventSubscription(
            event=event_name,
            listener=listener,
            registration_index=registration_index,
        )
        self._subscriptions_by_event[event_name][registration_index] = subscription
        self._subscriptions_by_index[registration_index] = subscription
        return DisposalHandle(lambda: self._unsubscribe(registration_index))

    async def publish(self, event: str, *args: object, **kwargs: object) -> None:
        """Publish one event to subscribed listeners in registration order."""
        self._context.require_permission("events")
        event_name = _validate_safe_name(event, field_name="event")
        subscriptions = self._subscriptions_by_event.get(event_name)
        if not subscriptions:
            return
        ordered = tuple(
            sorted(subscriptions.values(), key=lambda subscription: subscription.registration_index)
        )
        for subscription in ordered:
            try:
                outcome = subscription.listener(*args, **kwargs)
                if inspect.isawaitable(outcome):
                    await cast(Awaitable[object], outcome)
            except Exception as exc:
                self._context.record_exception(f"event:{event_name}", exc)

    def count(self, event: str | None = None) -> int:
        """Return the number of registered listeners."""
        if event is None:
            return len(self._subscriptions_by_index)
        event_name = _validate_safe_name(event, field_name="event")
        return len(self._subscriptions_by_event.get(event_name, ()))

    def dispose(self) -> None:
        """Remove every registered event listener."""
        self._subscriptions_by_event.clear()
        self._subscriptions_by_index.clear()

    def _unsubscribe(self, registration_index: int) -> None:
        subscription = self._subscriptions_by_index.pop(registration_index, None)
        if subscription is None:
            return
        event_subscriptions = self._subscriptions_by_event.get(subscription.event)
        if event_subscriptions is None:
            return
        event_subscriptions.pop(registration_index, None)
        if not event_subscriptions:
            self._subscriptions_by_event.pop(subscription.event, None)


class ExtensionServices:
    """Portable public runtime services owned by one activated extension."""

    def __init__(
        self,
        extension_id: str,
        permissions: Iterable[Permission | str],
        storage_backend: StorageBackend,
    ) -> None:
        validated_permissions = _validate_permissions(permissions)
        self._context = _ServiceContext(_validate_extension_id(extension_id), validated_permissions)
        self.storage = StorageService(self._context, storage_backend)
        self.tasks = OwnedTaskService(self._context)
        self.assets = AssetRegistry(self._context)
        self.commands = CommandRegistry(self._context)
        self.tools = ToolRegistry(self._context)
        self.routes = RouteRegistry(self._context)
        self.events = EventBus(self._context)
        self._dispose_lock = asyncio.Lock()
        self._disposed = False

    @property
    def extension_id(self) -> str:
        """Return the owning extension id."""
        return self._context.extension_id

    @property
    def permissions(self) -> frozenset[Permission]:
        """Return the extension's granted permission set."""
        return self._context.permissions

    @property
    def diagnostics(self) -> tuple[RuntimeDiagnostic, ...]:
        """Return collected non-fatal runtime diagnostics."""
        return tuple(self._context.diagnostics)

    @property
    def disposed(self) -> bool:
        """Return whether this service bundle has already been disposed."""
        return self._disposed

    async def dispose(self) -> None:
        """Dispose owned listeners, contributions, assets, and background tasks."""
        async with self._dispose_lock:
            if self._disposed:
                return
            await self.tasks.dispose()
            self.events.dispose()
            self.routes.dispose()
            self.tools.dispose()
            self.commands.dispose()
            self.assets.dispose()
            self._disposed = True


def _validate_permissions(permissions: Iterable[Permission | str]) -> frozenset[Permission]:
    selected: set[Permission] = set()
    for permission in permissions:
        if not isinstance(permission, str):
            raise RegistryError("permission values must be strings")
        if permission not in _ALLOWED_PERMISSIONS:
            raise RegistryError(f"unknown permission value {permission!r}")
        selected.add(cast(Permission, permission))
    return frozenset(selected)


def _copy_stored_value(value: StoredValue) -> StoredValue:
    return StoredValue(
        value=_normalize_json_value(value.value, field_name="value"),
        revision=value.revision,
    )


def _validate_extension_id(extension_id: str) -> str:
    return _validate_safe_name(extension_id, field_name="extension_id")


def _validate_safe_name(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise RegistryError(f"{field_name} must be a string")
    if not _SAFE_NAME_RE.fullmatch(value):
        raise RegistryError(f"{field_name} must match {_SAFE_NAME_RE.pattern!r}")
    return value


def _validate_storage_key(value: str, *, field_name: str = "key") -> str:
    return _validate_safe_name(value, field_name=field_name)


def _validate_scope(scope: StorageScope) -> StorageScope:
    if scope not in ("global", "workspace", "session"):
        raise RegistryError("scope must be one of 'global', 'workspace', or 'session'")
    return scope


def _validate_expected_revision(expected_revision: int | None) -> int | None:
    if expected_revision is None:
        return None
    if expected_revision == 0:
        return 0
    return _validate_revision(expected_revision, field_name="expected_revision")


def _validate_revision(value: int, *, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise RegistryError(f"{field_name} must be an int")
    if value < 1:
        raise RegistryError(f"{field_name} must be at least 1")
    return value


def _normalize_json_value(
    value: JSONValue,
    *,
    field_name: str,
    max_bytes: int | None = None,
) -> JSONValue:
    payload = _dump_json_bytes(value, field_name=field_name, max_bytes=max_bytes)
    decoded = json.loads(payload)
    return cast(JSONValue, decoded)


def _normalize_json_object(value: JSONObject, *, field_name: str) -> JSONObject:
    if not isinstance(value, Mapping):
        raise RegistryError(f"{field_name} must be a JSON object")
    payload = _dump_json_bytes(cast(JSONValue, dict(value)), field_name=field_name)
    decoded = json.loads(payload)
    if not isinstance(decoded, dict):
        raise RegistryError(f"{field_name} must be a JSON object")
    if not all(isinstance(key, str) for key in decoded):
        raise RegistryError(f"{field_name} must use string keys")
    return cast(JSONObject, decoded)


def _dump_json_bytes(
    value: JSONValue,
    *,
    field_name: str,
    max_bytes: int | None = None,
) -> bytes:
    try:
        encoded = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RegistryError(f"{field_name} must be finite JSON") from exc
    if max_bytes is not None and len(encoded) > max_bytes:
        raise RegistryError(f"{field_name} must be at most {max_bytes} bytes")
    return encoded


def _validate_text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise RegistryError(f"{field_name} must be a string")
    if not value.strip():
        raise RegistryError(f"{field_name} must not be blank")
    return value


def _normalize_string_mapping(
    value: Mapping[str, str],
    *,
    field_name: str,
) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise RegistryError(f"{field_name} must be a mapping of strings")
    normalized: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise RegistryError(f"{field_name} keys must be strings")
        if not isinstance(item, str):
            raise RegistryError(f"{field_name} values must be strings")
        if any(character in key for character in ("\r", "\n", "\x00")):
            raise RegistryError(f"{field_name} keys must not contain CR, LF, or NUL")
        if any(character in item for character in ("\r", "\n", "\x00")):
            raise RegistryError(f"{field_name} values must not contain CR, LF, or NUL")
        normalized[key] = item
    return normalized


def _normalize_header_mapping(
    value: Mapping[str, str],
    *,
    field_name: str,
) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise RegistryError(f"{field_name} must be a mapping of strings")
    normalized: dict[str, str] = {}
    for key, item in value.items():
        normalized_key = _validate_header_name(key, field_name=f"{field_name} keys")
        normalized[normalized_key] = _validate_header_value(
            item,
            field_name=f"{field_name}[{normalized_key!r}]",
        )
    return normalized


def _validate_header_name(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise RegistryError(f"{field_name} must be strings")
    if "\r" in value or "\n" in value or "\x00" in value:
        raise RegistryError(f"{field_name} must not contain CR, LF, or NUL")
    if not value or _HEADER_NAME_RE.fullmatch(value) is None:
        raise RegistryError(f"{field_name} must be valid HTTP header names")
    return value


def _validate_header_value(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise RegistryError(f"{field_name} must be a string")
    if "\r" in value or "\n" in value or "\x00" in value:
        raise RegistryError(f"{field_name} must not contain CR, LF, or NUL")
    return value


def _validate_asset_path(path: str) -> str:
    if not isinstance(path, str):
        raise RegistryError("path must be a string")
    if not path or path.startswith("/") or "\\" in path:
        raise RegistryError("path must be a safe relative path")
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise RegistryError("path must be a safe relative path")
    if any(any(character.isspace() for character in part) for part in parts):
        raise RegistryError("path must be a safe relative path")
    return path


def _validate_mime_type(mime_type: str) -> str:
    if not isinstance(mime_type, str):
        raise RegistryError("mime_type must be a string")
    normalized = mime_type.strip().lower()
    if not _MIME_RE.fullmatch(normalized):
        raise RegistryError("mime_type must be a valid type/subtype string")
    top_level = normalized.split("/", 1)[0]
    if top_level not in _ALLOWED_MIME_TOP_LEVELS:
        raise RegistryError("mime_type top-level type is not allowed")
    return normalized


def _validate_route_method(method: str) -> str:
    if not isinstance(method, str):
        raise RegistryError("method must be a string")
    normalized = method.upper()
    if normalized not in _ALLOWED_ROUTE_METHODS:
        raise RegistryError("method must be a supported HTTP verb")
    return normalized


def _validate_response_status(status: int) -> int:
    if not isinstance(status, int) or isinstance(status, bool):
        raise RegistryError("status must be an int")
    if not 200 <= status <= 599:
        raise RegistryError("status must be between 200 and 599")
    return status


def _validate_route_path(path: str) -> str:
    if not isinstance(path, str):
        raise RegistryError("path must be a string")
    if not path.startswith("/"):
        raise RegistryError("path must start with '/'")
    if any(marker in path for marker in ("{", "}", "*", "?", "#", "\\")):
        raise RegistryError("path must not contain parameters or wildcards")
    if path != "/":
        parts = path.split("/")[1:]
        if any(part in ("", ".", "..") for part in parts):
            raise RegistryError("path must not contain empty or traversal segments")
        if any(any(character.isspace() for character in part) for part in parts):
            raise RegistryError("path must not contain whitespace")
    return path


def _format_exception(exc: Exception) -> str:
    detail = str(exc)
    if detail:
        return f"{exc.__class__.__name__}: {detail}"
    return exc.__class__.__name__


def _close_awaitable(value: Awaitable[object]) -> None:
    if inspect.iscoroutine(value):
        value.close()


__all__ = [
    "AssetRecord",
    "AssetRegistry",
    "CommandHandler",
    "CommandRegistry",
    "CommandSpec",
    "EventBus",
    "EventListener",
    "ExtensionServices",
    "GLOBAL_SCOPE_ID",
    "MAX_ASSET_BYTES",
    "MAX_EXTENSION_ASSET_BYTES",
    "MAX_STORAGE_VALUE_BYTES",
    "OwnedTaskService",
    "PermissionDeniedError",
    "RevisionConflictError",
    "RouteHandler",
    "RouteRegistry",
    "RouteRequest",
    "RouteResponse",
    "RouteSpec",
    "ScopedStorage",
    "StorageBackend",
    "StorageScope",
    "StorageService",
    "StoredValue",
    "ToolHandler",
    "ToolRegistry",
    "ToolSpec",
]
