import json
from pathlib import Path

import pytest

from tau_extensions import (
    API_VERSION,
    MAX_CONTRIBUTIONS_BYTES,
    MAX_MANIFEST_BYTES,
    Dependency,
    ExtensionManifest,
    ManifestError,
    SemVer,
    VersionRange,
    parse_manifest_bytes,
    parse_manifest_file,
)


def _manifest_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 1,
        "id": "com.example.demo",
        "name": "Demo Extension",
        "version": "1.2.3",
        "api_version": "^1.0",
        "entrypoint": "demo.extension:setup",
        "permissions": ["commands", "tools"],
        "dependencies": [{"id": "com.example.shared", "version": "^1.1"}],
        "contributions": {
            "commands": [{"name": "demo.hello", "title": "Hello"}],
            "settings": {"enabled": True},
        },
    }
    payload.update(overrides)
    return payload


def _manifest_bytes(**overrides: object) -> bytes:
    return json.dumps(_manifest_payload(**overrides)).encode("utf-8")


def test_parse_manifest_bytes_returns_typed_portable_manifest() -> None:
    manifest = parse_manifest_bytes(_manifest_bytes())

    assert manifest == ExtensionManifest.model_validate(_manifest_payload())
    assert manifest.schema_version == 1
    assert manifest.id == "com.example.demo"
    assert manifest.version == SemVer("1.2.3")
    assert manifest.api_version == VersionRange("^1.0")
    assert manifest.api_version.is_api_compatible_with(API_VERSION) is True
    assert manifest.permissions == frozenset({"commands", "tools"})
    assert manifest.dependencies == (
        Dependency(id="com.example.shared", version=VersionRange("^1.1")),
    )
    assert manifest.contributions == {
        "commands": [{"name": "demo.hello", "title": "Hello"}],
        "settings": {"enabled": True},
    }
    assert manifest.model_dump() == {
        "schema_version": 1,
        "id": "com.example.demo",
        "name": "Demo Extension",
        "version": "1.2.3",
        "api_version": "^1.0",
        "entrypoint": "demo.extension:setup",
        "permissions": ["commands", "tools"],
        "dependencies": [{"id": "com.example.shared", "version": "^1.1"}],
        "contributions": {
            "commands": [{"name": "demo.hello", "title": "Hello"}],
            "settings": {"enabled": True},
        },
    }


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("1.2.3-alpha", "1.2.3-alpha.1"),
        ("1.2.3-alpha.1", "1.2.3-alpha.beta"),
        ("1.2.3-alpha.beta", "1.2.3-beta"),
        ("1.2.3-beta", "1.2.3"),
    ],
)
def test_semver_ordering_and_range_compatibility(left: str, right: str) -> None:
    assert SemVer(left) < SemVer(right)
    assert VersionRange("^1.2").contains(SemVer("1.2.0"))
    assert VersionRange("^1.2").contains(SemVer("1.9.9"))
    assert VersionRange("1.2.3").contains(SemVer("1.2.3"))
    assert VersionRange("1.2.3").contains(SemVer("1.2.4")) is False
    assert VersionRange("^1.2").contains(SemVer("2.0.0")) is False
    assert VersionRange("^1.2").is_api_compatible_with(API_VERSION) is True
    assert VersionRange("^9.0").is_api_compatible_with(API_VERSION) is False


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"schema_version": True}, "schema_version must be 1"),
        ({"id": "Bad.Id"}, "id must be a lowercase reverse-domain name or slug"),
        ({"entrypoint": "demo.extension.setup"}, "entrypoint must match module.path:attribute"),
        ({"permissions": ["tools", "tools"]}, "permissions must be unique"),
        ({"permissions": ["admin"]}, "permission value is not permitted: admin"),
        (
            {"dependencies": [{"id": "com.example.demo"}]},
            "dependency id must not match manifest id",
        ),
        (
            {"dependencies": [{"id": "com.example.one"}, {"id": "com.example.one"}]},
            "dependency id must be unique",
        ),
        ({"dependencies": "not-an-array"}, "dependencies must be a JSON array"),
        (
            {"api_version": "^2.0"},
            "api_version major is incompatible with tau_extensions API_VERSION",
        ),
        (
            {"api_version": "^1.0.0"},
            "api_version must be an exact or caret major.minor version",
        ),
        ({"contributions": []}, "contributions must be a JSON object"),
    ],
)
def test_manifest_validation_errors_are_exact(
    payload: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ManifestError, match=f"^{message}$"):
        parse_manifest_bytes(_manifest_bytes(**payload))


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        (b"\xff", "manifest is not valid UTF-8"),
        (b"[1, 2, 3]", "manifest must be a JSON object"),
        (
            b'{"schema_version":1,"id":"com.example.demo","id":"com.example.other"}',
            "manifest contains duplicate key: id",
        ),
        (
            b'{"schema_version":1,"id":"com.example.demo","name":"Demo","version":"1.2.3",'
            b'"api_version":"^1.0","entrypoint":"demo.extension:setup","contributions":{"score":NaN}}',
            "manifest contains non-finite number",
        ),
    ],
)
def test_parse_manifest_bytes_rejects_invalid_json_inputs(raw: bytes, message: str) -> None:
    with pytest.raises(ManifestError, match=f"^{message}$"):
        parse_manifest_bytes(raw)


def test_parse_manifest_bytes_rejects_missing_required_and_unknown_fields() -> None:
    missing = _manifest_payload()
    del missing["entrypoint"]

    with pytest.raises(ManifestError, match=r"^manifest is missing required field: entrypoint$"):
        parse_manifest_bytes(json.dumps(missing).encode("utf-8"))

    with pytest.raises(ManifestError, match=r"^manifest contains unknown field: unexpected$"):
        parse_manifest_bytes(_manifest_bytes(unexpected=True))


def test_parse_manifest_bytes_enforces_manifest_and_contributions_size_limits() -> None:
    oversized_manifest = b"{" + (b"x" * MAX_MANIFEST_BYTES) + b"}"
    with pytest.raises(ManifestError, match=rf"^manifest exceeds {MAX_MANIFEST_BYTES} bytes$"):
        parse_manifest_bytes(oversized_manifest)

    empty_contributions_size = len(
        json.dumps({"blob": ""}, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode(
            "utf-8"
        )
    )
    oversized_blob = "x" * (MAX_CONTRIBUTIONS_BYTES - empty_contributions_size + 1)

    with pytest.raises(
        ManifestError,
        match=rf"^contributions JSON exceeds {MAX_CONTRIBUTIONS_BYTES} bytes$",
    ):
        parse_manifest_bytes(_manifest_bytes(contributions={"blob": oversized_blob}))


def test_extension_manifest_model_validate_rejects_non_json_contributions_values() -> None:
    payload = _manifest_payload(contributions={"bad": {1, 2, 3}})

    with pytest.raises(ManifestError, match=r"^contributions.bad contains a non-JSON value$"):
        ExtensionManifest.model_validate(payload)


def test_parse_manifest_file_rejects_symlink_and_non_regular_files(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_bytes(_manifest_bytes())
    assert parse_manifest_file(manifest_path).id == "com.example.demo"

    link_path = tmp_path / "manifest-link.json"
    link_path.symlink_to(manifest_path)
    with pytest.raises(ManifestError, match=r"^manifest file must not be a symlink$"):
        parse_manifest_file(link_path)

    with pytest.raises(ManifestError, match=r"^manifest file must be a regular file$"):
        parse_manifest_file(tmp_path)
