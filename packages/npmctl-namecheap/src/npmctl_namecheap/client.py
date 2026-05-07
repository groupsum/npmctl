"""Small Namecheap XML API client."""

from __future__ import annotations

from typing import Any
from xml.etree import ElementTree

import requests

from npmctl_namecheap.config import NamecheapConfig
from npmctl_namecheap.errors import NamecheapError
from npmctl_namecheap.models import NamecheapRecord, split_zone

_NAMESPACE = {"nc": "http://api.namecheap.com/xml.response"}


class NamecheapClient:
    """HTTP client for the Namecheap XML API."""

    def __init__(self, config: NamecheapConfig, *, timeout_s: float = 15.0) -> None:
        self.config = config
        self.timeout_s = timeout_s
        self.session = requests.Session()

    def zones(self) -> tuple[str, ...]:
        data = self._request("namecheap.domains.getList")
        domains = data.findall(".//nc:Domain", _NAMESPACE)
        return tuple(sorted(str(item.attrib["Name"]).lower() for item in domains if item.attrib.get("Name")))

    def records(self, zone: str) -> tuple[NamecheapRecord, ...]:
        sld, tld = split_zone(zone)
        data = self._request("namecheap.domains.dns.getHosts", SLD=sld, TLD=tld)
        hosts = data.findall(".//nc:host", _NAMESPACE)
        return tuple(NamecheapRecord.from_attrs(host.attrib) for host in hosts)

    def _request(self, command: str, **params: str) -> ElementTree.Element:
        query: dict[str, Any] = {
            "ApiUser": self.config.api_user,
            "ApiKey": self.config.api_key,
            "UserName": self.config.username,
            "ClientIp": self.config.client_ip,
            "Command": command,
            **params,
        }
        response = self.session.get(self.config.api_base_url, params=query, timeout=self.timeout_s)
        if response.status_code < 200 or response.status_code >= 300:
            raise NamecheapError(f"Namecheap API failed: HTTP {response.status_code}")
        try:
            parsed = ElementTree.fromstring(response.text)
        except ElementTree.ParseError as exc:
            raise NamecheapError("Namecheap API returned invalid XML") from exc
        if parsed.attrib.get("Status") == "ERROR":
            errors = [item.text or "unknown error" for item in parsed.findall(".//nc:Error", _NAMESPACE)]
            raise NamecheapError("; ".join(errors))
        return parsed
