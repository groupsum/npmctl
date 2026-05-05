from __future__ import annotations

from npmctl.loader import load_desired_state
from npmctl.models import (
    DesiredAccessList,
    DesiredCertificate,
    DesiredProxyHost,
    DesiredState,
    ExistingResource,
    ExistingState,
    ResourceKind,
)
from npmctl.planner import PlannerOptions, compute_plan
from npmctl.schema import Capabilities, ResourceCapabilities


def _existing_proxy(**overrides):
    raw = {
        "id": 10,
        "domain_names": ["app.example.com"],
        "forward_host": "app",
        "forward_port": 3000,
        "forward_scheme": "http",
        "access_list_id": 0,
        "certificate_id": 0,
        "ssl_forced": 1,
        "caching_enabled": 0,
        "block_exploits": 1,
        "advanced_config": "",
        "meta": {"managed_by": "npmctl", "owner": "workload-a", "resource_id": "proxy.app"},
        "allow_websocket_upgrade": 1,
        "http2_support": 1,
        "enabled": 1,
        "locations": [],
        "hsts_enabled": 0,
        "hsts_subdomains": 0,
        "use_default_location": True,
        "ipv6": True,
    }
    raw.update(overrides)
    return ExistingResource.from_proxy_host(raw)


def _existing_certificate(**overrides):
    raw = {
        "id": 11,
        "name": "wildcard-example",
        "nice_name": "wildcard-example",
        "domain_names": ["*.example.com", "example.com"],
        "certificate_type": "letsencrypt",
        "provider": "letsencrypt",
        "meta": {
            "managed_by": "npmctl",
            "owner": "workload-a",
            "resource_id": "cert.wildcard-example",
        },
    }
    raw.update(overrides)
    return ExistingResource.from_certificate(raw)


def _existing_access_list(**overrides):
    raw = {
        "id": 12,
        "name": "private-admins",
        "satisfy_any": 0,
        "items": [],
        "meta": {
            "managed_by": "npmctl",
            "owner": "workload-a",
            "resource_id": "acl.private-admins",
        },
    }
    raw.update(overrides)
    return ExistingResource.from_access_list(raw)


def test_plan_creates_missing_resources(desired_file) -> None:
    desired = load_desired_state(desired_file)
    plan = compute_plan(desired=desired, existing=ExistingState(), capabilities=Capabilities.full_for_tests())
    assert plan.ok
    assert len(plan.by_action("create")) == 3


def test_plan_updates_owned_drift(desired_file) -> None:
    desired = load_desired_state(desired_file)
    existing = ExistingState(proxy_hosts=(_existing_proxy(forward_port=8080),))
    plan = compute_plan(desired=desired, existing=existing, capabilities=Capabilities.full_for_tests())
    assert any(op.action == "update" and op.kind == ResourceKind.PROXY_HOST for op in plan.operations)
    assert any("forward_port" in op.diff for op in plan.operations if op.action == "update")


def test_plan_treats_omitted_proxy_defaults_as_converged(desired_file) -> None:
    desired = load_desired_state(desired_file)
    existing_proxy = _existing_proxy(
        access_list_id=None,
        certificate_id=None,
        advanced_config=None,
        caching_enabled="0",
        ssl_forced="1",
        hsts_enabled=None,
        hsts_subdomains=None,
        meta={
            "managed_by": "npmctl",
            "owner": "workload-a",
            "resource_id": "proxy.app",
            "nginx_online": True,
        },
    )
    existing_proxy.raw.pop("locations")
    plan = compute_plan(
        desired=desired,
        existing=ExistingState(
            proxy_hosts=(existing_proxy,),
            certificates=(_existing_certificate(),),
            access_lists=(_existing_access_list(),),
        ),
        capabilities=Capabilities.empty(),
    )

    assert plan.ok
    assert any(op.action == "noop" and op.kind == ResourceKind.PROXY_HOST for op in plan.operations)


def test_plan_conflicts_on_foreign_owner(desired_file) -> None:
    desired = load_desired_state(desired_file)
    existing = ExistingState(
        proxy_hosts=(
            _existing_proxy(meta={"managed_by": "npmctl", "owner": "workload-b", "resource_id": "proxy.other"}),
        )
    )
    plan = compute_plan(desired=desired, existing=existing, capabilities=Capabilities.full_for_tests())
    assert not plan.ok
    assert plan.conflicts[0].code == "foreign_owner"


def test_plan_conflicts_on_unmanaged_without_adopt(desired_file) -> None:
    desired = load_desired_state(desired_file)
    existing = ExistingState(proxy_hosts=(_existing_proxy(meta={}),))
    plan = compute_plan(desired=desired, existing=existing, capabilities=Capabilities.full_for_tests())
    assert not plan.ok
    assert plan.conflicts[0].code == "unmanaged_resource"


def test_plan_adopts_unmanaged_when_explicit(desired_file) -> None:
    desired = load_desired_state(desired_file)
    existing = ExistingState(proxy_hosts=(_existing_proxy(meta={}),))
    plan = compute_plan(
        desired=desired,
        existing=existing,
        capabilities=Capabilities.full_for_tests(),
        options=PlannerOptions(adopt=True, strict_adopt=True),
    )
    assert plan.ok
    assert any(op.action == "adopt" for op in plan.operations)


def test_plan_prunes_owned_absent_resources(desired_file) -> None:
    desired = load_desired_state(desired_file)
    existing = ExistingState(
        proxy_hosts=(
            _existing_proxy(
                domain_names=["old.example.com"],
                meta={"managed_by": "npmctl", "owner": "workload-a", "resource_id": "proxy.old"},
            ),
        )
    )
    plan = compute_plan(
        desired=desired,
        existing=existing,
        capabilities=Capabilities.full_for_tests(),
        options=PlannerOptions(prune_owned=True),
    )
    assert any(op.action == "delete" for op in plan.operations)


def test_plan_detects_missing_update_capability(desired_file) -> None:
    desired = load_desired_state(desired_file)
    existing = ExistingState(proxy_hosts=(_existing_proxy(forward_port=8080),))
    caps = Capabilities.empty()
    plan = compute_plan(desired=desired, existing=existing, capabilities=caps)
    assert any(conflict.code == "missing_update_capability" for conflict in plan.conflicts)


def test_plan_detects_duplicate_existing_non_proxy_identity() -> None:
    cert_a = _existing_certificate(id=20)
    cert_b = _existing_certificate(id=21, name="wildcard-example-copy")
    acl_a = _existing_access_list(id=30)
    acl_b = _existing_access_list(id=31, name="private-admins-copy")

    plan = compute_plan(
        desired=DesiredState(),
        existing=ExistingState(certificates=(cert_a, cert_b), access_lists=(acl_a, acl_b)),
        capabilities=Capabilities.full_for_tests(),
    )

    conflicts = [conflict for conflict in plan.conflicts if conflict.code == "duplicate_existing_resource_id"]
    assert {conflict.kind for conflict in conflicts} == {ResourceKind.CERTIFICATE, ResourceKind.ACCESS_LIST}


def test_plan_detects_duplicate_existing_proxy_domains() -> None:
    first = _existing_proxy(id=20)
    second = _existing_proxy(
        id=21,
        meta={"managed_by": "npmctl", "owner": "workload-b", "resource_id": "proxy.other"},
    )

    plan = compute_plan(
        desired=DesiredState(),
        existing=ExistingState(proxy_hosts=(first, second)),
        capabilities=Capabilities.full_for_tests(),
    )

    assert any(conflict.code == "duplicate_existing_domain" for conflict in plan.conflicts)


def test_plan_owner_filter_limits_multiple_desired_owners() -> None:
    desired = DesiredState(
        proxy_hosts=(
            DesiredProxyHost.from_mapping(
                {
                    "domain_names": ["a.example.com"],
                    "forward_host": "a",
                    "forward_port": 3000,
                    "meta": {"managed_by": "npmctl", "owner": "workload-a", "resource_id": "proxy.a"},
                },
                path="a",
            ),
            DesiredProxyHost.from_mapping(
                {
                    "domain_names": ["b.example.com"],
                    "forward_host": "b",
                    "forward_port": 3000,
                    "meta": {"managed_by": "npmctl", "owner": "workload-b", "resource_id": "proxy.b"},
                },
                path="b",
            ),
        )
    )

    plan = compute_plan(
        desired=desired,
        existing=ExistingState(),
        capabilities=Capabilities.full_for_tests(),
        options=PlannerOptions(owner="workload-a"),
    )

    assert plan.ok
    assert [operation.resource_id for operation in plan.operations] == ["proxy.a"]


def test_plan_prune_owned_only_targets_selected_owner() -> None:
    existing_a = _existing_proxy(
        domain_names=["a.example.com"],
        meta={"managed_by": "npmctl", "owner": "workload-a", "resource_id": "proxy.a"},
    )
    existing_b = _existing_proxy(
        id=11,
        domain_names=["b.example.com"],
        meta={"managed_by": "npmctl", "owner": "workload-b", "resource_id": "proxy.b"},
    )

    plan = compute_plan(
        desired=DesiredState(),
        existing=ExistingState(proxy_hosts=(existing_a, existing_b)),
        capabilities=Capabilities.full_for_tests(),
        options=PlannerOptions(owner="workload-a", prune_owned=True),
    )

    assert [operation.resource_id for operation in plan.by_action("delete")] == ["proxy.a"]


def test_plan_detects_certificate_and_access_list_identity_drift_and_foreign_ownership() -> None:
    desired = DesiredState(
        certificates=(
            DesiredCertificate.from_mapping(
                {
                    "name": "desired-cert",
                    "domain_names": ["example.com"],
                    "meta": {"managed_by": "npmctl", "owner": "workload-a", "resource_id": "cert.one"},
                },
                path="cert",
            ),
        ),
        access_lists=(
            DesiredAccessList.from_mapping(
                {
                    "name": "desired-acl",
                    "meta": {"managed_by": "npmctl", "owner": "workload-a", "resource_id": "acl.one"},
                },
                path="acl",
            ),
        ),
    )
    drifted_cert = _existing_certificate(
        id=44,
        name="old-cert",
        meta={"managed_by": "npmctl", "owner": "workload-a", "resource_id": "cert.one"},
    )
    foreign_acl = _existing_access_list(
        id=45,
        name="desired-acl",
        meta={"managed_by": "npmctl", "owner": "workload-b", "resource_id": "acl.other"},
    )

    plan = compute_plan(
        desired=desired,
        existing=ExistingState(certificates=(drifted_cert,), access_lists=(foreign_acl,)),
        capabilities=Capabilities.full_for_tests(),
    )

    assert any(
        conflict.code == "resource_id_drift" and conflict.kind == ResourceKind.CERTIFICATE
        for conflict in plan.conflicts
    )
    assert any(
        conflict.code == "foreign_owner" and conflict.kind == ResourceKind.ACCESS_LIST for conflict in plan.conflicts
    )


def test_plan_checks_partial_capabilities_by_resource_type() -> None:
    desired = DesiredState(
        certificates=(
            DesiredCertificate.from_mapping(
                {
                    "name": "cert-one",
                    "domain_names": ["example.com"],
                    "meta": {"managed_by": "npmctl", "owner": "workload-a", "resource_id": "cert.one"},
                },
                path="cert",
            ),
        ),
        access_lists=(
            DesiredAccessList.from_mapping(
                {
                    "name": "acl-one",
                    "meta": {"managed_by": "npmctl", "owner": "workload-a", "resource_id": "acl.one"},
                },
                path="acl",
            ),
        ),
        proxy_hosts=(
            DesiredProxyHost.from_mapping(
                {
                    "domain_names": ["app.example.com"],
                    "forward_host": "app",
                    "forward_port": 3000,
                    "meta": {"managed_by": "npmctl", "owner": "workload-a", "resource_id": "proxy.one"},
                },
                path="proxy",
            ),
        ),
    )
    caps = Capabilities(
        proxy_hosts=ResourceCapabilities(list=True, create=True),
        certificates=ResourceCapabilities(list=True, create=False),
        access_lists=ResourceCapabilities(list=True, create=False),
    )

    plan = compute_plan(desired=desired, existing=ExistingState(), capabilities=caps)

    assert [operation.kind for operation in plan.by_action("create")] == [ResourceKind.PROXY_HOST]
    assert {conflict.kind for conflict in plan.conflicts} == {ResourceKind.CERTIFICATE, ResourceKind.ACCESS_LIST}
