"""HTTP route modules for Tau Web."""

from __future__ import annotations

from typing import Any


def setup_routes(app: Any) -> None:
    """Register Tau Web routes without importing aiohttp at package import time."""
    from tau_web.routes.assets import setup_routes as setup_asset_routes
    from tau_web.routes.events import setup_routes as setup_event_routes
    from tau_web.routes.extensions import setup_routes as setup_extension_routes
    from tau_web.routes.frontend import setup_routes as setup_frontend_routes
    from tau_web.routes.metadata import setup_routes as setup_metadata_routes
    from tau_web.routes.meters import setup_routes as setup_meter_routes
    from tau_web.routes.runs import setup_routes as setup_run_routes
    from tau_web.routes.sessions import setup_routes as setup_session_routes
    from tau_web.routes.timeline import setup_routes as setup_timeline_routes

    setup_session_routes(app)
    setup_timeline_routes(app)
    setup_run_routes(app)
    setup_metadata_routes(app)
    setup_meter_routes(app)
    setup_asset_routes(app)
    setup_event_routes(app)
    setup_extension_routes(app)
    setup_frontend_routes(app)
