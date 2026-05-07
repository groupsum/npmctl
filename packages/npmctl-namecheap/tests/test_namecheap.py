from __future__ import annotations

import pytest

from npmctl_namecheap.client import NamecheapClient
from npmctl_namecheap.config import NamecheapConfig
from npmctl_namecheap.errors import NamecheapError
from npmctl_namecheap.models import NamecheapRecord, split_zone
from npmctl_namecheap.provider import NamecheapDnsProvider


class FakeResponse:
    def __init__(self, status_code: int, text: str) -> None:
        self.status_code = status_code
        self.text = text


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def get(self, url: str, **kwargs) -> FakeResponse:
        self.calls.append({"url": url, **kwargs})
        return self.responses.pop(0)


def _config() -> NamecheapConfig:
    return NamecheapConfig(
        api_user="api-user",
        api_key="api-key",
        username="username",
        client_ip="192.0.2.10",
        api_base_url="https://namecheap.test/xml.response",
    )


def test_config_from_env_and_redaction() -> None:
    config = NamecheapConfig.from_env(
        {
            "NAMECHEAP_API_USER": "api-user",
            "NAMECHEAP_API_KEY": "api-key",
            "NAMECHEAP_USERNAME": "username",
            "NAMECHEAP_CLIENT_IP": "192.0.2.10",
        }
    )

    assert config.redacted()["api_key"] is True
    assert config.api_base_url == "https://api.namecheap.com/xml.response"


def test_config_requires_credentials() -> None:
    with pytest.raises(ValueError, match="missing Namecheap config"):
        NamecheapConfig.from_env({})


def test_split_zone_and_record_parsing() -> None:
    assert split_zone("Example.Com.") == ("example", "com")
    with pytest.raises(ValueError, match="zone must be"):
        split_zone("localhost")

    record = NamecheapRecord.from_attrs(
        {"HostId": "10", "Name": "WWW", "Type": "a", "Address": "192.0.2.10", "TTL": "300", "MXPref": ""}
    )

    assert record.to_dict() == {
        "id": "10",
        "name": "www",
        "type": "A",
        "value": "192.0.2.10",
        "ttl": 300,
        "priority": None,
    }


def test_client_lists_zones_and_records() -> None:
    client = NamecheapClient(_config())
    session = FakeSession(
        [
            FakeResponse(
                200,
                """<?xml version="1.0" encoding="utf-8"?>
                <ApiResponse Status="OK" xmlns="http://api.namecheap.com/xml.response">
                  <CommandResponse>
                    <DomainGetListResult>
                      <Domain Name="example.com" />
                    </DomainGetListResult>
                  </CommandResponse>
                </ApiResponse>""",
            ),
            FakeResponse(
                200,
                """<?xml version="1.0" encoding="utf-8"?>
                <ApiResponse Status="OK" xmlns="http://api.namecheap.com/xml.response">
                  <CommandResponse>
                    <DomainDNSGetHostsResult>
                      <host HostId="1" Name="@" Type="A" Address="192.0.2.10" TTL="300" />
                    </DomainDNSGetHostsResult>
                  </CommandResponse>
                </ApiResponse>""",
            ),
        ]
    )
    client.session = session  # type: ignore[assignment]

    assert client.zones() == ("example.com",)
    assert client.records("example.com")[0].address == "192.0.2.10"
    assert session.calls[0]["params"]["Command"] == "namecheap.domains.getList"  # type: ignore[index]
    assert session.calls[1]["params"]["SLD"] == "example"  # type: ignore[index]


def test_client_reports_http_api_and_xml_errors() -> None:
    client = NamecheapClient(_config())
    client.session = FakeSession([FakeResponse(500, "broken")])  # type: ignore[assignment]
    with pytest.raises(NamecheapError, match="HTTP 500"):
        client.zones()

    client.session = FakeSession([FakeResponse(200, "<not xml")])  # type: ignore[assignment]
    with pytest.raises(NamecheapError, match="invalid XML"):
        client.zones()

    client.session = FakeSession(
        [
            FakeResponse(
                200,
                """<ApiResponse Status="ERROR" xmlns="http://api.namecheap.com/xml.response">
                <Errors><Error>denied</Error></Errors>
                </ApiResponse>""",
            )
        ]
    )  # type: ignore[assignment]
    with pytest.raises(NamecheapError, match="denied"):
        client.zones()


def test_provider_returns_record_dicts() -> None:
    class Client:
        def zones(self):
            return ("example.com",)

        def records(self, zone: str):
            assert zone == "example.com"
            return (NamecheapRecord.from_attrs({"Name": "@", "Type": "A", "Address": "192.0.2.10"}),)

    provider = NamecheapDnsProvider(Client())  # type: ignore[arg-type]

    assert provider.zones() == ("example.com",)
    assert provider.records("example.com")[0]["value"] == "192.0.2.10"
