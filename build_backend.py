"""Tiny PEP 517 backend for Tau sdists/wheels.

This backend intentionally has no third-party dependencies so source tarballs can
be installed by pip in restricted Python 3.13 environments that cannot download
or import build backends such as hatchling/setuptools.
"""

from __future__ import annotations

import base64
import csv
import gzip
import hashlib
import io
import os
import tarfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

ROOT = Path(__file__).resolve().parent
ZIP_EPOCH = 315532800  # 1980-01-01T00:00:00Z (minimum for ZIP timestamps)


def _project() -> dict[str, Any]:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]


def _dist_name() -> str:
    return str(_project()["name"]).replace("-", "_")


def _version() -> str:
    return str(_project()["version"])


def _dist_info_name() -> str:
    return f"{_dist_name()}-{_version()}.dist-info"


def _source_date_epoch() -> int | None:
    value = os.environ.get("SOURCE_DATE_EPOCH")
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return max(parsed, 0)


def _build_mtime() -> int:
    epoch = _source_date_epoch()
    if epoch is None:
        return ZIP_EPOCH
    return epoch


def _zip_timestamp(epoch: int) -> tuple[int, int, int, int, int, int]:
    effective_epoch = max(epoch, ZIP_EPOCH)
    dt = datetime.fromtimestamp(effective_epoch, tz=UTC)
    return dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second


def _file_mode(path: Path) -> int:
    mode = path.stat().st_mode & 0o777
    if mode == 0:
        return 0o644
    return mode


def _metadata_text() -> str:
    project = _project()
    lines = [
        "Metadata-Version: 2.4",
        f"Name: {project['name']}",
        f"Version: {project['version']}",
        f"Summary: {project.get('description', '')}",
    ]
    if project.get("requires-python"):
        lines.append(f"Requires-Python: {project['requires-python']}")
    license_value = project.get("license")
    if isinstance(license_value, str):
        lines.append(f"License-Expression: {license_value}")
    urls = project.get("urls", {})
    for label, url in urls.items():
        lines.append(f"Project-URL: {label}, {url}")
    for dependency in project.get("dependencies", []):
        lines.append(f"Requires-Dist: {dependency}")
    for extra, dependencies in project.get("optional-dependencies", {}).items():
        lines.append(f"Provides-Extra: {extra}")
        for dependency in dependencies:
            separator = " and " if ";" in dependency else "; "
            lines.append(f'Requires-Dist: {dependency}{separator}extra == "{extra}"')
    readme = ROOT / str(project.get("readme", "README.md"))
    if readme.exists():
        lines.append("Description-Content-Type: text/markdown")
        lines.append("")
        lines.append(readme.read_text(encoding="utf-8"))
    else:
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _wheel_text() -> str:
    return "\n".join(
        [
            "Wheel-Version: 1.0",
            "Generator: tau-build-backend",
            "Root-Is-Purelib: true",
            "Tag: py3-none-any",
            "",
        ]
    )


def _entry_points_text() -> str:
    scripts = _project().get("scripts", {})
    if not scripts:
        return ""
    lines = ["[console_scripts]"]
    for name, target in scripts.items():
        lines.append(f"{name} = {target}")
    return "\n".join(lines) + "\n"


def _hash(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    return "sha256=" + base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _is_excluded_source(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    parts = relative.parts
    if any(part in {".venv", "__pycache__", "pycache", "node_modules"} for part in parts):
        return True
    generated_prefixes = (
        ("website", ".astro"),
        ("website", "dist"),
    )
    if any(parts[: len(prefix)] == prefix for prefix in generated_prefixes):
        return True
    if relative.name == ".env" or relative.name.startswith(".env."):
        return True
    browser_excluded_prefixes = (
        ("tests", "browser", "node_modules"),
        ("tests", "browser", "test-results"),
        ("tests", "browser", "playwright-report"),
        ("tests", "browser", ".cache"),
    )
    return any(parts[: len(prefix)] == prefix for prefix in browser_excluded_prefixes)


def _source_files() -> list[Path]:
    include_roots = ["src", "tests", "website", "dev-notes", "docs"]
    include_files = [
        "AGENTS.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "Makefile",
        "README.md",
        "build_backend.py",
        "pyproject.toml",
        "requirements.txt",
        "requirements-dev.txt",
    ]
    files: list[Path] = []
    for name in include_files:
        path = ROOT / name
        if path.is_file():
            files.append(path)
    for name in include_roots:
        root = ROOT / name
        if not root.exists():
            continue
        files.extend(
            path for path in root.rglob("*") if path.is_file() and not _is_excluded_source(path)
        )
    return sorted(files)


def _package_files() -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    src = ROOT / "src"
    shim = src / "pydantic.py"
    if shim.exists():
        files.append((shim, "pydantic.py"))
    package_data_suffixes = {
        ".md",
        ".html",
        ".css",
        ".js",
        ".json",
        ".ts",
        ".tsx",
        ".webmanifest",
        ".svg",
        ".png",
    }
    for package in ("tau_ai", "tau_agent", "tau_coding", "tau_extensions", "tau_web"):
        package_root = src / package
        for path in package_root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix == ".py" or path.suffix in package_data_suffixes:
                files.append((path, path.relative_to(src).as_posix()))
    return sorted(files, key=lambda item: item[1])


def _tar_info(arcname: str, data: bytes, mode: int, mtime: int) -> tarfile.TarInfo:
    info = tarfile.TarInfo(arcname)
    info.size = len(data)
    info.mode = mode
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = mtime
    return info


def prepare_metadata_for_build_wheel(
    metadata_directory: str, config_settings: dict[str, Any] | None = None
) -> str:
    del config_settings
    dist_info = Path(metadata_directory) / _dist_info_name()
    dist_info.mkdir(parents=True, exist_ok=True)
    (dist_info / "METADATA").write_text(_metadata_text(), encoding="utf-8")
    (dist_info / "WHEEL").write_text(_wheel_text(), encoding="utf-8")
    entry_points = _entry_points_text()
    if entry_points:
        (dist_info / "entry_points.txt").write_text(entry_points, encoding="utf-8")
    (dist_info / "RECORD").write_text("", encoding="utf-8")
    return dist_info.name


def build_wheel(
    wheel_directory: str,
    config_settings: dict[str, Any] | None = None,
    metadata_directory: str | None = None,
) -> str:
    del config_settings, metadata_directory
    wheel_name = f"{_dist_name()}-{_version()}-py3-none-any.whl"
    wheel_path = Path(wheel_directory) / wheel_name
    records: list[tuple[str, str, str]] = []
    build_mtime = _build_mtime()
    zip_timestamp = _zip_timestamp(build_mtime)

    def write(
        zf: zipfile.ZipFile,
        arcname: str,
        data: bytes,
        mode: int = 0o644,
        *,
        record: bool = True,
    ) -> None:
        info = zipfile.ZipInfo(arcname, date_time=zip_timestamp)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = (mode & 0o777) << 16
        info.create_system = 3
        zf.writestr(info, data)
        if record:
            records.append((arcname, _hash(data), str(len(data))))

    dist_info = _dist_info_name()
    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, arcname in _package_files():
            write(zf, arcname, path.read_bytes(), mode=_file_mode(path))
        write(zf, f"{dist_info}/METADATA", _metadata_text().encode("utf-8"))
        write(zf, f"{dist_info}/WHEEL", _wheel_text().encode("utf-8"))
        entry_points = _entry_points_text()
        if entry_points:
            write(zf, f"{dist_info}/entry_points.txt", entry_points.encode("utf-8"))
        record_name = f"{dist_info}/RECORD"
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")
        for row in records:
            writer.writerow(row)
        writer.writerow((record_name, "", ""))
        write(zf, record_name, output.getvalue().encode("utf-8"), record=False)
    return wheel_name


def build_sdist(sdist_directory: str, config_settings: dict[str, Any] | None = None) -> str:
    del config_settings
    sdist_name = f"{_dist_name()}-{_version()}.tar.gz"
    sdist_path = Path(sdist_directory) / sdist_name
    prefix = f"{_dist_name()}-{_version()}"
    build_mtime = _build_mtime()

    with (
        sdist_path.open("wb") as raw,
        gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=build_mtime) as gzip_file,
        tarfile.open(fileobj=gzip_file, mode="w", format=tarfile.PAX_FORMAT) as tf,
    ):
        for path in _source_files():
            relative = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            info = _tar_info(
                f"{prefix}/{relative}",
                data,
                mode=_file_mode(path),
                mtime=build_mtime,
            )
            tf.addfile(info, io.BytesIO(data))
        pkg_info = _metadata_text().encode("utf-8")
        info = _tar_info(
            f"{prefix}/PKG-INFO",
            pkg_info,
            mode=0o644,
            mtime=build_mtime,
        )
        tf.addfile(info, io.BytesIO(pkg_info))
    return sdist_name


def get_requires_for_build_wheel(config_settings: dict[str, Any] | None = None) -> list[str]:
    del config_settings
    return []


def get_requires_for_build_sdist(config_settings: dict[str, Any] | None = None) -> list[str]:
    del config_settings
    return []
