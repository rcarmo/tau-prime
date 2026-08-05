"""SQLite-backed storage and in-memory registries for Tau web extensions."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping

from tau_agent.types import JSONValue
from tau_extensions import (
    AssetRecord,
    ExtensionServices,
    RegistryError,
    RevisionConflictError,
    RouteSpec,
    StorageBackend,
    StorageScope,
    StoredValue,
)
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


class ExtensionDirectory:
    """Own registered extension service bundles and expose asset/route lookup."""

    def __init__(self) -> None:
        self._services_by_id: dict[str, ExtensionServices] = {}
        self._dispose_lock = asyncio.Lock()
        self._disposed = False

    @property
    def disposed(self) -> bool:
        return self._disposed

    @property
    def extension_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._services_by_id))

    def get(self, extension_id: str) -> ExtensionServices | None:
        return self._services_by_id.get(extension_id)

    def register(self, services: ExtensionServices) -> None:
        if self._disposed:
            raise RegistryError("extension directory is disposed")
        if not isinstance(services, ExtensionServices):
            raise RegistryError("services must be an ExtensionServices instance")
        extension_id = services.extension_id
        if extension_id in self._services_by_id:
            raise RegistryError(f"duplicate extension id {extension_id!r}")
        self._services_by_id[extension_id] = services

    async def unregister(self, extension_id: str) -> ExtensionServices | None:
        services = self._services_by_id.pop(extension_id, None)
        if services is None:
            return None
        await services.dispose()
        return services

    def lookup_asset(self, extension_id: str, path: str) -> AssetRecord | None:
        services = self._services_by_id.get(extension_id)
        if services is None:
            return None
        try:
            return services.assets.lookup(path)
        except RegistryError:
            return None

    def lookup_route(self, extension_id: str, method: str, path: str) -> RouteSpec | None:
        services = self._services_by_id.get(extension_id)
        if services is None:
            return None
        try:
            return services.routes.get(method, path)
        except RegistryError:
            return None

    async def dispose(self) -> None:
        async with self._dispose_lock:
            if self._disposed:
                return
            services = tuple(self._services_by_id.values())
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


def _stored_value_from_record(record: ExtensionStateRecord) -> StoredValue:
    return StoredValue(value=record.value, revision=record.revision)


def _portable_revision_conflict(
    exc: RepositoryRevisionConflictError,
) -> RevisionConflictError:
    return RevisionConflictError(exc.entity, expected=exc.expected, actual=exc.actual)


__all__ = ["ExtensionDirectory", "SqliteExtensionStorageBackend"]
