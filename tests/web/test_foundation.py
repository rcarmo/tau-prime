from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tau_web.config import DEFAULT_WEB_HOST, DEFAULT_WEB_PORT, WebConfig


def test_web_config_resolves_paths(tmp_path: Path) -> None:
    config = WebConfig(cwd=tmp_path / "..", database_path=tmp_path / "data" / "tau.sqlite3")

    assert config.cwd == (tmp_path / "..").resolve()
    assert config.database_path == (tmp_path / "data" / "tau.sqlite3").resolve()
    assert config.host == DEFAULT_WEB_HOST
    assert config.port == DEFAULT_WEB_PORT


@pytest.mark.parametrize("port", [0, 65536])
def test_web_config_rejects_invalid_port(tmp_path: Path, port: int) -> None:
    with pytest.raises(ValueError, match="port"):
        WebConfig(cwd=tmp_path, port=port)


def test_web_config_rejects_empty_host(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="host"):
        WebConfig(cwd=tmp_path, host="  ")


def test_web_package_import_does_not_load_optional_dependencies() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import tau_web; "
                "print('aiohttp' in sys.modules, 'aiosqlite' in sys.modules, "
                "'PIL' in sys.modules, 'pi_client' in sys.modules, "
                "'acp_client' in sys.modules)"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "False False False False False"
