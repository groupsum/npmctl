from __future__ import annotations

from pathlib import Path

from npmctl.apply import ApplyEngine
from npmctl.client import NpmClient
from npmctl.loader import load_desired_state
from npmctl.planner import PlannerOptions, compute_plan


def _client(base_url: str) -> NpmClient:
    return NpmClient(base_url=base_url, identity="admin@example.com", secret="changeme", timeout_s=5)


def test_apply_full_stack_and_idempotent(fake_npm_server, desired_file: Path) -> None:
    _, base_url = fake_npm_server
    client = _client(base_url)
    desired = load_desired_state(desired_file)
    caps = client.capabilities()
    existing = client.existing_state(include_certificates=True, include_access_lists=True)
    plan = compute_plan(desired=desired, existing=existing, capabilities=caps)
    result = ApplyEngine(client=client, capabilities=caps).apply(plan)
    assert len(result.mutations) == 3

    second_existing = client.existing_state(include_certificates=True, include_access_lists=True)
    second_plan = compute_plan(desired=desired, existing=second_existing, capabilities=caps)
    assert second_plan.ok
    assert len(second_plan.by_action("create")) == 0
    assert len(second_plan.by_action("noop")) == 3


def test_update_owned_proxy_host(fake_npm_server, desired_file: Path) -> None:
    state, base_url = fake_npm_server
    state.create(
        "proxy_hosts",
        {
            "domain_names": ["app.example.com"],
            "forward_host": "app",
            "forward_port": 8080,
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
        },
    )
    client = _client(base_url)
    desired = load_desired_state(desired_file)
    caps = client.capabilities()
    plan = compute_plan(
        desired=desired,
        existing=client.existing_state(include_certificates=True, include_access_lists=True),
        capabilities=caps,
    )
    ApplyEngine(client=client, capabilities=caps).apply(plan)
    assert state.proxy_hosts[0]["forward_port"] == 3000


def test_adopt_unmanaged_proxy_host(fake_npm_server, desired_file: Path) -> None:
    state, base_url = fake_npm_server
    state.create(
        "proxy_hosts",
        {
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
            "meta": {},
            "allow_websocket_upgrade": 1,
            "http2_support": 1,
            "enabled": 1,
            "locations": [],
            "hsts_enabled": 0,
            "hsts_subdomains": 0,
            "use_default_location": True,
            "ipv6": True,
        },
    )
    client = _client(base_url)
    desired = load_desired_state(desired_file)
    caps = client.capabilities()
    plan = compute_plan(
        desired=desired,
        existing=client.existing_state(include_certificates=True, include_access_lists=True),
        capabilities=caps,
        options=PlannerOptions(adopt=True),
    )
    ApplyEngine(client=client, capabilities=caps).apply(plan)
    assert state.proxy_hosts[0]["meta"]["managed_by"] == "npmctl"


def test_cli_apply_and_plan_json(fake_npm_server, desired_file: Path, capsys) -> None:
    from npmctl.cli import main

    _, base_url = fake_npm_server
    code = main(
        [
            "--base-url",
            base_url,
            "--identity",
            "admin@example.com",
            "--secret",
            "changeme",
            "--output",
            "json",
            "apply",
            str(desired_file),
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert '"applied": true' in out
