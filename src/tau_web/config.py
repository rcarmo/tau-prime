"""Configuration for Tau's optional browser runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from tau_coding.paths import TauPaths

DEFAULT_WEB_HOST = "127.0.0.1"
DEFAULT_WEB_PORT = 8080
DEFAULT_MAX_REQUEST_BYTES = 16 * 1024 * 1024
_ALLOWED_ORIGIN_SCHEMES = frozenset({"http", "https"})


def normalize_origin(origin: str) -> str:
    """Return a canonical HTTP(S) origin without paths, queries, or fragments."""
    normalized = origin.strip()
    if not normalized:
        raise ValueError("Web origins must not be blank")

    parts = urlsplit(normalized)
    if not parts.scheme or not parts.netloc:
        raise ValueError("Web origins must be absolute")

    scheme = parts.scheme.lower()
    if scheme not in _ALLOWED_ORIGIN_SCHEMES:
        raise ValueError("Web origins must use http or https")
    if parts.query or parts.fragment:
        raise ValueError("Web origins must not include query strings or fragments")
    if parts.path not in ("", "/"):
        raise ValueError("Web origins must not include a path")
    if parts.username is not None or parts.password is not None:
        raise ValueError("Web origins must not include user information")

    host = parts.hostname
    if host is None:
        raise ValueError("Web origins must be absolute")

    try:
        port = parts.port
    except ValueError as exc:
        raise ValueError("Web origins must include a valid port") from exc

    default_port = 80 if scheme == "http" else 443
    port_suffix = "" if port in (None, default_port) else f":{port}"
    host_text = f"[{host}]" if ":" in host else host
    return f"{scheme}://{host_text}{port_suffix}"


def normalize_auth_token(token: str | None) -> str | None:
    """Return a stripped auth token or ``None`` when auth is disabled."""
    if token is None:
        return None

    normalized = token.strip()
    if not normalized:
        raise ValueError("Web auth token must not be blank")
    return normalized


@dataclass(frozen=True, slots=True)
class WebConfig:
    """Validated host configuration with safe local defaults."""

    cwd: Path = field(default_factory=Path.cwd)
    host: str = DEFAULT_WEB_HOST
    port: int = DEFAULT_WEB_PORT
    database_path: Path | None = None
    auth_token: str | None = field(default=None, repr=False)
    allowed_origins: tuple[str, ...] = ()
    max_request_bytes: int = DEFAULT_MAX_REQUEST_BYTES
    max_active_runs: int = 4

    def __post_init__(self) -> None:
        cwd = self.cwd.expanduser().resolve()
        database_path = self.database_path or TauPaths().home / "tau.sqlite3"
        database_path = database_path.expanduser().resolve()
        host = self.host.strip()
        auth_token = normalize_auth_token(self.auth_token)
        allowed_origins = tuple(
            dict.fromkeys(normalize_origin(origin) for origin in self.allowed_origins)
        )

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
        object.__setattr__(self, "auth_token", auth_token)
        object.__setattr__(self, "allowed_origins", allowed_origins)
