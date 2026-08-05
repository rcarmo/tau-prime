import hashlib
import tarfile
from pathlib import Path

import build_backend


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_sdist_contains_makefile_and_docs(tmp_path: Path) -> None:
    filename = build_backend.build_sdist(str(tmp_path))

    with tarfile.open(tmp_path / filename, "r:gz") as archive:
        names = archive.getnames()

    assert any(name.endswith("/Makefile") for name in names)
    for required in (
        "/docs/architecture.md",
        "/docs/api.md",
        "/docs/examples.md",
        "/docs/storage.md",
        "/docs/web.md",
        "/docs/extensions.md",
    ):
        assert any(name.endswith(required) for name in names)

    for forbidden in (
        "/tests/browser/node_modules/",
        "/tests/browser/test-results/",
        "/tests/browser/playwright-report/",
        "/tests/browser/.cache/",
        "/.venv/",
        "/__pycache__/",
        "/pycache/",
    ):
        assert all(forbidden not in name for name in names)


def test_source_files_exclude_browser_artifacts_and_cache_dirs(
    tmp_path: Path, monkeypatch
) -> None:
    def write_text(relative: str) -> None:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("content", encoding="utf-8")

    write_text("src/module.py")
    write_text("tests/test_ok.py")
    write_text("docs/architecture.md")
    write_text("tests/browser/node_modules/pkg/index.js")
    write_text("tests/browser/test-results/results.json")
    write_text("tests/browser/playwright-report/index.html")
    write_text("tests/browser/.cache/cache.txt")
    write_text("tests/browser/.env.secret")
    write_text(".venv/bin/python")
    write_text("src/__pycache__/module.cpython-313.pyc")
    write_text("src/pycache/cache.dat")

    monkeypatch.setattr(build_backend, "ROOT", tmp_path)
    selected = {path.relative_to(tmp_path).as_posix() for path in build_backend._source_files()}

    assert "src/module.py" in selected
    assert "tests/test_ok.py" in selected
    assert "docs/architecture.md" in selected
    assert "tests/browser/node_modules/pkg/index.js" not in selected
    assert "tests/browser/test-results/results.json" not in selected
    assert "tests/browser/playwright-report/index.html" not in selected
    assert "tests/browser/.cache/cache.txt" not in selected
    assert "tests/browser/.env.secret" not in selected
    assert ".venv/bin/python" not in selected
    assert "src/__pycache__/module.cpython-313.pyc" not in selected
    assert "src/pycache/cache.dat" not in selected


def test_build_artifacts_are_deterministic_with_source_date_epoch(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1735689600")

    wheel_a = tmp_path / "wheel-a"
    wheel_b = tmp_path / "wheel-b"
    sdist_a = tmp_path / "sdist-a"
    sdist_b = tmp_path / "sdist-b"
    for directory in (wheel_a, wheel_b, sdist_a, sdist_b):
        directory.mkdir()

    wheel_name_a = build_backend.build_wheel(str(wheel_a))
    wheel_name_b = build_backend.build_wheel(str(wheel_b))
    sdist_name_a = build_backend.build_sdist(str(sdist_a))
    sdist_name_b = build_backend.build_sdist(str(sdist_b))

    assert wheel_name_a == wheel_name_b
    assert sdist_name_a == sdist_name_b
    assert _sha256(wheel_a / wheel_name_a) == _sha256(wheel_b / wheel_name_b)
    assert _sha256(sdist_a / sdist_name_a) == _sha256(sdist_b / sdist_name_b)
