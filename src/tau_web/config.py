"""Configuration for Tau's optional browser runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from tau_coding.paths import TauPaths

DEFAULT_WEB_HOST = "127.0.0.1"
DEFAULT_WEB_PORT = 8080
DEFAULT_MAX_REQUEST_BYTES = 16 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class WebConfig:
    """Validated host configuration with safe local defaults."""

    cwd: Path = field(default_factory=Path.cwd)
    host: str = DEFAULT_WEB_HOST
    port: int = DEFAULT_WEB_PORT
    database_path: Path | None = None
    max_request_bytes: int = DEFAULT_MAX_REQUEST_BYTES
    max_active_runs: int = 4

    def __post_init__(self) -> None:
        cwd = self.cwd.expanduser().resolve()
        database_path = self.database_path or TauPaths().home / "tau.sqlite3"
        database_path = database_path.expanduser().resolve()
        host = self.host.strip()

        if not host:
            raise ValueError("Web host must not be empty")
        if not 1 <= self.port <= 65535:
            raise ValueError("Web port must be between 1 and 65535")
        if self.max_request_bytes <= 0:
            raise ValueError("Maximum request size must be positive")
        if self.max_active_runs <= 0:
            raise ValueError("Maximum active runs must be positive")

        object.__setattr__(self, "cwd", cwd)
        object.__setattr__(self, "host", host)
        object.__setattr__(self, "database_path", database_path)
