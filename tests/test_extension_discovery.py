import hashlib
import json
from pathlib import Path

from tau_extensions.discovery import (
    MANIFEST_FILENAME,
    Diagnostic,
    DiscoveryResult,
    ExtensionSource,
    discover_extensions,
)


def _manifest_payload(
    extension_id: str,
    *,
    entrypoint: str = "demo.extension:setup",
    version: str = "1.0.0",
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "id": extension_id,
        "name": f"Extension {extension_id}",
        "version": version,
        "api_version": "^1.0",
        "entrypoint": entrypoint,
        "permissions": ["tools"],
        "dependencies": [],
        "contributions": {},
    }


def _write_manifest(
    extension_dir: Path,
    extension_id: str,
    *,
    entrypoint: str = "demo.extension:setup",
    version: str = "1.0.0",
    indent: int | None = None,
) -> bytes:
    extension_dir.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(
        _manifest_payload(extension_id, entrypoint=entrypoint, version=version),
        indent=indent,
    ).encode("utf-8")
    (extension_dir / MANIFEST_FILENAME).write_bytes(raw)
    return raw


def test_discover_extensions_is_deterministic_and_immediate(tmp_path: Path) -> None:
    workspace_root_b = tmp_path / "workspace-b"
    workspace_root_a = tmp_path / "workspace-a"
    admin_root = tmp_path / "admin-root"
    built_in_root = tmp_path / "built-in-root"

    _write_manifest(workspace_root_b / "zeta", "com.example.workspace-zeta")
    _write_manifest(workspace_root_a / "alpha", "com.example.workspace-alpha")
    _write_manifest(admin_root / "bravo", "com.example.admin-bravo")
    _write_manifest(built_in_root / "charlie", "com.example.builtin-charlie")
    _write_manifest(workspace_root_a / "nested" / "inner", "com.example.ignored")

    result = discover_extensions(
        {
            ExtensionSource.WORKSPACE: [workspace_root_b, workspace_root_a],
            ExtensionSource.BUILT_IN: [built_in_root],
            ExtensionSource.ADMIN: [admin_root],
        }
    )

    assert isinstance(result, DiscoveryResult)
    assert [candidate.manifest.id for candidate in result.candidates] == [
        "com.example.builtin-charlie",
        "com.example.admin-bravo",
        "com.example.workspace-alpha",
        "com.example.workspace-zeta",
    ]
    assert [candidate.path for candidate in result.candidates] == [
        (built_in_root / "charlie").resolve(),
        (admin_root / "bravo").resolve(),
        (workspace_root_a / "alpha").resolve(),
        (workspace_root_b / "zeta").resolve(),
    ]
    assert result.diagnostics == ()


def test_discover_extensions_isolates_malformed_manifests(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    _write_manifest(root / "good", "com.example.good")

    bad_dir = root / "bad"
    bad_dir.mkdir(parents=True)
    bad_manifest = bad_dir / MANIFEST_FILENAME
    bad_manifest.write_bytes(b"[")

    result = discover_extensions({ExtensionSource.WORKSPACE: [root]})

    assert [candidate.manifest.id for candidate in result.candidates] == ["com.example.good"]
    assert result.diagnostics == (
        Diagnostic(
            code="invalid_manifest",
            message="manifest is not valid JSON",
            path=bad_manifest,
            id=None,
        ),
    )


def test_discover_extensions_rejects_symlink_roots_children_and_manifests(
    tmp_path: Path,
) -> None:
    actual_root = tmp_path / "actual-root"
    actual_root.mkdir()
    _write_manifest(actual_root / "ok", "com.example.ok")

    symlink_root = tmp_path / "root-link"
    symlink_root.symlink_to(actual_root, target_is_directory=True)

    regular_root = tmp_path / "regular-root"
    regular_root.mkdir()

    outside_child = tmp_path / "outside-child"
    _write_manifest(outside_child, "com.example.outside")
    (regular_root / "child-link").symlink_to(outside_child, target_is_directory=True)

    manifest_target = tmp_path / "shared-manifest.json"
    manifest_target.write_bytes(_write_manifest(tmp_path / "manifest-source", "com.example.source"))
    manifest_link_dir = regular_root / "manifest-link"
    manifest_link_dir.mkdir()
    (manifest_link_dir / MANIFEST_FILENAME).symlink_to(manifest_target)

    result = discover_extensions(
        {
            ExtensionSource.WORKSPACE: [regular_root],
            ExtensionSource.BUILT_IN: [symlink_root],
        }
    )

    assert result.candidates == ()
    assert {(diagnostic.code, diagnostic.path) for diagnostic in result.diagnostics} == {
        ("root_symlink", symlink_root),
        ("child_symlink", regular_root / "child-link"),
        ("manifest_symlink", manifest_link_dir / MANIFEST_FILENAME),
    }


def test_discover_extensions_resolves_duplicate_ids_by_priority_then_path(
    tmp_path: Path,
) -> None:
    built_in_root = tmp_path / "built-in"
    admin_root = tmp_path / "admin"
    workspace_root = tmp_path / "workspace"

    duplicate_id = "com.example.shared"
    winner_dir = built_in_root / "aa-first"
    loser_built_in_dir = built_in_root / "zz-last"
    loser_admin_dir = admin_root / "mid"
    loser_workspace_dir = workspace_root / "tail"

    _write_manifest(winner_dir, duplicate_id, version="1.0.0")
    _write_manifest(loser_built_in_dir, duplicate_id, version="1.0.1")
    _write_manifest(loser_admin_dir, duplicate_id, version="1.0.2")
    _write_manifest(loser_workspace_dir, duplicate_id, version="1.0.3")

    result = discover_extensions(
        {
            ExtensionSource.WORKSPACE: [workspace_root],
            ExtensionSource.ADMIN: [admin_root],
            ExtensionSource.BUILT_IN: [built_in_root],
        }
    )

    assert [candidate.manifest.id for candidate in result.candidates] == [duplicate_id]
    assert result.candidates[0].path == winner_dir.resolve()
    duplicate_diagnostics = [
        (diagnostic.code, diagnostic.id, diagnostic.path) for diagnostic in result.diagnostics
    ]
    assert duplicate_diagnostics == [
        ("duplicate_id", duplicate_id, loser_built_in_dir.resolve() / MANIFEST_FILENAME),
        ("duplicate_id", duplicate_id, loser_admin_dir.resolve() / MANIFEST_FILENAME),
        ("duplicate_id", duplicate_id, loser_workspace_dir.resolve() / MANIFEST_FILENAME),
    ]


def test_discover_extensions_fingerprint_uses_exact_manifest_bytes(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    extension_dir = root / "demo"

    first_raw = _write_manifest(extension_dir, "com.example.demo", indent=None)
    first = discover_extensions({ExtensionSource.WORKSPACE: [root]}).candidates[0]

    second_raw = _write_manifest(extension_dir, "com.example.demo", indent=2)
    second = discover_extensions({ExtensionSource.WORKSPACE: [root]}).candidates[0]

    assert first.manifest == second.manifest
    assert first.fingerprint == hashlib.sha256(first_raw).hexdigest()
    assert second.fingerprint == hashlib.sha256(second_raw).hexdigest()
    assert first.fingerprint != second.fingerprint


def test_discover_extensions_does_not_import_entrypoints(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    extension_dir = root / "boom"
    _write_manifest(extension_dir, "com.example.boom", entrypoint="boom:setup")
    (extension_dir / "boom.py").write_text(
        'raise RuntimeError("boom imported")\n',
        encoding="utf-8",
    )

    result = discover_extensions({ExtensionSource.WORKSPACE: [root]})

    assert [candidate.manifest.id for candidate in result.candidates] == ["com.example.boom"]
    assert result.diagnostics == ()
