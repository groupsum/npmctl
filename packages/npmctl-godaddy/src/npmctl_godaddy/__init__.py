"""GoDaddy DNS extension for npmctl."""

from npmctl_godaddy.client import GoDaddyClient
from npmctl_godaddy.config import GoDaddyConfig
from npmctl_godaddy.provider import GoDaddyDnsProvider

__all__ = ["GoDaddyClient", "GoDaddyConfig", "GoDaddyDnsProvider"]
