"""Apply owner-scoped plans to NPM."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from npmctl.client import NpmClient
from npmctl.errors import ConflictError, ValidationError
from npmctl.metadata import merge_managed_meta
from npmctl.models import (
    DesiredAccessList,
    DesiredCertificate,
    DesiredProxyHost,
    ExistingResource,
    PlanAction,
    ResourceKind,
)
from npmctl.planner import Plan, PlanOperation
from npmctl.schema import Capabilities


@dataclass(slots=True)
class ApplyResult:
    """Result of applying a plan."""

    applied: bool
    mutations: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"applied": self.applied, "mutations": list(self.mutations)}


class ApplyEngine:
    """Executes a validated plan in dependency order."""

    def __init__(self, *, client: NpmClient, capabilities: Capabilities) -> None:
        self.client = client
        self.capabilities = capabilities
        self.created_by_resource_id: dict[str, ExistingResource] = {}

    def apply(self, plan: Plan) -> ApplyResult:
        """Apply the plan. Conflicts prevent all mutations."""

        if plan.conflicts:
            raise ConflictError("refusing to apply plan with conflicts")
        for operation in plan.operations:
            if operation.desired is not None and operation.existing is not None:
                self.created_by_resource_id.setdefault(operation.desired.identity.resource_id, operation.existing)
        result = ApplyResult(applied=True)
        for operation in _ordered_operations(plan.operations):
            if operation.action == PlanAction.NOOP:
                continue
            mutation = self._apply_operation(operation)
            result.mutations.append(mutation)
        return result

    def _apply_operation(self, operation: PlanOperation) -> dict[str, Any]:
        if operation.action == PlanAction.CREATE:
            return self._create(operation)
        if operation.action == PlanAction.UPDATE:
            return self._update(operation)
        if operation.action == PlanAction.ADOPT:
            return self._adopt(operation)
        if operation.action == PlanAction.DELETE:
            return self._delete(operation)
        raise ValidationError(f"unsupported apply operation {operation.action}")

    def _create(self, operation: PlanOperation) -> dict[str, Any]:
        desired = _require_desired(operation)
        payload = self._payload_for(desired)
        created = self.client.create_resource(desired.kind, payload)
        self.created_by_resource_id[desired.identity.resource_id] = created
        return {
            "action": "create",
            "kind": desired.kind.value,
            "resource_id": desired.identity.resource_id,
            "id": created.id,
        }

    def _update(self, operation: PlanOperation) -> dict[str, Any]:
        desired = _require_desired(operation)
        existing = _require_existing(operation)
        payload = self._merge_existing_with_desired(existing, desired)
        cap = self.capabilities.for_kind(desired.kind)
        updated = self.client.update_resource(desired.kind, existing.id, payload, method=cap.update_method or "put")
        return {
            "action": "update",
            "kind": desired.kind.value,
            "resource_id": desired.identity.resource_id,
            "id": updated.id,
        }

    def _adopt(self, operation: PlanOperation) -> dict[str, Any]:
        desired = _require_desired(operation)
        existing = _require_existing(operation)
        payload = dict(existing.raw)
        payload["meta"] = merge_managed_meta(payload.get("meta"), desired.meta)
        cap = self.capabilities.for_kind(desired.kind)
        updated = self.client.update_resource(desired.kind, existing.id, payload, method=cap.update_method or "put")
        return {
            "action": "adopt",
            "kind": desired.kind.value,
            "resource_id": desired.identity.resource_id,
            "id": updated.id,
        }

    def _delete(self, operation: PlanOperation) -> dict[str, Any]:
        existing = _require_existing(operation)
        self.client.delete_resource(existing.kind, existing.id)
        resource_id = existing.identity.resource_id if existing.identity else None
        return {"action": "delete", "kind": existing.kind.value, "resource_id": resource_id, "id": existing.id}

    def _merge_existing_with_desired(
        self, existing: ExistingResource, desired: DesiredProxyHost | DesiredCertificate | DesiredAccessList
    ) -> dict[str, Any]:
        payload = dict(existing.raw)
        payload.update(self._payload_for(desired))
        payload["meta"] = merge_managed_meta(existing.raw.get("meta"), desired.meta)
        return payload

    def _payload_for(self, desired: DesiredProxyHost | DesiredCertificate | DesiredAccessList) -> dict[str, Any]:
        if isinstance(desired, DesiredProxyHost):
            certificate_id = self._resolve_reference(desired.certificate_ref, ResourceKind.CERTIFICATE)
            access_list_id = self._resolve_reference(desired.access_list_ref, ResourceKind.ACCESS_LIST)
            return desired.to_payload(certificate_id=certificate_id, access_list_id=access_list_id)
        return desired.to_payload()

    def _resolve_reference(self, ref: str | None, kind: ResourceKind) -> int | None:
        if ref is None:
            return None
        created = self.created_by_resource_id.get(ref)
        if created is not None:
            return created.id
        # Desired references are validated during loading. Existing IDs for referenced
        # resources are already in plan operations when they are noops/updates; use the
        # first matching operation from dependency order if available. The CLI uses fresh
        # list state, so create ordering covers new references.
        return None


def _ordered_operations(operations: tuple[PlanOperation, ...]) -> list[PlanOperation]:
    creates_updates_adopts = [
        op for op in operations if op.action in {PlanAction.CREATE, PlanAction.UPDATE, PlanAction.ADOPT}
    ]
    deletes = [op for op in operations if op.action == PlanAction.DELETE]
    order = {ResourceKind.CERTIFICATE: 0, ResourceKind.ACCESS_LIST: 1, ResourceKind.PROXY_HOST: 2}
    delete_order = {ResourceKind.PROXY_HOST: 0, ResourceKind.ACCESS_LIST: 1, ResourceKind.CERTIFICATE: 2}
    return sorted(creates_updates_adopts, key=lambda op: order[op.kind]) + sorted(
        deletes, key=lambda op: delete_order[op.kind]
    )


def _require_desired(operation: PlanOperation) -> DesiredProxyHost | DesiredCertificate | DesiredAccessList:
    if operation.desired is None:
        raise ValidationError(f"operation {operation.action} requires desired resource")
    return operation.desired


def _require_existing(operation: PlanOperation) -> ExistingResource:
    if operation.existing is None:
        raise ValidationError(f"operation {operation.action} requires existing resource")
    return operation.existing
