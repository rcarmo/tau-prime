from __future__ import annotations

import base64
import hashlib
from collections.abc import Mapping

import pytest

from tau_extensions import (
    TRUSTED_FRONTEND_SDK_VERSION,
    AnnotationProviderSpec,
    EditorAnnotation,
    ExtensionServices,
    FileRenderContext,
    FileRendererSpec,
    PermissionDeniedError,
    RegistryError,
    StorageScope,
    StoredValue,
    TrustedFrontendModuleSpec,
    WidgetReference,
    WidgetSpec,
    validate_annotations,
)
from tau_extensions.types import JSONValue
from tau_extensions.web import StandardView, Text


class FakeStorageBackend:
    async def get(
        self,
        extension_id: str,
        *,
        scope: StorageScope,
        scope_id: str,
        key: str,
    ) -> StoredValue | None:
        del extension_id, scope, scope_id, key
        return None

    async def list(
        self,
        extension_id: str,
        *,
        scope: StorageScope,
        scope_id: str,
    ) -> Mapping[str, StoredValue]:
        del extension_id, scope, scope_id
        return {}

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
        del extension_id, scope, scope_id, key, expected_revision
        return StoredValue(value=value, revision=1)

    async def delete(
        self,
        extension_id: str,
        *,
        scope: StorageScope,
        scope_id: str,
        key: str,
        expected_revision: int,
    ) -> StoredValue | None:
        del extension_id, scope, scope_id, key, expected_revision
        return None


def _sri_sha256(content: bytes) -> str:
    return f"sha256-{base64.b64encode(hashlib.sha256(content).digest()).decode('ascii')}"


def test_file_renderer_and_annotation_contracts_match_and_dispose() -> None:
    services = ExtensionServices("com.example.extended", ["views"], FakeStorageBackend())
    context = FileRenderContext("notes/demo.md", "text/markdown", "# Demo")
    view = StandardView(
        id="markdown-preview",
        title="Markdown preview",
        placement="sidebar",
        components=(Text("Demo"),),
    )
    renderer = FileRendererSpec(
        "markdown",
        lambda value: view if value.content else None,
        filename_patterns=("*.md",),
        priority=10,
    )
    provider = AnnotationProviderSpec(
        "headings",
        lambda value: (EditorAnnotation(1, f"{value.path} heading", source="demo"),),
        media_types=("text/*",),
    )

    renderer_handle = services.file_renderers.register(renderer)
    provider_handle = services.annotation_providers.register(provider)

    assert renderer.matches(context)
    assert provider.matches(context)
    assert services.file_renderers.items() == (renderer,)
    assert services.annotation_providers.items() == (provider,)
    assert validate_annotations((EditorAnnotation(1, "ok"),))[0].to_json() == {
        "line": 1,
        "message": "ok",
        "severity": "info",
    }

    renderer_handle.dispose()
    provider_handle.dispose()
    assert services.file_renderers.items() == ()
    assert services.annotation_providers.items() == ()


def test_extended_ui_permissions_validation_and_widget_assets() -> None:
    services = ExtensionServices("com.example.denied", [], FakeStorageBackend())
    with pytest.raises(PermissionDeniedError, match="views"):
        services.file_renderers.register(
            FileRendererSpec("text", lambda context: None, media_types=("text/plain",))
        )

    widget_services = ExtensionServices(
        "com.example.widgets",
        ["assets", "sandboxed_widgets"],
        FakeStorageBackend(),
    )
    widget_services.assets.register(
        "widget.js",
        b"document.body.dataset.ready = 'yes';",
        mime_type="application/javascript",
    )
    widget_services.assets.register(
        "widget.css",
        b"body { color: white; }",
        mime_type="text/css",
    )
    widget = WidgetSpec(
        "preview",
        "Preview",
        "widget.js",
        style_path="widget.css",
        actions={"refresh": lambda payload: {"payload": payload}},
    )
    handle = widget_services.widgets.register(widget)

    assert widget_services.widgets.get("preview") == widget
    assert WidgetReference("preview").widget_id == "preview"
    handle.dispose()
    assert widget_services.widgets.get("preview") is None

    with pytest.raises(RegistryError, match="JavaScript asset"):
        widget_services.widgets.register(WidgetSpec("missing", "Missing", "missing.js"))


def test_extended_ui_rejects_invalid_and_unbounded_values() -> None:
    with pytest.raises(RegistryError, match="basename globs"):
        FileRendererSpec("bad", lambda context: None, filename_patterns=("../*.md",))
    with pytest.raises(RegistryError, match="at least 1"):
        EditorAnnotation(0, "bad")
    with pytest.raises(RegistryError, match="between 120 and 1200"):
        WidgetSpec("bad", "Bad", "widget.js", height=5000)
    with pytest.raises(RegistryError, match="at most 256"):
        validate_annotations(tuple(EditorAnnotation(1, "x") for _ in range(257)))


def test_trusted_frontend_registry_registers_valid_module_and_disposes() -> None:
    services = ExtensionServices(
        "com.example.trusted",
        ["assets", "trusted_frontend"],
        FakeStorageBackend(),
    )
    script = b"console.log('trusted');"
    integrity = _sri_sha256(script)

    services.assets.register("trusted/main.js", script, mime_type="application/javascript")
    module = TrustedFrontendModuleSpec(
        "shell",
        "trusted/main.js",
        integrity,
    )

    handle = services.trusted_frontend.register(module)

    assert services.trusted_frontend.get("shell") == module
    assert services.trusted_frontend.items() == (module,)
    assert module.sdk_version == TRUSTED_FRONTEND_SDK_VERSION

    handle.dispose()
    assert services.trusted_frontend.get("shell") is None
    assert services.trusted_frontend.items() == ()


def test_trusted_frontend_registry_rejects_invalid_sri_syntax() -> None:
    with pytest.raises(RegistryError, match="sha256-<base64 digest>"):
        TrustedFrontendModuleSpec("shell", "trusted/main.js", "sha256-not-base64")


def test_trusted_frontend_registry_rejects_integrity_mismatch() -> None:
    services = ExtensionServices(
        "com.example.trusted",
        ["assets", "trusted_frontend"],
        FakeStorageBackend(),
    )
    script = b"console.log('actual');"
    services.assets.register("trusted/main.js", script, mime_type="application/javascript")

    with pytest.raises(RegistryError, match="declared integrity"):
        services.trusted_frontend.register(
            TrustedFrontendModuleSpec(
                "shell",
                "trusted/main.js",
                _sri_sha256(b"console.log('different');"),
            )
        )


def test_trusted_frontend_registry_rejects_wrong_asset_mime() -> None:
    services = ExtensionServices(
        "com.example.trusted",
        ["assets", "trusted_frontend"],
        FakeStorageBackend(),
    )
    script = b"console.log('trusted');"
    services.assets.register("trusted/main.js", script, mime_type="text/plain")

    with pytest.raises(RegistryError, match="JavaScript asset"):
        services.trusted_frontend.register(
            TrustedFrontendModuleSpec("shell", "trusted/main.js", _sri_sha256(script))
        )


def test_trusted_frontend_registry_requires_assets_and_trusted_frontend_permissions() -> None:
    module = TrustedFrontendModuleSpec(
        "shell",
        "trusted/main.js",
        _sri_sha256(b"console.log('trusted');"),
    )

    missing_assets = ExtensionServices(
        "com.example.trusted",
        ["trusted_frontend"],
        FakeStorageBackend(),
    )
    with pytest.raises(PermissionDeniedError, match="assets"):
        missing_assets.trusted_frontend.register(module)

    missing_trusted_frontend = ExtensionServices(
        "com.example.trusted",
        ["assets"],
        FakeStorageBackend(),
    )
    script = b"console.log('trusted');"
    missing_trusted_frontend.assets.register(
        "trusted/main.js",
        script,
        mime_type="application/javascript",
    )
    with pytest.raises(PermissionDeniedError, match="trusted_frontend"):
        missing_trusted_frontend.trusted_frontend.register(module)


def test_trusted_frontend_registry_rejects_unsupported_sdk() -> None:
    with pytest.raises(RegistryError, match="sdk_version"):
        TrustedFrontendModuleSpec(
            "shell",
            "trusted/main.js",
            _sri_sha256(b"console.log('trusted');"),
            sdk_version="2.0",
        )
