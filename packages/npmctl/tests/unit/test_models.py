from __future__ import annotations

import pytest

from npmctl.errors import ValidationError
from npmctl.models import DesiredAccessList, DesiredCertificate, DesiredProxyHost, canonicalize_domain

META = {"managed_by": "npmctl", "owner": "workload-a", "resource_id": "res.one"}


def test_proxy_host_happy_path_normalizes_domains() -> None:
    host = DesiredProxyHost.from_mapping(
        {
            "domain_names": ["App.Example.Com.", "app.example.com"],
            "forward_host": "app",
            "forward_port": 3000,
            "meta": META,
            "use_default_location": False,
            "ipv6": False,
        },
        path="host",
    )
    payload = host.to_payload()

    assert host.domain_names == ("app.example.com",)
    assert payload["access_list_id"] == 0
    assert "use_default_location" not in payload
    assert "ipv6" not in payload


def test_proxy_host_rejects_conflicting_id_and_ref() -> None:
    with pytest.raises(ValidationError):
        DesiredProxyHost.from_mapping(
            {
                "domain_names": ["app.example.com"],
                "forward_host": "app",
                "forward_port": 3000,
                "access_list_id": 1,
                "access_list_ref": "acl.one",
                "meta": META,
            },
            path="host",
        )


@pytest.mark.parametrize("domain", ["*.example.com", "api.example.com"])
def test_valid_domains(domain: str) -> None:
    assert canonicalize_domain(domain, path="d") == domain


@pytest.mark.parametrize("domain", ["*", "example..com", "-bad.example.com", "bad_.example.com"])
def test_invalid_domains(domain: str) -> None:
    with pytest.raises(ValidationError):
        canonicalize_domain(domain, path="d")


def test_certificate_and_acl_models_accept_api_payload() -> None:
    cert = DesiredCertificate.from_mapping(
        {
            "name": "wildcard",
            "domain_names": ["*.example.com", "example.com"],
            "meta": META,
            "api_payload": {"provider": "letsencrypt"},
        },
        path="cert",
    )
    acl = DesiredAccessList.from_mapping({"name": "admins", "meta": META, "api_payload": {"items": []}}, path="acl")
    assert cert.to_payload()["provider"] == "letsencrypt"
    assert acl.to_payload()["items"] == []


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, 1),
        (False, 0),
        (1, 1),
        (0, 0),
    ],
)
def test_proxy_host_toggle_fields_accept_only_boolean_like_values(value, expected) -> None:
    host = DesiredProxyHost.from_mapping(
        {
            "domain_names": ["app.example.com"],
            "forward_host": "app",
            "forward_port": 3000,
            "meta": META,
            "ssl_forced": value,
            "caching_enabled": value,
            "block_exploits": value,
            "allow_websocket_upgrade": value,
            "http2_support": value,
            "hsts_enabled": value,
            "hsts_subdomains": value,
            "enabled": value,
        },
        path="host",
    )

    payload = host.to_payload()
    for field in (
        "ssl_forced",
        "caching_enabled",
        "block_exploits",
        "allow_websocket_upgrade",
        "http2_support",
        "hsts_enabled",
        "hsts_subdomains",
        "enabled",
    ):
        assert payload[field] == expected


@pytest.mark.parametrize("value", [2, -1, "1", None])
def test_proxy_host_toggle_fields_reject_invalid_values(value) -> None:
    with pytest.raises(ValidationError, match="ssl_forced"):
        DesiredProxyHost.from_mapping(
            {
                "domain_names": ["app.example.com"],
                "forward_host": "app",
                "forward_port": 3000,
                "meta": META,
                "ssl_forced": value,
            },
            path="host",
        )


@pytest.mark.parametrize("host", ["http://app", "app/path", "bad host", "bad$host"])
def test_proxy_host_rejects_invalid_forward_host_edges(host: str) -> None:
    with pytest.raises(ValidationError, match="forward_host"):
        DesiredProxyHost.from_mapping(
            {"domain_names": ["app.example.com"], "forward_host": host, "forward_port": 3000, "meta": META},
            path="host",
        )


@pytest.mark.parametrize("scheme", ["ftp", "", 1])
def test_proxy_host_rejects_invalid_forward_scheme(scheme) -> None:
    with pytest.raises(ValidationError, match="forward_scheme"):
        DesiredProxyHost.from_mapping(
            {
                "domain_names": ["app.example.com"],
                "forward_host": "app",
                "forward_port": 3000,
                "forward_scheme": scheme,
                "meta": META,
            },
            path="host",
        )


def test_proxy_host_rejects_invalid_locations_shape() -> None:
    with pytest.raises(ValidationError, match="locations"):
        DesiredProxyHost.from_mapping(
            {
                "domain_names": ["app.example.com"],
                "forward_host": "app",
                "forward_port": 3000,
                "locations": {"path": "/api"},
                "meta": META,
            },
            path="host",
        )


def test_proxy_host_rejects_invalid_advanced_config_shape() -> None:
    with pytest.raises(ValidationError, match="advanced_config"):
        DesiredProxyHost.from_mapping(
            {
                "domain_names": ["app.example.com"],
                "forward_host": "app",
                "forward_port": 3000,
                "advanced_config": ["bad"],
                "meta": META,
            },
            path="host",
        )


@pytest.mark.parametrize(
    ("model", "raw"),
    [
        (
            DesiredCertificate,
            {
                "name": "wildcard",
                "domain_names": ["example.com"],
                "meta": META,
                "api_payload": ["bad"],
            },
        ),
        (DesiredAccessList, {"name": "admins", "meta": META, "api_payload": "bad"}),
    ],
)
def test_certificate_and_access_list_reject_invalid_api_payload(model, raw) -> None:
    with pytest.raises(ValidationError, match="api_payload"):
        model.from_mapping(raw, path="resource")
