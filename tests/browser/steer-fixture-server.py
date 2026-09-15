"""Local browser fixture using installed Tau code and a gated, provider-free agent."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from aiohttp import web

from tau_agent import AgentEndEvent, AgentStartEvent, QueueUpdateEvent
from tau_web.app import SERVICES_KEY, create_app
from tau_web.config import WebConfig


class FixtureSession:
    def __init__(self) -> None:
        self.release = asyncio.Event()
        self.active = False

    async def prompt(self, prompt):
        self.active = True
        yield AgentStartEvent()
        try:
            await self.release.wait()
        finally:
            self.active = False
        yield AgentEndEvent()

    async def continue_run(self):
        async for event in self.prompt("continue"):
            yield event

    async def queue_message(self, content, *, behavior):
        if not self.active:
            raise RuntimeError("Fixture session is idle")
        return QueueUpdateEvent(
            steering=(content,) if behavior == "steer" else (),
            follow_up=(content,) if behavior == "follow_up" else (),
        )

    async def cancel(self):
        self.release.set()

    async def aclose(self):
        self.release.set()


async def main() -> None:
    with TemporaryDirectory(prefix="tau-steer-installed-") as root:
        app = create_app(
            WebConfig(
                cwd=Path(root),
                database_path=Path(root) / "test.sqlite3",
                auth_token=os.environ["TAU_BROWSER_TEST_AUTH_TOKEN"],
            )
        )
        runner = web.AppRunner(app)
        await runner.setup()
        try:
            services = app._state[SERVICES_KEY]
            await services.sessions.create(
                workspace_root=Path(root),
                provider_name="test",
                model="fixture",
                agent_name="fixture",
                session_id="steer-fixture",
            )
            services.runtime.register_session("steer-fixture", FixtureSession())
            await web.TCPSite(
                runner, "127.0.0.1", int(os.environ.get("TAU_BROWSER_PORT", "8894"))
            ).start()
            await asyncio.Event().wait()
        finally:
            await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
