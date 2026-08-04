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
    assert config.auth_token is None
    assert config.allowed_origins == ()


def test_web_config_normalizes_auth_token_and_allowed_origins(tmp_path: Path) -> None:
    config = WebConfig(
        cwd=tmp_path,
        auth_token="  secret-token  ",
        allowed_origins=(
            " HTTPS://Example.com:443/ ",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:8080/",
        ),
    )

    assert config.auth_token == "secret-token"
    assert config.allowed_origins == ("https://example.com", "http://127.0.0.1:8080")
    assert "secret-token" not in repr(config)


@pytest.mark.parametrize("port", [0, 65536])
def test_web_config_rejects_invalid_port(tmp_path: Path, port: int) -> None:
    with pytest.raises(ValueError, match="port"):
        WebConfig(cwd=tmp_path, port=port)


def test_web_config_rejects_empty_host(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="host"):
        WebConfig(cwd=tmp_path, host="  ")


@pytest.mark.parametrize("auth_token", ["", "   "])
def test_web_config_rejects_blank_auth_token(tmp_path: Path, auth_token: str) -> None:
    with pytest.raises(ValueError, match="auth token"):
        WebConfig(cwd=tmp_path, auth_token=auth_token)


@pytest.mark.parametrize(
    ("origin", "message"),
    [
        ("", "blank"),
        ("ftp://example.com", "http or https"),
        ("/relative", "absolute"),
        ("https://example.com/path", "path"),
        ("https://example.com?query=1", "query strings or fragments"),
    ],
)
def test_web_config_rejects_invalid_allowed_origin(
    tmp_path: Path,
    origin: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        WebConfig(cwd=tmp_path, allowed_origins=(origin,))


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
