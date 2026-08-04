"""Tau's optional browser runtime.

Importing this package must not import optional web dependencies. Applications
should call :func:`tau_web.app.create_app` only after installing ``tau-prime[web]``.
"""

from tau_web.config import WebConfig

__all__ = ["WebConfig"]
