from __future__ import annotations

import pytest

from npmctl.apply import ApplyEngine
from npmctl.errors import ApiError, ConflictError, ValidationError
from npmctl.models import (
    DesiredAccessList,
    DesiredCertificate,
    DesiredProxyHost,
    ExistingResource,
    PlanAction,
    ResourceKind,
)
from npmctl.planner import Plan, PlanConflict, PlanOperation
from npmctl.schema import Capabilities


def _meta(resource_id: str, owner: str = "workload-a") -> dict[str, str]:
    return {"managed_by": "npmctl", "owner": owner, "resource_id": resource_id}


def _cert(resource_id: str = "cert.one") -> DesiredCertificate:
    return DesiredCertificate.from_mapping(
        {
            "name": "cert-one",
            "domain_names": ["app.example.com"],
            "meta": _meta(resource_id),
            "api_payload": {"provider": "other"},
        },
        path="cert",
    )


def _acl(resource_id: str = "acl.one") -> DesiredAccessList:
    return DesiredAccessList.from_mapping(
        {"name": "acl-one", "meta": _meta(resource_id), "api_payload": {"items": [], "clients": []}},
        path="acl",
    )


def _proxy(
    resource_id: str = "proxy.one",
    *,
    certificate_ref: str | None = "cert.one",
    access_list_ref: str | None = "acl.one",
) -> DesiredProxyHost:
    raw = {
        "domain_names": ["app.example.com"],
        "forward_host": "app",
        "forward_port": 3000,
        "meta": _meta(resource_id),
        "certificate_ref": certificate_ref,
        "access_list_ref": access_list_ref,
    }
    return DesiredProxyHost.from_mapping(raw, path="proxy")


def _existing(kind: ResourceKind, resource_id: str, item_id: int, **overrides) -> ExistingResource:
    if kind == ResourceKind.CERTIFICATE:
        raw = {
            "id": item_id,
            "name": "cert-one",
            "domain_names": ["app.example.com"],
            "provider": "other",
            "meta": _meta(resource_id),
        }
        raw.update(overrides)
        return ExistingResource.from_certificate(raw)
    if kind == ResourceKind.ACCESS_LIST:
        raw = {"id": item_id, "name": "acl-one", "items": [], "clients": [], "meta": _meta(resource_id)}
        raw.update(overrides)
        return ExistingResource.from_access_list(raw)
    raw = {
        "id": item_id,
        "domain_names": ["app.example.com"],
        "forward_host": "app",
        "forward_port": 3000,
        "forward_scheme": "http",
        "meta": _meta(resource_id),
    }
    raw.update(overrides)
    return ExistingResource.from_proxy_host(raw)


class RecordingClient:
    def __init__(self, *, delete_ok: bool = True) -> None:
        self.events: list[tuple[str, ResourceKind, int | None, dict | None]] = []
        self.next_id = 100
        self.delete_ok = delete_ok

    def create_resource(self, kind: ResourceKind, payload: dict) -> ExistingResource:
        self.events.append(("create", kind, None, payload))
        self.next_id += 1
        raw = dict(payload) | {"id": self.next_id}
        if kind == ResourceKind.CERTIFICATE:
            return ExistingResource.from_certificate(raw)
        if kind == ResourceKind.ACCESS_LIST:
            return ExistingResource.from_access_list(raw)
        return ExistingResource.from_proxy_host(raw)

    def update_resource(
        self, kind: ResourceKind, resource_id: int, payload: dict, *, method: str = "put"
    ) -> ExistingResource:
        self.events.append((f"update:{method}", kind, resource_id, payload))
        raw = dict(payload) | {"id": resource_id}
        if kind == ResourceKind.CERTIFICATE:
            return ExistingResource.from_certificate(raw)
        if kind == ResourceKind.ACCESS_LIST:
            return ExistingResource.from_access_list(raw)
        return ExistingResource.from_proxy_host(raw)

    def delete_resource(self, kind: ResourceKind, resource_id: int) -> bool:
        self.events.append(("delete", kind, resource_id, None))
        return self.delete_ok


def _engine(client: RecordingClient) -> ApplyEngine:
    return ApplyEngine(client=client, capabilities=Capabilities.full_for_tests())


def test_apply_orders_dependencies_and_reverse_deletes() -> None:
    client = RecordingClient()
    old_cert = _existing(ResourceKind.CERTIFICATE, "cert.old", 1, name="old-cert")
    old_acl = _existing(ResourceKind.ACCESS_LIST, "acl.old", 2, name="old-acl")
    old_proxy = _existing(ResourceKind.PROXY_HOST, "proxy.old", 3, domain_names=["old.example.com"])
    plan = Plan(
        operations=(
            PlanOperation(PlanAction.DELETE, ResourceKind.CERTIFICATE, existing=old_cert),
            PlanOperation(PlanAction.CREATE, ResourceKind.PROXY_HOST, desired=_proxy()),
            PlanOperation(PlanAction.DELETE, ResourceKind.ACCESS_LIST, existing=old_acl),
            PlanOperation(PlanAction.CREATE, ResourceKind.ACCESS_LIST, desired=_acl()),
            PlanOperation(PlanAction.DELETE, ResourceKind.PROXY_HOST, existing=old_proxy),
            PlanOperation(PlanAction.CREATE, ResourceKind.CERTIFICATE, desired=_cert()),
        ),
        conflicts=(),
        existing_count=3,
    )

    result = _engine(client).apply(plan)

    assert [f"{event}:{kind.value}" for event, kind, _, _ in client.events] == [
        "create:certificate",
        "create:access_list",
        "create:proxy_host",
        "delete:proxy_host",
        "delete:access_list",
        "delete:certificate",
    ]
    proxy_payload = client.events[2][3]
    assert proxy_payload["certificate_id"] == result.mutations[0]["id"]
    assert proxy_payload["access_list_id"] == result.mutations[1]["id"]


def test_apply_resolves_references_from_existing_noop_operations() -> None:
    client = RecordingClient()
    plan = Plan(
        operations=(
            PlanOperation(
                PlanAction.NOOP,
                ResourceKind.CERTIFICATE,
                desired=_cert(),
                existing=_existing(ResourceKind.CERTIFICATE, "cert.one", 41),
            ),
            PlanOperation(
                PlanAction.NOOP,
                ResourceKind.ACCESS_LIST,
                desired=_acl(),
                existing=_existing(ResourceKind.ACCESS_LIST, "acl.one", 42),
            ),
            PlanOperation(PlanAction.CREATE, ResourceKind.PROXY_HOST, desired=_proxy()),
        ),
        conflicts=(),
        existing_count=2,
    )

    _engine(client).apply(plan)

    proxy_payload = client.events[0][3]
    assert proxy_payload["certificate_id"] == 41
    assert proxy_payload["access_list_id"] == 42


def test_apply_rejects_unresolved_references_before_mutation() -> None:
    client = RecordingClient()
    plan = Plan(
        operations=(
            PlanOperation(PlanAction.CREATE, ResourceKind.PROXY_HOST, desired=_proxy(certificate_ref="missing")),
        ),
        conflicts=(),
        existing_count=0,
    )

    with pytest.raises(ValidationError, match="unresolved certificate reference"):
        _engine(client).apply(plan)

    assert client.events == []


def test_apply_adopt_merges_metadata_without_overwriting_payload_fields() -> None:
    client = RecordingClient()
    existing = _existing(
        ResourceKind.PROXY_HOST,
        "legacy",
        5,
        meta={"manual": "keep"},
        forward_host="manual-host",
        forward_port=8080,
    )
    plan = Plan(
        operations=(PlanOperation(PlanAction.ADOPT, ResourceKind.PROXY_HOST, desired=_proxy(), existing=existing),),
        conflicts=(),
        existing_count=1,
    )

    _engine(client).apply(plan)

    payload = client.events[0][3]
    assert payload["forward_host"] == "manual-host"
    assert payload["forward_port"] == 8080
    assert payload["meta"]["manual"] == "keep"
    assert payload["meta"]["managed_by"] == "npmctl"
    assert payload["meta"]["owner"] == "workload-a"
    assert payload["meta"]["resource_id"] == "proxy.one"


def test_apply_refuses_conflicted_plan_without_mutation() -> None:
    client = RecordingClient()
    plan = Plan(
        operations=(PlanOperation(PlanAction.CREATE, ResourceKind.PROXY_HOST, desired=_proxy()),),
        conflicts=(PlanConflict(code="foreign_owner", message="blocked"),),
        existing_count=1,
    )

    with pytest.raises(ConflictError):
        _engine(client).apply(plan)

    assert client.events == []


def test_apply_reports_delete_success_and_failure() -> None:
    existing = _existing(ResourceKind.PROXY_HOST, "proxy.old", 7)
    plan = Plan(
        operations=(PlanOperation(PlanAction.DELETE, ResourceKind.PROXY_HOST, existing=existing),),
        conflicts=(),
        existing_count=1,
    )
    ok_client = RecordingClient()
    result = _engine(ok_client).apply(plan)
    assert result.mutations == [{"action": "delete", "kind": "proxy_host", "resource_id": "proxy.old", "id": 7}]

    failing_client = RecordingClient(delete_ok=False)
    with pytest.raises(ApiError, match="delete failed"):
        _engine(failing_client).apply(plan)
