"""Portable extended UI contribution contracts for Tau extensions.

The contracts in this module do not depend on Tau Web. Python extensions own
matching and behavior while hosts retain control over rendering and the DOM.
"""

from __future__ import annotations

import base64
import binascii
import fnmatch
import hashlib
import hmac
import re
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Literal, Protocol, cast

from tau_extensions.manifest import Permission
from tau_extensions.runtime import DisposalHandle, RegistryError
from tau_extensions.types import JSONObject, JSONValue
from tau_extensions.web import StandardView

MAX_ANNOTATIONS = 256
MAX_ANNOTATION_MESSAGE_BYTES = 8 * 1024
MAX_WIDGET_HEIGHT = 1200
MIN_WIDGET_HEIGHT = 120
TRUSTED_FRONTEND_SDK_VERSION = "1.0"

type FileRendererHandler = Callable[
    ["FileRenderContext"], "FileRenderOutput | Awaitable[FileRenderOutput]"
]
type FileRenderOutput = StandardView | "WidgetReference" | None
type AnnotationHandler = Callable[
    ["FileRenderContext"],
    "Sequence[EditorAnnotation] | Awaitable[Sequence[EditorAnnotation]]",
]
type WidgetActionHandler = Callable[[JSONObject], JSONValue | Awaitable[JSONValue]]
type AnnotationSeverity = Literal["info", "warning", "error"]

_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")
_MIME_RE = re.compile(r"^[A-Za-z0-9!#$&^_.+*-]+/[A-Za-z0-9!#$&^_.+*-]+$")


class _ServiceContext(Protocol):
    extension_id: str

    def require_permission(self, permission: Permission) -> None: ...


class _RegisteredAsset(Protocol):
    @property
    def content(self) -> bytes: ...

    @property
    def mime_type(self) -> str: ...


@dataclass(frozen=True, slots=True)
class FileRenderContext:
    """One bounded UTF-8 workspace file exposed to a contribution."""

    path: str
    media_type: str
    content: str

    def __post_init__(self) -> None:
        if not isinstance(self.path, str) or not self.path or "\x00" in self.path:
            raise RegistryError("path must be a non-empty string without NUL")
        object.__setattr__(self, "media_type", _validate_media_type(self.media_type))
        if not isinstance(self.content, str):
            raise RegistryError("content must be a string")


@dataclass(frozen=True, slots=True)
class WidgetReference:
    """Reference a widget registered by the same extension."""

    widget_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "widget_id", _validate_name(self.widget_id, "widget_id"))


@dataclass(frozen=True, slots=True)
class FileRendererSpec:
    """Match a file and return a declarative view or sandboxed widget."""

    id: str
    handler: FileRendererHandler
    filename_patterns: tuple[str, ...] = ()
    media_types: tuple[str, ...] = ()
    priority: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _validate_name(self.id, "id"))
        if not callable(self.handler):
            raise RegistryError("file renderer handler must be callable")
        object.__setattr__(
            self,
            "filename_patterns",
            _validate_patterns(self.filename_patterns),
        )
        object.__setattr__(
            self,
            "media_types",
            tuple(_validate_media_type(value) for value in self.media_types),
        )
        if not self.filename_patterns and not self.media_types:
            raise RegistryError("file renderer must declare a filename pattern or media type")
        if not isinstance(self.priority, int) or isinstance(self.priority, bool):
            raise RegistryError("priority must be an int")
        if not -1000 <= self.priority <= 1000:
            raise RegistryError("priority must be between -1000 and 1000")

    def matches(self, context: FileRenderContext) -> bool:
        filename = PurePosixPath(context.path).name
        return any(
            fnmatch.fnmatchcase(filename, pattern) for pattern in self.filename_patterns
        ) or any(_media_type_matches(pattern, context.media_type) for pattern in self.media_types)


@dataclass(frozen=True, slots=True)
class EditorAnnotation:
    """A bounded line-oriented annotation for the read-only editor."""

    line: int
    message: str
    end_line: int | None = None
    severity: AnnotationSeverity = "info"
    code: str | None = None
    source: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.line, int) or isinstance(self.line, bool) or self.line < 1:
            raise RegistryError("annotation line must be an int of at least 1")
        if self.end_line is not None and (
            not isinstance(self.end_line, int)
            or isinstance(self.end_line, bool)
            or self.end_line < self.line
        ):
            raise RegistryError("annotation end_line must be at least line")
        object.__setattr__(
            self,
            "message",
            _validate_text(self.message, "annotation message", MAX_ANNOTATION_MESSAGE_BYTES),
        )
        if self.severity not in ("info", "warning", "error"):
            raise RegistryError("annotation severity must be info, warning, or error")
        if self.code is not None:
            object.__setattr__(self, "code", _validate_name(self.code, "annotation code"))
        if self.source is not None:
            object.__setattr__(
                self, "source", _validate_text(self.source, "annotation source", 256)
            )

    def to_json(self) -> JSONObject:
        value: JSONObject = {
            "line": self.line,
            "message": self.message,
            "severity": self.severity,
        }
        if self.end_line is not None:
            value["end_line"] = self.end_line
        if self.code is not None:
            value["code"] = self.code
        if self.source is not None:
            value["source"] = self.source
        return value


@dataclass(frozen=True, slots=True)
class AnnotationProviderSpec:
    """Match files and return line-oriented editor annotations."""

    id: str
    handler: AnnotationHandler
    filename_patterns: tuple[str, ...] = ()
    media_types: tuple[str, ...] = ()
    priority: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _validate_name(self.id, "id"))
        if not callable(self.handler):
            raise RegistryError("annotation handler must be callable")
        object.__setattr__(self, "filename_patterns", _validate_patterns(self.filename_patterns))
        object.__setattr__(
            self,
            "media_types",
            tuple(_validate_media_type(value) for value in self.media_types),
        )
        if not self.filename_patterns and not self.media_types:
            raise RegistryError("annotation provider must declare a filename pattern or media type")
        if not isinstance(self.priority, int) or isinstance(self.priority, bool):
            raise RegistryError("priority must be an int")
        if not -1000 <= self.priority <= 1000:
            raise RegistryError("priority must be between -1000 and 1000")

    def matches(self, context: FileRenderContext) -> bool:
        filename = PurePosixPath(context.path).name
        return any(
            fnmatch.fnmatchcase(filename, pattern) for pattern in self.filename_patterns
        ) or any(_media_type_matches(pattern, context.media_type) for pattern in self.media_types)


@dataclass(frozen=True, slots=True)
class WidgetSpec:
    """A host-wrapped, opaque-origin widget backed by registered assets."""

    id: str
    title: str
    script_path: str
    style_path: str | None = None
    height: int = 360
    actions: Mapping[str, WidgetActionHandler] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _validate_name(self.id, "id"))
        object.__setattr__(self, "title", _validate_text(self.title, "title", 512))
        object.__setattr__(self, "script_path", _validate_asset_path(self.script_path))
        if self.style_path is not None:
            object.__setattr__(self, "style_path", _validate_asset_path(self.style_path))
        if not isinstance(self.height, int) or isinstance(self.height, bool):
            raise RegistryError("widget height must be an int")
        if not MIN_WIDGET_HEIGHT <= self.height <= MAX_WIDGET_HEIGHT:
            raise RegistryError(
                f"widget height must be between {MIN_WIDGET_HEIGHT} and {MAX_WIDGET_HEIGHT}"
            )
        if not isinstance(self.actions, Mapping):
            raise RegistryError("widget actions must be a mapping")
        normalized: dict[str, WidgetActionHandler] = {}
        for name, handler in self.actions.items():
            normalized_name = _validate_name(name, "widget action name")
            if not callable(handler):
                raise RegistryError("widget action handlers must be callable")
            normalized[normalized_name] = handler
        object.__setattr__(self, "actions", MappingProxyType(normalized))


class _SpecRegistry:
    def __init__(self, context: _ServiceContext, permission: Permission) -> None:
        self._context = context
        self._permission = permission
        self._specs: dict[str, object] = {}

    def _register(self, spec_id: str, spec: object) -> DisposalHandle:
        self._context.require_permission(self._permission)
        if spec_id in self._specs:
            raise RegistryError(f"duplicate contribution id {spec_id!r}")
        self._specs[spec_id] = spec

        def dispose() -> None:
            self._specs.pop(spec_id, None)

        return DisposalHandle(dispose)

    def get(self, spec_id: str) -> object | None:
        return self._specs.get(_validate_name(spec_id, "id"))

    def items(self) -> tuple[object, ...]:
        return tuple(self._specs.values())

    def dispose(self) -> None:
        self._specs.clear()


class FileRendererRegistry(_SpecRegistry):
    def __init__(self, context: _ServiceContext) -> None:
        super().__init__(context, "views")

    def register(self, spec: FileRendererSpec) -> DisposalHandle:
        if not isinstance(spec, FileRendererSpec):
            raise RegistryError("spec must be a FileRendererSpec")
        return self._register(spec.id, spec)

    def get(self, spec_id: str) -> FileRendererSpec | None:
        return cast(FileRendererSpec | None, super().get(spec_id))

    def items(self) -> tuple[FileRendererSpec, ...]:
        return cast(tuple[FileRendererSpec, ...], super().items())


class AnnotationProviderRegistry(_SpecRegistry):
    def __init__(self, context: _ServiceContext) -> None:
        super().__init__(context, "views")

    def register(self, spec: AnnotationProviderSpec) -> DisposalHandle:
        if not isinstance(spec, AnnotationProviderSpec):
            raise RegistryError("spec must be an AnnotationProviderSpec")
        return self._register(spec.id, spec)

    def get(self, spec_id: str) -> AnnotationProviderSpec | None:
        return cast(AnnotationProviderSpec | None, super().get(spec_id))

    def items(self) -> tuple[AnnotationProviderSpec, ...]:
        return cast(tuple[AnnotationProviderSpec, ...], super().items())


class WidgetRegistry(_SpecRegistry):
    def __init__(
        self,
        context: _ServiceContext,
        asset_lookup: Callable[[str], object | None],
    ) -> None:
        super().__init__(context, "sandboxed_widgets")
        self._asset_lookup = asset_lookup

    def register(self, spec: WidgetSpec) -> DisposalHandle:
        if not isinstance(spec, WidgetSpec):
            raise RegistryError("spec must be a WidgetSpec")
        script = self._asset_lookup(spec.script_path)
        if script is None or getattr(script, "mime_type", None) not in (
            "application/javascript",
            "text/javascript",
        ):
            raise RegistryError("widget script_path must reference a registered JavaScript asset")
        if spec.style_path is not None:
            style = self._asset_lookup(spec.style_path)
            if style is None or getattr(style, "mime_type", None) != "text/css":
                raise RegistryError("widget style_path must reference a registered CSS asset")
        return self._register(spec.id, spec)

    def get(self, spec_id: str) -> WidgetSpec | None:
        return cast(WidgetSpec | None, super().get(spec_id))

    def items(self) -> tuple[WidgetSpec, ...]:
        return cast(tuple[WidgetSpec, ...], super().items())


@dataclass(frozen=True, slots=True)
class TrustedFrontendModuleSpec:
    """One trusted same-origin frontend module backed by a local JavaScript asset."""

    id: str
    script_path: str
    integrity: str
    sdk_version: str = TRUSTED_FRONTEND_SDK_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _validate_name(self.id, "id"))
        object.__setattr__(
            self,
            "script_path",
            _validate_trusted_frontend_script_path(self.script_path),
        )
        object.__setattr__(self, "integrity", _validate_integrity(self.integrity))
        if self.sdk_version != TRUSTED_FRONTEND_SDK_VERSION:
            raise RegistryError(
                f"trusted frontend sdk_version must be {TRUSTED_FRONTEND_SDK_VERSION!r}"
            )


class TrustedFrontendRegistry(_SpecRegistry):
    def __init__(
        self,
        context: _ServiceContext,
        asset_lookup: Callable[[str], object | None],
    ) -> None:
        super().__init__(context, "trusted_frontend")
        self._asset_lookup = asset_lookup

    def register(self, spec: TrustedFrontendModuleSpec) -> DisposalHandle:
        self._context.require_permission("assets")
        if not isinstance(spec, TrustedFrontendModuleSpec):
            raise RegistryError("spec must be a TrustedFrontendModuleSpec")
        asset = self._asset_lookup(spec.script_path)
        if asset is None or getattr(asset, "mime_type", None) not in (
            "application/javascript",
            "text/javascript",
        ):
            raise RegistryError(
                "trusted frontend script_path must reference a registered JavaScript asset"
            )
        registered_asset = cast(_RegisteredAsset, asset)
        if not hmac.compare_digest(
            _integrity_for_bytes(registered_asset.content),
            spec.integrity,
        ):
            raise RegistryError("trusted frontend asset bytes do not match declared integrity")
        return self._register(spec.id, spec)

    def get(self, spec_id: str) -> TrustedFrontendModuleSpec | None:
        return cast(TrustedFrontendModuleSpec | None, super().get(spec_id))

    def items(self) -> tuple[TrustedFrontendModuleSpec, ...]:
        return tuple(
            cast(TrustedFrontendModuleSpec, self._specs[spec_id]) for spec_id in sorted(self._specs)
        )


def validate_annotations(value: object) -> tuple[EditorAnnotation, ...]:
    """Validate and bound one provider result."""
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise RegistryError("annotation provider must return a sequence of EditorAnnotation values")
    if len(value) > MAX_ANNOTATIONS:
        raise RegistryError(f"annotation provider must return at most {MAX_ANNOTATIONS} items")
    annotations: list[EditorAnnotation] = []
    for item in value:
        if not isinstance(item, EditorAnnotation):
            raise RegistryError("annotation provider must return EditorAnnotation values")
        annotations.append(item)
    return tuple(annotations)


def _validate_name(value: str, field_name: str) -> str:
    if not isinstance(value, str) or _SAFE_NAME_RE.fullmatch(value) is None:
        raise RegistryError(f"{field_name} must match {_SAFE_NAME_RE.pattern!r}")
    return value


def _validate_text(value: str, field_name: str, max_bytes: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RegistryError(f"{field_name} must be a non-blank string")
    if len(value.encode("utf-8")) > max_bytes:
        raise RegistryError(f"{field_name} must be at most {max_bytes} bytes")
    return value


def _validate_patterns(patterns: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(patterns, tuple):
        raise RegistryError("filename_patterns must be a tuple")
    normalized: list[str] = []
    for pattern in patterns:
        if (
            not isinstance(pattern, str)
            or not pattern
            or len(pattern.encode("utf-8")) > 256
            or "/" in pattern
            or "\\" in pattern
            or "\x00" in pattern
        ):
            raise RegistryError("filename patterns must be bounded basename globs")
        normalized.append(pattern)
    return tuple(normalized)


def _validate_media_type(value: str) -> str:
    if not isinstance(value, str):
        raise RegistryError("media_type must be a string")
    normalized = value.strip().lower()
    if _MIME_RE.fullmatch(normalized) is None:
        raise RegistryError("media_type must be a valid type/subtype string")
    if "*" in normalized and not normalized.endswith("/*"):
        raise RegistryError("media_type wildcard is permitted only as type/*")
    return normalized


def _media_type_matches(pattern: str, value: str) -> bool:
    return pattern == value or (pattern.endswith("/*") and value.startswith(pattern[:-1]))


def _validate_asset_path(path: str) -> str:
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path:
        raise RegistryError("widget asset paths must be safe relative paths")
    if any(part in ("", ".", "..") for part in path.split("/")):
        raise RegistryError("widget asset paths must be safe relative paths")
    return path


def _validate_trusted_frontend_script_path(path: str) -> str:
    if (
        not isinstance(path, str)
        or not path
        or path.startswith("/")
        or "\\" in path
        or ":" in path
    ):
        raise RegistryError("trusted frontend script_path must be a safe relative path")
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts) or any(
        any(character.isspace() for character in part) for part in parts
    ):
        raise RegistryError("trusted frontend script_path must be a safe relative path")
    return path


def _validate_integrity(value: str) -> str:
    if not isinstance(value, str):
        raise RegistryError("integrity must use the form 'sha256-<base64 digest>'")
    algorithm, separator, encoded = value.partition("-")
    if algorithm != "sha256" or separator != "-" or not encoded:
        raise RegistryError("integrity must use the form 'sha256-<base64 digest>'")
    try:
        digest = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise RegistryError("integrity must use the form 'sha256-<base64 digest>'") from exc
    if len(digest) != hashlib.sha256().digest_size:
        raise RegistryError("integrity must use the form 'sha256-<base64 digest>'")
    if base64.b64encode(digest).decode("ascii") != encoded:
        raise RegistryError("integrity must use the form 'sha256-<base64 digest>'")
    return value


def _integrity_for_bytes(content: bytes) -> str:
    digest = hashlib.sha256(bytes(content)).digest()
    return f"sha256-{base64.b64encode(digest).decode('ascii')}"


__all__ = [
    "AnnotationHandler",
    "AnnotationProviderRegistry",
    "AnnotationProviderSpec",
    "AnnotationSeverity",
    "EditorAnnotation",
    "FileRenderContext",
    "FileRenderOutput",
    "FileRendererHandler",
    "FileRendererRegistry",
    "FileRendererSpec",
    "MAX_ANNOTATIONS",
    "MAX_ANNOTATION_MESSAGE_BYTES",
    "MAX_WIDGET_HEIGHT",
    "MIN_WIDGET_HEIGHT",
    "TRUSTED_FRONTEND_SDK_VERSION",
    "TrustedFrontendModuleSpec",
    "TrustedFrontendRegistry",
    "WidgetActionHandler",
    "WidgetReference",
    "WidgetRegistry",
    "WidgetSpec",
    "validate_annotations",
]
