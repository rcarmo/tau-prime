"""SQLite-backed storage and in-memory registries for Tau web extensions."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import cast

from tau_agent.types import JSONValue
from tau_extensions import (
    AnnotationProviderSpec,
    AssetRecord,
    EditorAnnotation,
    ExtensionServices,
    ExtensionSource,
    FileRenderContext,
    FileRendererSpec,
    RegistryError,
    RevisionConflictError,
    RouteSpec,
    StorageBackend,
    StorageScope,
    StoredValue,
    TrustedFrontendModuleSpec,
    WidgetReference,
    WidgetSpec,
    validate_annotations,
)
from tau_extensions.web import StandardView
from tau_web.sqlite.repositories import (
    ExtensionStateRecord,
    ExtensionStateRepository,
    RecordNotFoundError,
)
from tau_web.sqlite.repositories import (
    RevisionConflictError as RepositoryRevisionConflictError,
)


class SqliteExtensionStorageBackend(StorageBackend):
    """Adapt the durable extension-state repository to portable extension storage."""

    def __init__(self, repository: ExtensionStateRepository) -> None:
        self._repository = repository

    @property
    def repository(self) -> ExtensionStateRepository:
        return self._repository

    async def get(
        self,
        extension_id: str,
        *,
        scope: StorageScope,
        scope_id: str,
        key: str,
    ) -> StoredValue | None:
        record = await self._repository.get(extension_id, scope, scope_id, key)
        return _stored_value_from_record(record) if record is not None else None

    async def list(
        self,
        extension_id: str,
        *,
        scope: StorageScope,
        scope_id: str,
    ) -> Mapping[str, StoredValue]:
        records = await self._repository.list_scope(scope, scope_id, extension_id=extension_id)
        return {record.key: _stored_value_from_record(record) for record in records}

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
        try:
            record = await self._repository.save(
                extension_id,
                scope=scope,
                scope_id=scope_id,
                key=key,
                value=value,
                expected_revision=expected_revision,
            )
        except RepositoryRevisionConflictError as exc:
            raise _portable_revision_conflict(exc) from exc
        return _stored_value_from_record(record)

    async def delete(
        self,
        extension_id: str,
        *,
        scope: StorageScope,
        scope_id: str,
        key: str,
        expected_revision: int,
    ) -> StoredValue | None:
        try:
            record = await self._repository.delete(
                extension_id,
                scope=scope,
                scope_id=scope_id,
                key=key,
                expected_revision=expected_revision,
            )
        except RecordNotFoundError:
            return None
        except RepositoryRevisionConflictError as exc:
            raise _portable_revision_conflict(exc) from exc
        return _stored_value_from_record(record)


_EXTENDED_UI_TIMEOUT_SECONDS = 5.0


@dataclass(frozen=True, slots=True)
class ResolvedFileRenderer:
    extension_id: str
    renderer_id: str
    output: StandardView | WidgetReference


@dataclass(frozen=True, slots=True)
class ResolvedAnnotation:
    extension_id: str
    provider_id: str
    annotation: EditorAnnotation


@dataclass(frozen=True, slots=True)
class RegisteredTrustedFrontendModule:
    extension_id: str
    module_id: str
    sdk_version: str
    integrity: str
    asset_path: str


@dataclass(frozen=True, slots=True)
class _RegisteredExtension:
    services: ExtensionServices
    source: ExtensionSource


class ExtensionDirectory:
    """Own registered extension service bundles and expose portable contributions."""

    def __init__(self) -> None:
        self._services_by_id: dict[str, _RegisteredExtension] = {}
        self._dispose_lock = asyncio.Lock()
        self._disposed = False

    @property
    def disposed(self) -> bool:
        return self._disposed

    @property
    def extension_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._services_by_id))

    def get(self, extension_id: str) -> ExtensionServices | None:
        registered = self._services_by_id.get(extension_id)
        return registered.services if registered is not None else None

    def register(
        self,
        services: ExtensionServices,
        *,
        source: ExtensionSource = ExtensionSource.BUILT_IN,
    ) -> None:
        if self._disposed:
            raise RegistryError("extension directory is disposed")
        if not isinstance(services, ExtensionServices):
            raise RegistryError("services must be an ExtensionServices instance")
        if not isinstance(source, ExtensionSource):
            raise RegistryError("source must be an ExtensionSource")
        extension_id = services.extension_id
        if extension_id in self._services_by_id:
            raise RegistryError(f"duplicate extension id {extension_id!r}")
        self._services_by_id[extension_id] = _RegisteredExtension(services=services, source=source)

    async def unregister(self, extension_id: str) -> ExtensionServices | None:
        registered = self._services_by_id.pop(extension_id, None)
        if registered is None:
            return None
        await registered.services.dispose()
        return registered.services

    def lookup_asset(self, extension_id: str, path: str) -> AssetRecord | None:
        registered = self._services_by_id.get(extension_id)
        if registered is None:
            return None
        try:
            return registered.services.assets.lookup(path)
        except RegistryError:
            return None

    def lookup_route(self, extension_id: str, method: str, path: str) -> RouteSpec | None:
        registered = self._services_by_id.get(extension_id)
        if registered is None:
            return None
        try:
            return registered.services.routes.get(method, path)
        except RegistryError:
            return None

    def lookup_widget(self, extension_id: str, widget_id: str) -> WidgetSpec | None:
        registered = self._services_by_id.get(extension_id)
        if registered is None:
            return None
        try:
            return registered.services.widgets.get(widget_id)
        except RegistryError:
            return None

    def lookup_trusted_frontend_module(
        self,
        extension_id: str,
        module_id: str,
    ) -> RegisteredTrustedFrontendModule | None:
        registered = self._services_by_id.get(extension_id)
        if registered is None or registered.source is ExtensionSource.WORKSPACE:
            return None
        try:
            module = registered.services.trusted_frontend.get(module_id)
        except RegistryError:
            return None
        if module is None:
            return None
        return _trusted_frontend_module_record(extension_id, module)

    def list_trusted_frontend_modules(
        self,
        *,
        limit: int,
    ) -> tuple[RegisteredTrustedFrontendModule, ...]:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
            raise RegistryError("limit must be a non-negative int")
        if limit == 0:
            return ()
        records: list[RegisteredTrustedFrontendModule] = []
        for extension_id in sorted(self._services_by_id):
            registered = self._services_by_id[extension_id]
            if registered.source is ExtensionSource.WORKSPACE:
                continue
            for module in registered.services.trusted_frontend.items():
                records.append(_trusted_frontend_module_record(extension_id, module))
                if len(records) >= limit:
                    return tuple(records)
        return tuple(records)

    async def render_file(self, context: FileRenderContext) -> ResolvedFileRenderer | None:
        candidates: list[tuple[int, str, FileRendererSpec]] = []
        for extension_id in sorted(self._services_by_id):
            services = self._services_by_id[extension_id].services
            for spec in services.file_renderers.items():
                if spec.matches(context):
                    candidates.append((-spec.priority, extension_id, spec))
        for _priority, extension_id, spec in sorted(
            candidates, key=lambda item: (item[0], item[1], item[2].id)
        ):
            try:
                output = await asyncio.wait_for(
                    _invoke_handler(spec.handler, context),
                    timeout=_EXTENDED_UI_TIMEOUT_SECONDS,
                )
            except (asyncio.CancelledError, KeyboardInterrupt):
                raise
            except Exception:
                continue
            if isinstance(output, StandardView):
                return ResolvedFileRenderer(extension_id, spec.id, output)
            if (
                isinstance(output, WidgetReference)
                and self.lookup_widget(extension_id, output.widget_id) is not None
            ):
                return ResolvedFileRenderer(extension_id, spec.id, output)
        return None

    async def annotate_file(self, context: FileRenderContext) -> tuple[ResolvedAnnotation, ...]:
        candidates: list[tuple[int, str, AnnotationProviderSpec]] = []
        for extension_id in sorted(self._services_by_id):
            services = self._services_by_id[extension_id].services
            for spec in services.annotation_providers.items():
                if spec.matches(context):
                    candidates.append((-spec.priority, extension_id, spec))
        resolved: list[ResolvedAnnotation] = []
        for _priority, extension_id, spec in sorted(
            candidates, key=lambda item: (item[0], item[1], item[2].id)
        ):
            try:
                value = await asyncio.wait_for(
                    _invoke_handler(spec.handler, context),
                    timeout=_EXTENDED_UI_TIMEOUT_SECONDS,
                )
                annotations = validate_annotations(value)
            except (asyncio.CancelledError, KeyboardInterrupt):
                raise
            except Exception:
                continue
            resolved.extend(
                ResolvedAnnotation(extension_id, spec.id, annotation) for annotation in annotations
            )
        return tuple(resolved)

    async def invoke_widget_action(
        self,
        extension_id: str,
        widget_id: str,
        action: str,
        payload: object,
    ) -> object:
        widget = self.lookup_widget(extension_id, widget_id)
        if widget is None:
            raise LookupError("unknown widget")
        handler = widget.actions.get(action)
        if handler is None:
            raise LookupError("unknown widget action")
        return await asyncio.wait_for(
            _invoke_handler(handler, payload),
            timeout=_EXTENDED_UI_TIMEOUT_SECONDS,
        )

    async def dispose(self) -> None:
        async with self._dispose_lock:
            if self._disposed:
                return
            services = tuple(registered.services for registered in self._services_by_id.values())
            self._services_by_id.clear()
            self._disposed = True

        first_error: BaseException | None = None
        for services_bundle in services:
            try:
                await services_bundle.dispose()
            except BaseException as exc:
                if first_error is None:
                    first_error = exc
        if first_error is not None:
            raise first_error


async def _invoke_handler(handler: object, argument: object) -> object:
    if inspect.iscoroutinefunction(handler):
        return await cast(Awaitable[object], handler(argument))
    result = await asyncio.to_thread(cast(Callable[[object], object], handler), argument)
    if inspect.isawaitable(result):
        return await cast(Awaitable[object], result)
    return result


def _trusted_frontend_module_record(
    extension_id: str,
    module: TrustedFrontendModuleSpec,
) -> RegisteredTrustedFrontendModule:
    return RegisteredTrustedFrontendModule(
        extension_id=extension_id,
        module_id=module.id,
        sdk_version=module.sdk_version,
        integrity=module.integrity,
        asset_path=module.script_path,
    )


def _stored_value_from_record(record: ExtensionStateRecord) -> StoredValue:
    return StoredValue(value=record.value, revision=record.revision)


def _portable_revision_conflict(
    exc: RepositoryRevisionConflictError,
) -> RevisionConflictError:
    return RevisionConflictError(exc.entity, expected=exc.expected, actual=exc.actual)


__all__ = [
    "ExtensionDirectory",
    "RegisteredTrustedFrontendModule",
    "ResolvedAnnotation",
    "ResolvedFileRenderer",
    "SqliteExtensionStorageBackend",
]
