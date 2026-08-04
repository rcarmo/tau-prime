"""aiohttp application entry points for Tau Web."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, cast

from tau_web.config import WebConfig

CONFIG_KEY = "tau.web.config"
SERVICES_KEY = "tau.web.services"


async def _services_context(app: Any) -> AsyncIterator[None]:
    from tau_web.services import TauWebServices

    config = cast(WebConfig, app._state[CONFIG_KEY])
    services = await TauWebServices.open(config)
    app._state[SERVICES_KEY] = services
    try:
        yield
    finally:
        try:
            await services.close()
        finally:
            app._state.pop(SERVICES_KEY, None)


def create_app(config: WebConfig | None = None) -> Any:
    """Create the web application without importing aiohttp at package import time."""
    try:
        from aiohttp import web
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Tau Web dependencies are not installed; install 'tau-prime[web]'"
        ) from exc

    from tau_web.middleware import build_middlewares

    active_config = config or WebConfig()
    app = web.Application(
        client_max_size=active_config.max_request_bytes,
        middlewares=build_middlewares(active_config),
    )
    app._state[CONFIG_KEY] = active_config
    app.cleanup_ctx.append(_services_context)

    async def health(request: Any) -> Any:
        payload: dict[str, str | int] = {"status": "ok", "service": "tau-web"}
        services = cast(Any, request.app._state.get(SERVICES_KEY))
        if services is not None:
            payload["database"] = "ready"
            payload["recovered_runs"] = services.database.recovered_run_count
        return web.json_response(payload)

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
