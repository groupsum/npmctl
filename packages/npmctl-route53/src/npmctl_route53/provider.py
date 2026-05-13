"""npmctl DNS provider implementation for Route 53."""

from __future__ import annotations

from npmctl_route53.client import Route53Client
from npmctl_route53.config import Route53Config


class Route53DnsProvider:
    """DNS provider backed by AWS Route 53."""

    name = "route53"

    def __init__(self, client: Route53Client | None = None) -> None:
        self._client = client

    @property
    def client(self) -> Route53Client:
        if self._client is None:
            self._client = Route53Client(Route53Config.from_env())
        return self._client

    def zones(self) -> tuple[str, ...]:
        return self.client.zones()

    def records(self, zone: str) -> tuple[dict[str, object], ...]:
        return tuple(record.to_dict() for record in self.client.records(zone))
