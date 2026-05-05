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
