from __future__ import annotations

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

    assert "tau_extensions/__init__.py" in archive_names
    assert "tau_extensions/builtin/diagnostic/__init__.py" in archive_names
    assert "tau_extensions/builtin/diagnostic/extension.py" in archive_names
    assert "tau_extensions/builtin/diagnostic/tau-extension.json" in archive_names
    assert "tau_extensions/web/__init__.py" in archive_names
    assert "tau_web/__init__.py" in archive_names
    assert "tau_web/app.py" in archive_names
    assert "tau_web/config.py" in archive_names
    assert "tau_web/middleware.py" in archive_names


def test_wheel_includes_frontend_static_assets() -> None:
    archive_names = {archive_name for _, archive_name in build_backend._package_files()}

    assert "tau_web/static/index.html" in archive_names
    assert "tau_web/static/app.css" in archive_names
    assert "tau_web/static/app.js" in archive_names
    assert "tau_web/static/extension-ui.js" in archive_names
    assert "tau_web/static/manifest.webmanifest" in archive_names
    assert "tau_web/static/sw.js" in archive_names
