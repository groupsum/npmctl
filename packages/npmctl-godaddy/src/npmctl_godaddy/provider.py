"""npmctl DNS provider implementation for GoDaddy."""

from __future__ import annotations

from npmctl_godaddy.client import GoDaddyClient
from npmctl_godaddy.config import GoDaddyConfig


class GoDaddyDnsProvider:
    """DNS provider backed by the GoDaddy Domains API."""

    name = "godaddy"

    def __init__(self, client: GoDaddyClient | None = None) -> None:
        self._client = client

    @property
    def client(self) -> GoDaddyClient:
        if self._client is None:
            self._client = GoDaddyClient(GoDaddyConfig.from_env())
        return self._client

    def zones(self) -> tuple[str, ...]:
        return self.client.zones()

    def records(self, zone: str) -> tuple[dict[str, object], ...]:
        return tuple(record.to_dict() for record in self.client.records(zone))
