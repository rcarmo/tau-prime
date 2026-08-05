from __future__ import annotations

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


def test_wheel_declares_tau_console_script(tmp_path: Path) -> None:
    wheel_name = build_backend.build_wheel(str(tmp_path))
    dist_info = build_backend._dist_info_name()

    with zipfile.ZipFile(tmp_path / wheel_name, "r") as archive:
        entry_points = archive.read(f"{dist_info}/entry_points.txt").decode("utf-8")

    assert "[console_scripts]" in entry_points
    assert "tau = tau_coding.cli:app" in entry_points
