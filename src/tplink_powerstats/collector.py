from __future__ import annotations

import datetime
import typing

import kasa
from prometheus_client import CollectorRegistry, Counter, Gauge


class Collector:

    def __init__(
        self,
        host: str,
        username: str = "",
        password: str = "",
    ) -> None:

        self.host = host
        self.username = username
        self.password = password
        self.dev: typing.Union[kasa.Device, None] = None
        self.setup_complete = False

        labels = ["alias", "device_id", "hw_ver", "sw_ver", "mac", "model"]

        self.registry = CollectorRegistry()

        self.tplink_current = Gauge(
            "tplink_current",
            "Current flowing through device in Ampere.",
            labels,
            registry=self.registry,
        )
        self.tplink_metadata = Gauge(
            "tplink_metadata",
            "Device metadata.",
            labels,
            registry=self.registry,
        )
        self.tplink_on_time = Counter(
            "tplink_on_time",
            "Time in seconds since online.",
            labels,
            registry=self.registry,
        )
        self.tplink_online = Gauge(
            "tplink_online",
            "Device online.",
            labels,
            registry=self.registry,
        )
        self.tplink_power_load = Gauge(
            "tplink_power_load",
            "Current power in Watt.",
            labels,
            registry=self.registry,
        )
        self.tplink_power_today = Gauge(
            "tplink_power_today",
            "Current power in kWh.",
            labels,
            registry=self.registry,
        )
        self.tplink_power_month = Gauge(
            "tplink_power_month",
            "Current power in kWh.",
            labels,
            registry=self.registry,
        )

        self.tplink_relay_state = Gauge(
            "tplink_relay_state",
            "Relay state (switch on/off).",
            labels,
            registry=self.registry,
        )
        self.tplink_rssi = Gauge(
            "tplink_rssi",
            "Wifi received signal strength indicator.",
            labels,
            registry=self.registry,
        )
        self.tplink_voltage = Gauge(
            "tplink_voltage",
            "Current voltage connected to device in Volt.",
            labels,
            registry=self.registry,
        )

    async def _setup(self) -> None:
        self.dev = await kasa.Discover.discover_single(self.host,
                                                       username=self.username,
                                                       password=self.password)

    async def _update(self) -> None:
        await self._setup()
        if self.dev:
            await self.dev.update()

    async def get(self) -> dict[str, typing.Any]:
        await self._update()

        if self.dev is None or not self.dev.has_emeter:
            return {}

        uptime = self.uptime(self.dev.state_information.get("On since"))

        return {
            "labels": {
                "alias": self.dev.alias,
                "device_id": self.dev.sys_info.get(
                    "device_id",
                    self.dev.sys_info.get("deviceId", ""),
                ),
                "hw_ver": self.dev.hw_info.get("hw_ver", ""),
                "sw_ver": self.dev.hw_info.get("sw_ver", ""),
                "mac": self.dev.hw_info.get("mac", ""),
                "model": self.dev.model,
            },
            "state": {
                "voltage": self._convert_to_number("Voltage"),
                "current": self._convert_to_number("Current"),
                "rssi": self._convert_to_number("RSSI"),
                "relay_state": self.dev.sys_info.get(
                    "relay_state",
                    1 if self.dev.sys_info.get("device_on") else 0,
                ),
                "metadata": 1,
                "online": 1 if self.dev.state_information.get("State") else 0,
                "on_time": uptime,
                "power_load": self._convert_to_number("Current consumption"),
                "power_today": self._convert_to_number("Today's consumption"),
                "power_month": self._convert_to_number("This month's consumption"),
            },
        }

    def _convert_to_number(self, label: str) -> float:
        if self.dev:
            raw_value = self.dev.state_information.get(label, None)
            if raw_value:
                return float(raw_value)
        return 0.0

    async def update_metrics(self) -> None:
        results = await self.get()
        labels = results["labels"]
        state = results["state"]

        self.tplink_current.labels(**labels).set(state["current"])
        self.tplink_metadata.labels(**labels).set(state["metadata"])
        self.tplink_on_time.labels(**labels).inc(state["on_time"])
        self.tplink_online.labels(**labels).set(state["online"])
        self.tplink_power_load.labels(**labels).set(state["power_load"])
        self.tplink_power_today.labels(**labels).set(state["power_today"])
        self.tplink_power_month.labels(**labels).set(state["power_month"])
        self.tplink_relay_state.labels(**labels).set(state["relay_state"])
        self.tplink_rssi.labels(**labels).set(state["rssi"])
        self.tplink_voltage.labels(**labels).set(state["voltage"])

    def get_registry(self) -> CollectorRegistry:
        return self.registry

    @staticmethod
    def uptime(on_since: typing.Optional[datetime.datetime]) -> float:
        if not on_since:
            return float(0)

        now = datetime.datetime.now(on_since.tzinfo)
        uptime = now - on_since
        return uptime.total_seconds()
