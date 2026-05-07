"""Owner-scoped plan engine for NPM resources."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from npmctl.models import (
    DesiredProxyHost,
    DesiredResource,
    DesiredState,
    ExistingResource,
    ExistingState,
    PlanAction,
    ResourceKind,
)
from npmctl.schema import Capabilities

_PROXY_HOST_DEFAULTS: dict[str, Any] = {
    "access_list_id": 0,
    "certificate_id": 0,
    "ssl_forced": 0,
    "caching_enabled": 0,
    "block_exploits": 0,
    "advanced_config": "",
    "allow_websocket_upgrade": 0,
    "http2_support": 0,
    "enabled": 1,
    "locations": [],
    "hsts_enabled": 0,
    "hsts_subdomains": 0,
}


@dataclass(frozen=True, slots=True)
class PlannerOptions:
    """Planner behavior flags."""

    owner: str | None = None
    allow_updates: bool = True
    prune_owned: bool = False
    adopt: bool = False
    strict_adopt: bool = True
    allow_field_drift: bool = False


@dataclass(frozen=True, slots=True)
class PlanConflict:
    """A safety conflict that blocks apply."""

    code: str
    message: str
    kind: ResourceKind | None = None
    owner: str | None = None
    resource_id: str | None = None
    existing_id: int | str | None = None
    domain: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "kind": self.kind.value if self.kind else None,
            "owner": self.owner,
            "resource_id": self.resource_id,
            "existing_id": self.existing_id,
            "domain": self.domain,
        }


@dataclass(frozen=True, slots=True)
class PlanOperation:
    """One planned mutation or no-op."""

    action: PlanAction
    kind: ResourceKind
    desired: DesiredResource | None = None
    existing: ExistingResource | None = None
    reason: str = ""
    diff: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def owner(self) -> str | None:
        if self.desired is not None:
            return self.desired.identity.owner
        if self.existing is not None and self.existing.identity is not None:
            return self.existing.identity.owner
        return None

    @property
    def resource_id(self) -> str | None:
        if self.desired is not None:
            return self.desired.identity.resource_id
        if self.existing is not None and self.existing.identity is not None:
            return self.existing.identity.resource_id
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "kind": self.kind.value,
            "owner": self.owner,
            "resource_id": self.resource_id,
            "existing": self.existing.to_dict() if self.existing else None,
            "reason": self.reason,
            "diff": self.diff,
        }


@dataclass(frozen=True, slots=True)
class Plan:
    """Complete plan result."""

    operations: tuple[PlanOperation, ...]
    conflicts: tuple[PlanConflict, ...]
    existing_count: int

    @property
    def ok(self) -> bool:
        return not self.conflicts

    def by_action(self, action: PlanAction) -> tuple[PlanOperation, ...]:
        return tuple(op for op in self.operations if op.action == action)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "existing_count": self.existing_count,
            "summary": {
                action.value: len(self.by_action(action)) for action in PlanAction if action != PlanAction.CONFLICT
            }
            | {"conflict": len(self.conflicts)},
            "operations": [op.to_dict() for op in self.operations],
            "conflicts": [conflict.to_dict() for conflict in self.conflicts],
        }


def compute_plan(
    *,
    desired: DesiredState,
    existing: ExistingState,
    capabilities: Capabilities,
    options: PlannerOptions | None = None,
) -> Plan:
    """Compute side-effect-free owner-scoped CRUD/adopt plan."""

    opts = options or PlannerOptions()
    operations: list[PlanOperation] = []
    conflicts: list[PlanConflict] = []
    all_existing = existing.resources()

    _detect_existing_integrity_conflicts(existing, conflicts)
    desired_resources = desired.resources()
    desired_by_identity = {(res.kind, res.identity.owner, res.identity.resource_id): res for res in desired_resources}

    existing_by_identity: dict[tuple[ResourceKind, str, str], ExistingResource] = {}
    existing_by_key: dict[tuple[ResourceKind, Any], ExistingResource] = {}
    domain_index: dict[str, ExistingResource] = {}
    for item in all_existing:
        existing_by_key[(item.kind, item.natural_key)] = item
        if item.identity is not None:
            existing_by_identity[(item.kind, item.identity.owner, item.identity.resource_id)] = item
        if item.kind == ResourceKind.PROXY_HOST:
            for domain in item.domain_names:
                domain_index[domain] = item

    for resource in desired_resources:
        identity = resource.identity
        identity_key = (resource.kind, identity.owner, identity.resource_id)
        natural_key = (resource.kind, resource.natural_key)
        cap = capabilities.for_kind(resource.kind)

        if opts.owner and identity.owner != opts.owner:
            continue

        existing_same_identity = existing_by_identity.get(identity_key)
        if existing_same_identity is not None and existing_same_identity.natural_key != resource.natural_key:
            conflicts.append(
                PlanConflict(
                    code="resource_id_drift",
                    message=(
                        f"{resource.kind.value} {identity.resource_id} exists with natural key "
                        f"{existing_same_identity.natural_key!r}, desired {resource.natural_key!r}"
                    ),
                    kind=resource.kind,
                    owner=identity.owner,
                    resource_id=identity.resource_id,
                    existing_id=existing_same_identity.id,
                )
            )
            continue

        if isinstance(resource, DesiredProxyHost):
            collision = _proxy_domain_collision(resource, domain_index, existing_same_identity)
            if collision is not None:
                conflicts.append(collision)
                continue

        existing_same_key = existing_by_key.get(natural_key)
        if existing_same_key is None:
            if not cap.create:
                conflicts.append(_capability_conflict(resource, "create"))
            else:
                operations.append(PlanOperation(PlanAction.CREATE, resource.kind, desired=resource, reason="missing"))
            continue

        if existing_same_key.identity is None:
            if not opts.adopt:
                conflicts.append(
                    PlanConflict(
                        code="unmanaged_resource",
                        message=f"{resource.kind.value} {resource.natural_key!r} exists but has no npmctl ownership metadata",
                        kind=resource.kind,
                        owner=identity.owner,
                        resource_id=identity.resource_id,
                        existing_id=existing_same_key.id,
                    )
                )
                continue
            diff = diff_resource(resource, existing_same_key)
            diff.pop("meta", None)
            if opts.strict_adopt and diff and not opts.allow_field_drift:
                conflicts.append(
                    PlanConflict(
                        code="adopt_field_drift",
                        message=f"cannot strictly adopt {resource.kind.value} {resource.natural_key!r}; fields differ",
                        kind=resource.kind,
                        owner=identity.owner,
                        resource_id=identity.resource_id,
                        existing_id=existing_same_key.id,
                    )
                )
                continue
            if not cap.update:
                conflicts.append(_capability_conflict(resource, "update", existing_id=existing_same_key.id))
            else:
                operations.append(
                    PlanOperation(
                        PlanAction.ADOPT,
                        resource.kind,
                        desired=resource,
                        existing=existing_same_key,
                        reason="explicit adopt",
                        diff=diff,
                    )
                )
            continue

        if existing_same_key.identity != identity:
            conflicts.append(
                PlanConflict(
                    code="foreign_owner",
                    message=(
                        f"{resource.kind.value} {resource.natural_key!r} is owned by "
                        f"{existing_same_key.identity.owner}/{existing_same_key.identity.resource_id}"
                    ),
                    kind=resource.kind,
                    owner=identity.owner,
                    resource_id=identity.resource_id,
                    existing_id=existing_same_key.id,
                )
            )
            continue

        diff = diff_resource(resource, existing_same_key)
        if not diff:
            operations.append(
                PlanOperation(
                    PlanAction.NOOP,
                    resource.kind,
                    desired=resource,
                    existing=existing_same_key,
                    reason="already converged",
                )
            )
            continue
        if not opts.allow_updates:
            conflicts.append(
                PlanConflict(
                    code="owned_drift_updates_disabled",
                    message=f"{resource.kind.value} {identity.resource_id} drifted but updates are disabled",
                    kind=resource.kind,
                    owner=identity.owner,
                    resource_id=identity.resource_id,
                    existing_id=existing_same_key.id,
                )
            )
            continue
        if not cap.update:
            conflicts.append(_capability_conflict(resource, "update", existing_id=existing_same_key.id))
            continue
        operations.append(
            PlanOperation(
                PlanAction.UPDATE,
                resource.kind,
                desired=resource,
                existing=existing_same_key,
                reason="owned drift",
                diff=diff,
            )
        )

    if opts.prune_owned:
        prune_owners = {opts.owner} if opts.owner else set(desired.owners)
        for item in all_existing:
            if item.identity is None or item.identity.owner not in prune_owners:
                continue
            key = (item.kind, item.identity.owner, item.identity.resource_id)
            if key in desired_by_identity:
                continue
            cap = capabilities.for_kind(item.kind)
            if not cap.delete:
                conflicts.append(
                    PlanConflict(
                        code="missing_delete_capability",
                        message=f"NPM API does not expose delete for {item.kind.value}",
                        kind=item.kind,
                        owner=item.identity.owner,
                        resource_id=item.identity.resource_id,
                        existing_id=item.id,
                    )
                )
            else:
                operations.append(
                    PlanOperation(
                        PlanAction.DELETE, item.kind, existing=item, reason="owned resource absent from desired state"
                    )
                )

    return Plan(operations=tuple(operations), conflicts=tuple(conflicts), existing_count=len(all_existing))


def diff_resource(desired: DesiredResource, existing: ExistingResource) -> dict[str, dict[str, Any]]:
    """Return desired-vs-existing field diff for fields controlled by desired."""

    desired_payload = _normalized_payload(desired.comparable_payload())
    existing_payload = _normalized_existing(existing, desired_payload)
    diff: dict[str, dict[str, Any]] = {}
    for key, desired_value in desired_payload.items():
        actual_value = existing_payload.get(key)
        if actual_value != desired_value:
            diff[key] = {"actual": actual_value, "desired": desired_value}
    return diff


def _normalized_payload(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    if "domain_names" in out and isinstance(out["domain_names"], list):
        out["domain_names"] = sorted(out["domain_names"])
    if "meta" in out and isinstance(out["meta"], dict):
        out["meta"] = {key: out["meta"][key] for key in sorted(out["meta"])}
    return out


def _normalized_existing(existing: ExistingResource, desired_payload: dict[str, Any]) -> dict[str, Any]:
    raw = dict(existing.raw)
    if existing.kind == ResourceKind.CERTIFICATE and "name" not in raw and existing.name is not None:
        raw["name"] = existing.name
    if existing.kind == ResourceKind.ACCESS_LIST and "name" not in raw and existing.name is not None:
        raw["name"] = existing.name
    if existing.kind == ResourceKind.PROXY_HOST:
        for key, default in _PROXY_HOST_DEFAULTS.items():
            if key in desired_payload and raw.get(key) is None:
                raw[key] = default
    filtered: dict[str, Any] = {}
    for key, desired_value in desired_payload.items():
        actual_value = raw.get(key)
        if key == "meta" and isinstance(actual_value, dict) and isinstance(desired_value, dict):
            actual_value = {meta_key: actual_value.get(meta_key) for meta_key in desired_value}
        else:
            actual_value = _coerce_existing_value(actual_value, desired_value)
        filtered[key] = actual_value
    if "domain_names" in filtered and isinstance(filtered["domain_names"], list):
        filtered["domain_names"] = sorted(filtered["domain_names"])
    if "meta" in filtered and isinstance(filtered["meta"], dict):
        filtered["meta"] = {key: filtered["meta"][key] for key in sorted(filtered["meta"])}
    return filtered


def _coerce_existing_value(actual_value: Any, desired_value: Any) -> Any:
    if desired_value == [] and actual_value is None:
        return []
    if isinstance(desired_value, int) and not isinstance(desired_value, bool):
        if isinstance(actual_value, bool):
            return int(actual_value)
        if isinstance(actual_value, str) and actual_value.strip().isdigit():
            return int(actual_value)
    return actual_value


def _proxy_domain_collision(
    desired: DesiredProxyHost,
    domain_index: dict[str, ExistingResource],
    same_identity: ExistingResource | None,
) -> PlanConflict | None:
    for domain in desired.domain_names:
        existing = domain_index.get(domain)
        if existing is None:
            continue
        if same_identity is not None and existing.id == same_identity.id:
            continue
        if existing.natural_key == desired.natural_key:
            continue
        return PlanConflict(
            code="domain_collision",
            message=f"domain {domain} already exists on proxy host id={existing.id}",
            kind=ResourceKind.PROXY_HOST,
            owner=desired.identity.owner,
            resource_id=desired.identity.resource_id,
            existing_id=existing.id,
            domain=domain,
        )
    return None


def _detect_existing_integrity_conflicts(existing: ExistingState, conflicts: list[PlanConflict]) -> None:
    seen_domains: dict[str, ExistingResource] = {}
    seen_identity: dict[tuple[ResourceKind, str, str], ExistingResource] = {}
    for item in existing.resources():
        if item.identity is not None:
            key = (item.kind, item.identity.owner, item.identity.resource_id)
            prior = seen_identity.get(key)
            if prior is not None and prior.id != item.id:
                conflicts.append(
                    PlanConflict(
                        code="duplicate_existing_resource_id",
                        message=f"duplicate existing {item.kind.value} identity {item.identity.owner}/{item.identity.resource_id}",
                        kind=item.kind,
                        owner=item.identity.owner,
                        resource_id=item.identity.resource_id,
                        existing_id=item.id,
                    )
                )
            seen_identity[key] = item
        if item.kind == ResourceKind.PROXY_HOST:
            for domain in item.domain_names:
                prior = seen_domains.get(domain)
                if prior is not None and prior.id != item.id:
                    conflicts.append(
                        PlanConflict(
                            code="duplicate_existing_domain",
                            message=f"duplicate existing proxy host domain {domain}",
                            kind=ResourceKind.PROXY_HOST,
                            existing_id=item.id,
                            domain=domain,
                        )
                    )
                seen_domains[domain] = item


def _capability_conflict(resource: DesiredResource, operation: str, *, existing_id: int | None = None) -> PlanConflict:
    return PlanConflict(
        code=f"missing_{operation}_capability",
        message=f"NPM API does not expose {operation} for {resource.kind.value}",
        kind=resource.kind,
        owner=resource.identity.owner,
        resource_id=resource.identity.resource_id,
        existing_id=existing_id,
    )
