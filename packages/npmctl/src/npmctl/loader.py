"""Desired-state loading and cross-file validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from npmctl.errors import ValidationError
from npmctl.models import (
    DesiredAccessList,
    DesiredCertificate,
    DesiredProxyHost,
    DesiredResource,
    DesiredState,
    ResourceKind,
)

SUPPORTED_EXTENSIONS = frozenset({".yaml", ".yml", ".json"})
EXPECTED_API_VERSION = "npmctl.io/v1"
EXPECTED_SCHEMA_VERSION = 1


def load_desired_state(path: str | Path) -> DesiredState:
    """Load a desired-state file or directory."""

    root = Path(path)
    if not root.exists():
        raise ValidationError(f"desired-state path does not exist: {root}")
    files = _discover_files(root)
    if not files:
        raise ValidationError(f"desired-state path contains no YAML or JSON files: {root}")

    proxy_hosts: list[DesiredProxyHost] = []
    certificates: list[DesiredCertificate] = []
    access_lists: list[DesiredAccessList] = []
    for file_path in files:
        doc = _read_document(file_path)
        _validate_document_header(doc, path=str(file_path))
        for index, item in enumerate(doc.get("certificates") or []):
            certificates.append(DesiredCertificate.from_mapping(item, path=f"{file_path}.certificates[{index}]"))
        for index, item in enumerate(doc.get("access_lists") or []):
            access_lists.append(DesiredAccessList.from_mapping(item, path=f"{file_path}.access_lists[{index}]"))
        for index, item in enumerate(doc.get("proxy_hosts") or []):
            proxy_hosts.append(DesiredProxyHost.from_mapping(item, path=f"{file_path}.proxy_hosts[{index}]"))

    desired = DesiredState(
        proxy_hosts=tuple(proxy_hosts),
        certificates=tuple(certificates),
        access_lists=tuple(access_lists),
        source_files=tuple(str(file_path) for file_path in files),
    )
    validate_desired_state_integrity(desired)
    return desired


def _discover_files(root: Path) -> list[Path]:
    if root.is_file():
        if root.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValidationError(f"unsupported desired-state extension: {root.suffix}")
        return [root]
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS)


def _read_document(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - platform dependent
        raise ValidationError(f"failed to read {path}: {exc}") from exc
    try:
        if path.suffix.lower() == ".json":
            parsed = json.loads(text)
        else:
            parsed = yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ValidationError(f"failed to parse {path}: {exc}") from exc
    if parsed is None:
        parsed = {}
    if not isinstance(parsed, dict):
        raise ValidationError(f"{path} must contain a YAML/JSON object")
    return parsed


def _validate_document_header(doc: dict[str, Any], *, path: str) -> None:
    if doc.get("apiVersion") != EXPECTED_API_VERSION:
        raise ValidationError(f"{path}.apiVersion must be {EXPECTED_API_VERSION!r}; run npmctl migrate if needed")
    if doc.get("schemaVersion") != EXPECTED_SCHEMA_VERSION:
        raise ValidationError(f"{path}.schemaVersion must be {EXPECTED_SCHEMA_VERSION}; run npmctl migrate if needed")
    for key in ("proxy_hosts", "certificates", "access_lists"):
        if key in doc and doc[key] is not None and not isinstance(doc[key], list):
            raise ValidationError(f"{path}.{key} must be a list")


def validate_desired_state_integrity(desired: DesiredState) -> None:
    """Validate global uniqueness and ownership invariants."""

    resource_ids: dict[str, DesiredResource] = {}
    natural_keys: dict[tuple[ResourceKind, object], DesiredResource] = {}
    domains: dict[str, DesiredProxyHost] = {}

    for resource in desired.resources():
        identity = resource.identity
        if identity.resource_id in resource_ids:
            raise ValidationError(f"duplicate meta.resource_id: {identity.resource_id}")
        resource_ids[identity.resource_id] = resource
        if isinstance(resource, DesiredProxyHost):
            for domain in resource.domain_names:
                if domain in domains:
                    raise ValidationError(f"duplicate proxy host domain across desired state: {domain}")
                domains[domain] = resource
        natural_key = (resource.kind, resource.natural_key)
        if natural_key in natural_keys:
            raise ValidationError(f"duplicate {resource.kind.value} natural key: {resource.natural_key}")
        natural_keys[natural_key] = resource

    certificate_ids = {cert.identity.resource_id for cert in desired.certificates}
    access_list_ids = {acl.identity.resource_id for acl in desired.access_lists}
    for host in desired.proxy_hosts:
        if host.certificate_ref is not None and host.certificate_ref not in certificate_ids:
            raise ValidationError(
                f"proxy host {host.identity.resource_id} references unknown certificate {host.certificate_ref}"
            )
        if host.access_list_ref is not None and host.access_list_ref not in access_list_ids:
            raise ValidationError(
                f"proxy host {host.identity.resource_id} references unknown access list {host.access_list_ref}"
            )
