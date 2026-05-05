from __future__ import annotations

from npmctl.loader import load_desired_state
from npmctl.models import ExistingResource, ExistingState, ResourceKind
from npmctl.planner import PlannerOptions, compute_plan
from npmctl.schema import Capabilities


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
        hsts_enabled=None,
        hsts_subdomains=None,
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
