import asyncio
import contextlib

from aiohttp import web
from prometheus_client import (
    CollectorRegistry,
    PlatformCollector,
    ProcessCollector,
    generate_latest,
)

from .exporter import Exporter


class DefaultExporter:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        PlatformCollector(registry=self.registry)
        ProcessCollector(registry=self.registry)

    async def collect(self, request: web.Request) -> web.Response:  # noqa: ARG002
        return web.Response(
            body=generate_latest(self.registry),
            headers={"Content-Type": "text/plain"},
        )


async def main() -> None:

    custom_exporter = Exporter()
    default_exporter = DefaultExporter()

    app = web.Application()
    app.router.add_get("/scrape", custom_exporter.collect)
    app.router.add_get("/metrics", default_exporter.collect)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 9101)  # noqa: S104
    await site.start()

    done = asyncio.Event()
    await done.wait()   # Sleep forever


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
