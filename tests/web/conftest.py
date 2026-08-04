"""Shared Tau Web test fixtures."""

from pathlib import Path

import pytest

from tau_web.config import WebConfig


@pytest.fixture
def web_config(tmp_path: Path) -> WebConfig:
    return WebConfig(cwd=tmp_path, database_path=tmp_path / "tau.sqlite3")
