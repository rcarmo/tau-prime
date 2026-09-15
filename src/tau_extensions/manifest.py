"""Portable extension manifest contracts for Tau."""

from __future__ import annotations

import json
import math
import re
import stat
from collections.abc import Mapping, Sequence
from functools import total_ordering
from pathlib import Path
from typing import Any, ClassVar, Literal, Never, Self, cast

from pydantic import BaseModel, ConfigDict
from tau_extensions.types import JSONObject, JSONValue

API_VERSION = "1.0"
MAX_MANIFEST_BYTES = 256 * 1024
MAX_CONTRIBUTIONS_BYTES = 128 * 1024


def _parse_api_major(value: str) -> int:
    head = value[1:] if value.startswith("^") else value
    major, _sep, _tail = head.partition(".")
    return int(major)


type Permission = Literal[
    "storage",
    "background_tasks",
    "assets",
    "commands",
    "tools",
    "routes",
    "events",
    "views",
    "actions",
    "sandboxed_widgets",
    "trusted_frontend",
]

_ALLOWED_PERMISSIONS: frozenset[str] = frozenset(
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
        "sandboxed_widgets",
        "trusted_frontend",
    }
)
_MISSING = object()
_ID_LABEL_RE = r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
_ID_RE = re.compile(rf"^(?:(?:{_ID_LABEL_RE}\.)+{_ID_LABEL_RE}|{_ID_LABEL_RE})$")
_ENTRYPOINT_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*:[A-Za-z_][A-Za-z0-9_]*$"
)
_SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
_VERSION_RANGE_RE = re.compile(r"^(\^)?(0|[1-9]\d*)\.(0|[1-9]\d*)(?:\.(0|[1-9]\d*))?$")


class ManifestError(ValueError):
    """Stable error raised for manifest parsing and validation failures."""


@total_ordering
class SemVer(str):
    """Strict semantic version string with minimal ordering support."""

    __slots__ = ("major", "minor", "patch", "prerelease", "build")

    major: int
    minor: int
    patch: int
    prerelease: tuple[int | str, ...]
    build: tuple[str, ...]

    def __new__(cls, value: str) -> Self:
        return cls.parse(value)

    @classmethod
    def parse(cls, value: object, *, field: str = "version") -> Self:
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            raise ManifestError(f"{field} must be a string")
        match = _SEMVER_RE.fullmatch(value)
        if match is None:
            raise ManifestError(f"{field} must be a strict semantic version")
        prerelease = _parse_prerelease(match.group(4), field=field)
        build = tuple(match.group(5).split(".")) if match.group(5) else ()
        instance = str.__new__(cls, value)
        object.__setattr__(instance, "major", int(match.group(1)))
        object.__setattr__(instance, "minor", int(match.group(2)))
        object.__setattr__(instance, "patch", int(match.group(3)))
        object.__setattr__(instance, "prerelease", prerelease)
        object.__setattr__(instance, "build", build)
        return instance

    def __lt__(self, other: object) -> bool:
        other_semver = _coerce_semver_for_compare(other)
        if other_semver is None:
            return NotImplemented
        self_core = (self.major, self.minor, self.patch)
        other_core = (other_semver.major, other_semver.minor, other_semver.patch)
        if self_core != other_core:
            return self_core < other_core
        return _compare_prerelease(self.prerelease, other_semver.prerelease) < 0


@total_ordering
class VersionRange(str):
    """Minimal exact/caret version range helper."""

    __slots__ = ("kind", "major", "minor", "patch")

    kind: Literal["exact", "caret"]
    major: int
    minor: int
    patch: int | None

    def __new__(cls, value: str) -> Self:
        return cls.parse(value)

    @classmethod
    def parse(
        cls,
        value: object,
        *,
        field: str = "version range",
        allow_patch: bool = True,
    ) -> Self:
        if isinstance(value, cls):
            if not allow_patch and value.patch is not None:
                raise ManifestError(f"{field} must be an exact or caret major.minor version")
            return value
        if not isinstance(value, str):
            raise ManifestError(f"{field} must be a string")
        match = _VERSION_RANGE_RE.fullmatch(value)
        if match is None or (not allow_patch and match.group(4) is not None):
            if allow_patch:
                raise ManifestError(f"{field} must be an exact or caret version range")
            raise ManifestError(f"{field} must be an exact or caret major.minor version")
        instance = str.__new__(cls, value)
        object.__setattr__(instance, "kind", "caret" if match.group(1) else "exact")
        object.__setattr__(instance, "major", int(match.group(2)))
        object.__setattr__(instance, "minor", int(match.group(3)))
        object.__setattr__(instance, "patch", int(match.group(4)) if match.group(4) else None)
        return instance

    @property
    def base(self) -> tuple[int, int, int]:
        return (self.major, self.minor, self.patch or 0)

    def contains(self, version: SemVer) -> bool:
        if version.major != self.major:
            return False
        if self.kind == "exact":
            if self.patch is None:
                return version.minor == self.minor
            return (version.minor, version.patch) == (self.minor, self.patch)
        if self.patch is None:
            return version.minor >= self.minor
        return (version.minor, version.patch) >= (self.minor, self.patch)

    def is_api_compatible_with(self, api_version: str) -> bool:
        return self.major == _parse_api_major(api_version)

    def __lt__(self, other: object) -> bool:
        other_range = _coerce_version_range_for_compare(other)
        if other_range is None:
            return NotImplemented
        if self.base != other_range.base:
            return self.base < other_range.base
        return (self.kind == "exact") and (other_range.kind == "caret")


class FrozenModel(BaseModel):
    """Small frozen BaseModel compatible with Tau's lightweight pydantic shim."""

    model_config = ConfigDict(extra="forbid")

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_frozen", False) and not name.startswith("_"):
            raise TypeError(f"{self.__class__.__name__} is frozen")
        object.__setattr__(self, name, value)

    @classmethod
    def model_validate(cls, value: Any) -> Any:
        if isinstance(value, cls):
            return value
        if not isinstance(value, dict):
            raise ManifestError(f"{cls.__name__} must be an object")
        return cls(**value)

    def _freeze(self) -> None:
        object.__setattr__(self, "_frozen", True)

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        exclude_none = bool(kwargs.get("exclude_none", False))
        output: dict[str, Any] = {}
        for field_name in self.__class__.__annotations__:
            if field_name.startswith("_"):
                continue
            value = getattr(self, field_name)
            if exclude_none and value is None:
                continue
            output[field_name] = _to_plain_value(value)
        return output


class Dependency(FrozenModel):
    """Manifest dependency declaration."""

    id: str
    version: VersionRange | None = None

    @classmethod
    def model_validate(cls, value: Any) -> Self:
        if isinstance(value, cls):
            return value
        data = _require_object(value, message="dependency must be an object")
        _require_keys(data, {"id", "version"}, message="dependency contains unknown field")
        if "id" not in data:
            raise ManifestError("dependency id is required")
        return cls(id=data["id"], version=data.get("version", _MISSING))

    def __init__(self, id: object, version: object = _MISSING) -> None:
        object.__setattr__(self, "id", _validate_manifest_id(id, field="dependency id"))
        object.__setattr__(
            self,
            "version",
            None
            if version is _MISSING
            else VersionRange.parse(version, field="dependency version"),
        )
        self._freeze()


class ExtensionManifest(FrozenModel):
    """Portable extension manifest contract."""

    schema_version: Literal[1]
    id: str
    name: str
    version: SemVer
    api_version: VersionRange
    entrypoint: str
    permissions: frozenset[Permission]
    dependencies: tuple[Dependency, ...]
    contributions: JSONObject

    _api_major: ClassVar[int] = _parse_api_major(API_VERSION)

    @classmethod
    def model_validate(cls, value: Any) -> Self:
        if isinstance(value, cls):
            return value
        data = _require_object(value, message="manifest must be a JSON object")
        _require_keys(
            data,
            {
                "schema_version",
                "id",
                "name",
                "version",
                "api_version",
                "entrypoint",
                "permissions",
                "dependencies",
                "contributions",
            },
            message="manifest contains unknown field",
        )
        required = ("schema_version", "id", "name", "version", "api_version", "entrypoint")
        missing = [field for field in required if field not in data]
        if missing:
            raise ManifestError(f"manifest is missing required field: {missing[0]}")
        return cls(
            schema_version=data["schema_version"],
            id=data["id"],
            name=data["name"],
            version=data["version"],
            api_version=data["api_version"],
            entrypoint=data["entrypoint"],
            permissions=data.get("permissions", _MISSING),
            dependencies=data.get("dependencies", _MISSING),
            contributions=data.get("contributions", _MISSING),
        )

    def __init__(
        self,
        *,
        schema_version: object,
        id: object,
        name: object,
        version: object,
        api_version: object,
        entrypoint: object,
        permissions: object = _MISSING,
        dependencies: object = _MISSING,
        contributions: object = _MISSING,
    ) -> None:
        manifest_id = _validate_manifest_id(id, field="id")
        object.__setattr__(self, "schema_version", _validate_schema_version(schema_version))
        object.__setattr__(self, "id", manifest_id)
        object.__setattr__(self, "name", _validate_name(name))
        object.__setattr__(self, "version", SemVer.parse(version, field="version"))
        api_range = VersionRange.parse(api_version, field="api_version", allow_patch=False)
        if api_range.major != self._api_major:
            raise ManifestError("api_version major is incompatible with tau_extensions API_VERSION")
        object.__setattr__(self, "api_version", api_range)
        object.__setattr__(self, "entrypoint", _validate_entrypoint(entrypoint))
        object.__setattr__(
            self,
            "permissions",
            _validate_permissions(permissions if permissions is not _MISSING else []),
        )
        object.__setattr__(
            self,
            "dependencies",
            _validate_dependencies(
                dependencies if dependencies is not _MISSING else [],
                manifest_id=manifest_id,
            ),
        )
        object.__setattr__(
            self,
            "contributions",
            _validate_contributions(contributions if contributions is not _MISSING else {}),
        )
        self._freeze()


def parse_manifest_bytes(data: bytes | bytearray | memoryview) -> ExtensionManifest:
    """Parse a manifest from bounded UTF-8 JSON bytes."""

    raw = bytes(data)
    if len(raw) > MAX_MANIFEST_BYTES:
        raise ManifestError(f"manifest exceeds {MAX_MANIFEST_BYTES} bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ManifestError("manifest is not valid UTF-8") from exc
    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_finite_number,
        )
    except ManifestError:
        raise
    except json.JSONDecodeError as exc:
        raise ManifestError("manifest is not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise ManifestError("manifest must be a JSON object")
    return ExtensionManifest.model_validate(parsed)


def parse_manifest_file(
    path: str | Path,
    *,
    allow_symlink: bool = False,
) -> ExtensionManifest:
    """Parse a manifest from a regular bounded file."""

    manifest_path = Path(path)
    try:
        path_stat = manifest_path.lstat()
    except FileNotFoundError as exc:
        raise ManifestError("manifest file does not exist") from exc
    if stat.S_ISLNK(path_stat.st_mode) and not allow_symlink:
        raise ManifestError("manifest file must not be a symlink")
    try:
        target_stat = manifest_path.stat() if allow_symlink else path_stat
    except FileNotFoundError as exc:
        raise ManifestError("manifest file does not exist") from exc
    if not stat.S_ISREG(target_stat.st_mode):
        raise ManifestError("manifest file must be a regular file")
    if target_stat.st_size > MAX_MANIFEST_BYTES:
        raise ManifestError(f"manifest exceeds {MAX_MANIFEST_BYTES} bytes")
    data = manifest_path.read_bytes()
    if len(data) > MAX_MANIFEST_BYTES:
        raise ManifestError(f"manifest exceeds {MAX_MANIFEST_BYTES} bytes")
    return parse_manifest_bytes(data)


def _validate_schema_version(value: object) -> Literal[1]:
    if value != 1 or not isinstance(value, int) or isinstance(value, bool):
        raise ManifestError("schema_version must be 1")
    return 1


def _validate_manifest_id(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise ManifestError(f"{field} must be a string")
    if _ID_RE.fullmatch(value) is None:
        raise ManifestError(f"{field} must be a lowercase reverse-domain name or slug")
    return value


def _validate_name(value: object) -> str:
    if not isinstance(value, str):
        raise ManifestError("name must be a string")
    if not value.strip() or len(value) > 128:
        raise ManifestError("name must be non-blank and at most 128 characters")
    return value


def _validate_entrypoint(value: object) -> str:
    if not isinstance(value, str):
        raise ManifestError("entrypoint must be a string")
    if _ENTRYPOINT_RE.fullmatch(value) is None:
        raise ManifestError("entrypoint must match module.path:attribute")
    return value


def _validate_permissions(value: object) -> frozenset[Permission]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ManifestError("permissions must be a JSON array")
    raw_permissions = list(value)
    permissions: list[Permission] = []
    seen: set[str] = set()
    for item in raw_permissions:
        if not isinstance(item, str) or item not in _ALLOWED_PERMISSIONS:
            raise ManifestError(f"permission value is not permitted: {item}")
        if item in seen:
            raise ManifestError("permissions must be unique")
        seen.add(item)
        permissions.append(cast(Permission, item))
    return frozenset(permissions)


def _validate_dependencies(value: object, *, manifest_id: str) -> tuple[Dependency, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray, Mapping)):
        raise ManifestError("dependencies must be a JSON array")
    dependencies: list[Dependency] = []
    seen: set[str] = set()
    for item in value:
        dependency = Dependency.model_validate(item)
        if dependency.id == manifest_id:
            raise ManifestError("dependency id must not match manifest id")
        if dependency.id in seen:
            raise ManifestError("dependency id must be unique")
        seen.add(dependency.id)
        dependencies.append(dependency)
    return tuple(dependencies)


def _validate_contributions(value: object) -> JSONObject:
    if not isinstance(value, dict):
        raise ManifestError("contributions must be a JSON object")
    validated = _validate_json_object(value, path="contributions")
    encoded = json.dumps(validated, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    if len(encoded.encode("utf-8")) > MAX_CONTRIBUTIONS_BYTES:
        raise ManifestError(f"contributions JSON exceeds {MAX_CONTRIBUTIONS_BYTES} bytes")
    return validated


def _validate_json_object(value: dict[object, object], *, path: str) -> dict[str, JSONValue]:
    validated: dict[str, JSONValue] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ManifestError(f"{path} contains a non-string key")
        validated[key] = _validate_json_value(item, path=f"{path}.{key}")
    return validated


def _validate_json_value(value: object, *, path: str) -> JSONValue:
    if value is None or isinstance(value, (str, bool, int)):
        return cast(JSONValue, value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ManifestError(f"{path} contains a non-finite number")
        return value
    if isinstance(value, list):
        return [_validate_json_value(item, path=f"{path}[]") for item in value]
    if isinstance(value, dict):
        return _validate_json_object(value, path=path)
    raise ManifestError(f"{path} contains a non-JSON value")


def _require_object(value: Any, *, message: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(message)
    return value


def _require_keys(value: dict[str, Any], allowed: set[str], *, message: str) -> None:
    unexpected = sorted(key for key in value if key not in allowed)
    if unexpected:
        raise ManifestError(f"{message}: {unexpected[0]}")


def _reject_duplicate_keys(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise ManifestError(f"manifest contains duplicate key: {key}")
        value[key] = item
    return value


def _reject_non_finite_number(value: str) -> Never:
    del value
    raise ManifestError("manifest contains non-finite number")


def _parse_prerelease(value: str | None, *, field: str) -> tuple[int | str, ...]:
    if not value:
        return ()
    identifiers: list[int | str] = []
    for part in value.split("."):
        if part.isdigit():
            if len(part) > 1 and part.startswith("0"):
                raise ManifestError(f"{field} must be a strict semantic version")
            identifiers.append(int(part))
            continue
        identifiers.append(part)
    return tuple(identifiers)


def _compare_prerelease(left: tuple[int | str, ...], right: tuple[int | str, ...]) -> int:
    if left == right:
        return 0
    if not left:
        return 1
    if not right:
        return -1
    for left_part, right_part in zip(left, right, strict=False):
        if left_part == right_part:
            continue
        if isinstance(left_part, int) and isinstance(right_part, int):
            return -1 if left_part < right_part else 1
        if isinstance(left_part, str) and isinstance(right_part, str):
            return -1 if left_part < right_part else 1
        if isinstance(left_part, int):
            return -1
        return 1
    if len(left) < len(right):
        return -1
    return 1


def _coerce_semver_for_compare(value: object) -> SemVer | None:
    if isinstance(value, SemVer):
        return value
    if isinstance(value, str):
        try:
            return SemVer.parse(value)
        except ManifestError:
            return None
    return None


def _coerce_version_range_for_compare(value: object) -> VersionRange | None:
    if isinstance(value, VersionRange):
        return value
    if isinstance(value, str):
        try:
            return VersionRange.parse(value)
        except ManifestError:
            return None
    return None


def _to_plain_value(value: Any) -> Any:
    if isinstance(value, FrozenModel):
        return value.model_dump()
    if isinstance(value, dict):
        return {key: _to_plain_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_to_plain_value(item) for item in value]
    if isinstance(value, frozenset):
        return sorted(cast("frozenset[str]", value))
    if isinstance(value, list):
        return [_to_plain_value(item) for item in value]
    return value


__all__ = [
    "API_VERSION",
    "Dependency",
    "ExtensionManifest",
    "MAX_CONTRIBUTIONS_BYTES",
    "MAX_MANIFEST_BYTES",
    "ManifestError",
    "Permission",
    "SemVer",
    "VersionRange",
    "parse_manifest_bytes",
    "parse_manifest_file",
]
