from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

import build_backend


def test_wheel_metadata_includes_core_and_web_dependencies() -> None:
    metadata = build_backend._metadata_text()

    assert "Provides-Extra: web" in metadata
    assert "Requires-Dist: aiosqlite>=0.22,<1" in metadata
    assert 'Requires-Dist: aiosqlite>=0.22,<1; extra == "web"' not in metadata
    assert 'Requires-Dist: aiohttp>=3.13,<4; extra == "web"' in metadata
    assert 'Requires-Dist: pillow>=12,<13; extra == "web"' in metadata
    assert 'Requires-Dist: watchfiles>=1.1,<2; extra == "web"' in metadata


def test_wheel_includes_optional_runtime_packages() -> None:
    archive_names = {archive_name for _, archive_name in build_backend._package_files()}

    diagnostic_root = build_backend.ROOT / "src" / "tau_extensions" / "builtin" / "diagnostic"
    included_suffixes = {
        ".py",
        ".md",
        ".html",
        ".css",
        ".js",
        ".json",
        ".webmanifest",
        ".svg",
        ".png",
    }
    expected_diagnostic = {
        f"tau_extensions/builtin/diagnostic/{path.relative_to(diagnostic_root).as_posix()}"
        for path in diagnostic_root.rglob("*")
        if path.is_file() and path.suffix in included_suffixes
    }

    assert "tau_extensions/__init__.py" in archive_names
    assert "tau_extensions/web/__init__.py" in archive_names
    assert expected_diagnostic <= archive_names
    assert "tau_extensions/builtin/diagnostic/tau-extension.json" in archive_names
    assert "tau_web/__init__.py" in archive_names
    assert "tau_web/app.py" in archive_names
    assert "tau_web/config.py" in archive_names
    assert "tau_web/middleware.py" in archive_names


def test_wheel_includes_frontend_static_assets() -> None:
    archive_names = {archive_name for _, archive_name in build_backend._package_files()}

    static_root = build_backend.ROOT / "src" / "tau_web" / "static"
    expected_assets = {
        f"tau_web/static/{path.relative_to(static_root).as_posix()}"
        for path in static_root.rglob("*")
        if path.is_file()
    }

    assert expected_assets <= archive_names
    assert "tau_web/static/widget-bridge.js" in archive_names
    assert "tau_web/static/frontend-sdk.js" in archive_names
    assert "tau_web/static/preact-shell.js" in archive_names


def test_vendored_assets_match_pinned_piclaw_2_15_3() -> None:
    # Verified byte-for-byte against the 2.15.3 release's visual/dist assets.
    # Pin upstream bytes, not a digest generated from Tau during the test:
    # reference comparisons must not silently drift with local CSS edits.
    expected = {
        "piclaw-reference.css": "50e8f293f4553cae89a383b2c35497c0a31c442a734ff38e858d7d3244e007ad",
        "JetBrainsMonoNFM-Medium-hh38vnv1.woff2": "e9d33faabc0c688c5b417d5b5e40e874edaf232bfa553fc504f1bce99b872d03",
        "JetBrainsMonoNFM-Regular-rhdb9m6d.woff2": "3154cf51aa75c0aa9f6ed786a539b04624297da2d95ea322d5bf38cbfc82bbb0",
        "firacode-nerd-font-mono-bold-v7nf8tpn.ttf": "bd014a21f3cd64203dd0850437091d716e929a4518b0e5848d6d3ad6af12b21d",
        "firacode-nerd-font-mono-regular-f4sytzp8.ttf": "ad88c69cb6a497db9f2714e4b414817aabbee621484a1560bfdb3fd73abdd564",
    }
    static_root = build_backend.ROOT / "src" / "tau_web" / "static"
    for name, digest in expected.items():
        assert hashlib.sha256((static_root / name).read_bytes()).hexdigest() == digest, name


def test_classic_reference_assets_are_pinned_and_packaged(tmp_path: Path) -> None:
    static_root = build_backend.ROOT / "src" / "tau_web" / "static"
    css_bytes = (static_root / "piclaw-classic.css").read_bytes()
    assert hashlib.sha256(css_bytes).hexdigest() == "632b049f34a164f73b4f2a379d4bfc4ee76327955b32331c9af6db28281b0ab6"
    fonts = set(re.findall(r"url\(\./([^)]*)\)", css_bytes.decode()))
    assert fonts == {"firacode-nerd-font-mono-bold-v7nf8tpn.ttf", "firacode-nerd-font-mono-regular-f4sytzp8.ttf"}
    wheel_name = build_backend.build_wheel(str(tmp_path))
    with zipfile.ZipFile(tmp_path / wheel_name) as archive:
        for name in fonts | {"piclaw-classic.css"}:
            assert archive.read(f"tau_web/static/{name}") == (static_root / name).read_bytes()


def test_built_wheel_preserves_piclaw_css_and_font_bytes(tmp_path: Path) -> None:
    wheel_name = build_backend.build_wheel(str(tmp_path))
    static_root = build_backend.ROOT / "src" / "tau_web" / "static"
    css = (static_root / "piclaw-reference.css").read_text(encoding="utf-8")
    font_names = set(re.findall(r"url\(\./([^)]*)\)", css))
    assert len(font_names) == 4
    with zipfile.ZipFile(tmp_path / wheel_name, "r") as archive:
        for name in sorted(font_names | {"piclaw-reference.css", "PICLAW-LICENSE.md", "FONT-LICENSES.md"}):
            assert archive.read(f"tau_web/static/{name}") == (static_root / name).read_bytes()


def test_wheel_includes_preact_frontend_sources() -> None:
    archive_names = {archive_name for _, archive_name in build_backend._package_files()}

    for expected in (
        "tau_web/frontend/README.md",
        "tau_web/frontend/build.ts",
        "tau_web/frontend/package.json",
        "tau_web/frontend/src/index.tsx",
        "tau_web/frontend/tsconfig.json",
    ):
        assert expected in archive_names


def test_wheel_excludes_dependency_and_cache_trees() -> None:
    archive_names = {archive_name for _, archive_name in build_backend._package_files()}

    forbidden_parts = {
        ".cache",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "node_modules",
    }
    assert not any(forbidden_parts.intersection(Path(name).parts) for name in archive_names)


def test_wheel_declares_tau_console_script(tmp_path: Path) -> None:
    wheel_name = build_backend.build_wheel(str(tmp_path))
    dist_info = build_backend._dist_info_name()

    with zipfile.ZipFile(tmp_path / wheel_name, "r") as archive:
        entry_points = archive.read(f"{dist_info}/entry_points.txt").decode("utf-8")

    assert "[console_scripts]" in entry_points
    assert "tau = tau_coding.cli:app" in entry_points
