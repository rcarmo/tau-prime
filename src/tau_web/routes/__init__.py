"""HTTP route modules for Tau Web."""

from __future__ import annotations

from typing import Any


def setup_routes(app: Any) -> None:
    """Register Tau Web routes without importing aiohttp at package import time."""
    from tau_web.routes.runs import setup_routes as setup_run_routes
    from tau_web.routes.sessions import setup_routes as setup_session_routes

    setup_session_routes(app)
    setup_run_routes(app)
