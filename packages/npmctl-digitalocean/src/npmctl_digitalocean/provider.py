"""npmctl DNS provider implementation for DigitalOcean."""

from __future__ import annotations

from npmctl_digitalocean.client import DigitalOceanClient
from npmctl_digitalocean.config import DigitalOceanConfig


class DigitalOceanDnsProvider:
    """DNS provider backed by the DigitalOcean Domain Records API."""

    name = "digitalocean"

    def __init__(self, client: DigitalOceanClient | None = None) -> None:
        self._client = client

    @property
    def client(self) -> DigitalOceanClient:
        if self._client is None:
            self._client = DigitalOceanClient(DigitalOceanConfig.from_env())
        return self._client

    def zones(self) -> tuple[str, ...]:
        return self.client.zones()

    def records(self, zone: str) -> tuple[dict[str, object], ...]:
        return tuple(record.to_dict() for record in self.client.records(zone))
