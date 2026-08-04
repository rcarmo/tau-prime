"""aiohttp application entry points for Tau Web."""

from __future__ import annotations

from typing import Any

from tau_web.config import WebConfig


def create_app(config: WebConfig | None = None) -> Any:
    """Create the web application without importing aiohttp at package import time."""
    try:
        from aiohttp import web  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Tau Web dependencies are not installed; install 'tau-prime[web]'"
        ) from exc

    active_config = config or WebConfig()
    app = web.Application(client_max_size=active_config.max_request_bytes)
    app["tau.web.config"] = active_config

    async def health(_: Any) -> Any:
        return web.json_response({"status": "ok", "service": "tau-web"})

    app.router.add_get("/api/health", health)
    return app


def run(config: WebConfig | None = None) -> None:
    """Run Tau Web until interrupted."""
    try:
        from aiohttp import web
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Tau Web dependencies are not installed; install 'tau-prime[web]'"
        ) from exc

    active_config = config or WebConfig()
    web.run_app(create_app(active_config), host=active_config.host, port=active_config.port)
