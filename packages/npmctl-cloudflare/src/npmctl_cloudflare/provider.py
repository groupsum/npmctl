"""npmctl DNS provider implementation for Cloudflare."""

from __future__ import annotations

from npmctl_cloudflare.client import CloudflareClient
from npmctl_cloudflare.config import CloudflareConfig


class CloudflareDnsProvider:
    """DNS provider backed by the Cloudflare DNS Records API."""

    name = "cloudflare"

    def __init__(self, client: CloudflareClient | None = None) -> None:
        self._client = client

    @property
    def client(self) -> CloudflareClient:
        if self._client is None:
            self._client = CloudflareClient(CloudflareConfig.from_env())
        return self._client

    def zones(self) -> tuple[str, ...]:
        return self.client.zones()

    def records(self, zone: str) -> tuple[dict[str, object], ...]:
        return tuple(record.to_dict() for record in self.client.records(zone))
