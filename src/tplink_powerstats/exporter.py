from aiohttp import web
from prometheus_client import generate_latest

from .collector import Collector


class Exporter:

    def __init__(self) -> None:

        self.collectors: dict[str, Collector] = {}

    async def get_collector(self, target: str, username: str, password: str) -> Collector:
        if target not in self.collectors:
            self.collectors[target] = Collector(target, username, password)
        return self.collectors[target]

    async def collect(self, request: web.Request) -> web.Response:
        target = request.query.get("target")
        username = request.query.get("username")
        password = request.query.get("password")
        if not target or not username or not password:
            return web.Response(
                body="'target', 'username' and 'password' parameters must be specified",
                status=400,
            )

        device = await self.get_collector(target, username, password)
        await device.update_metrics()

        return web.Response(body=generate_latest(device.get_registry()),
                            headers={"Content-Type": "text/plain"})
