"""Desired-state loading and cross-file validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from npmctl.errors import ValidationError
from npmctl.metadata import ManagedIdentity
from npmctl.models import (
    DesiredAccessList,
    DesiredCertificate,
    DesiredGenericResource,
    DesiredProxyHost,
    DesiredResource,
    DesiredState,
    ResourceKind,
    mapping_or_empty,
    require_mapping,
)
from npmctl.plugins import PluginRegistry

SUPPORTED_EXTENSIONS = frozenset({".yaml", ".yml", ".json"})
EXPECTED_API_VERSION = "npmctl.io/v1"
EXPECTED_SCHEMA_VERSION = 1


def load_desired_state(path: str | Path, *, plugin_registry: PluginRegistry | None = None) -> DesiredState:
    """Load a desired-state file or directory."""

    root = Path(path)
    if not root.exists():
        raise ValidationError(f"desired-state path does not exist: {root}")
    files = _discover_files(root)
    if not files:
        raise ValidationError(f"desired-state path contains no YAML or JSON files: {root}")
    plugins = plugin_registry or PluginRegistry.discover()

    proxy_hosts: list[DesiredProxyHost] = []
    certificates: list[DesiredCertificate] = []
    access_lists: list[DesiredAccessList] = []
    redirection_hosts: list[DesiredGenericResource] = []
    dead_hosts: list[DesiredGenericResource] = []
    streams: list[DesiredGenericResource] = []
    users: list[DesiredGenericResource] = []
    settings: list[DesiredGenericResource] = []
    for file_path in files:
        doc = _read_document(file_path)
        _validate_document_header(doc, path=str(file_path))
        for index, item in enumerate(doc.get("certificates") or []):
            certificates.append(DesiredCertificate.from_mapping(item, path=f"{file_path}.certificates[{index}]"))
        for index, item in enumerate(doc.get("access_lists") or []):
            access_lists.append(DesiredAccessList.from_mapping(item, path=f"{file_path}.access_lists[{index}]"))
        for index, item in enumerate(doc.get("redirection_hosts") or []):
            redirection_hosts.append(
                DesiredGenericResource.from_mapping(
                    ResourceKind.REDIRECTION_HOST, item, path=f"{file_path}.redirection_hosts[{index}]"
                )
            )
        for index, item in enumerate(doc.get("dead_hosts") or []):
            dead_hosts.append(
                DesiredGenericResource.from_mapping(
                    ResourceKind.DEAD_HOST, item, path=f"{file_path}.dead_hosts[{index}]"
                )
            )
        for index, item in enumerate(doc.get("streams") or []):
            streams.append(
                DesiredGenericResource.from_mapping(ResourceKind.STREAM, item, path=f"{file_path}.streams[{index}]")
            )
        for index, item in enumerate(doc.get("users") or []):
            users.append(
                DesiredGenericResource.from_mapping(ResourceKind.USER, item, path=f"{file_path}.users[{index}]")
            )
        for index, item in enumerate(doc.get("settings") or []):
            settings.append(
                DesiredGenericResource.from_mapping(ResourceKind.SETTING, item, path=f"{file_path}.settings[{index}]")
            )
        for index, item in enumerate(doc.get("plugin_resources") or []):
            resource = _plugin_resource_from_mapping(
                item, plugins=plugins, path=f"{file_path}.plugin_resources[{index}]"
            )
            _append_generic_resource(
                resource,
                redirection_hosts=redirection_hosts,
                dead_hosts=dead_hosts,
                streams=streams,
                users=users,
                settings=settings,
            )
        for index, item in enumerate(doc.get("external_certificates") or []):
            certificates.append(
                _external_certificate_from_mapping(
                    item, plugins=plugins, path=f"{file_path}.external_certificates[{index}]"
                )
            )
        for index, item in enumerate(doc.get("proxy_hosts") or []):
            proxy_hosts.append(DesiredProxyHost.from_mapping(item, path=f"{file_path}.proxy_hosts[{index}]"))

    desired = DesiredState(
        proxy_hosts=tuple(proxy_hosts),
        certificates=tuple(certificates),
        access_lists=tuple(access_lists),
        redirection_hosts=tuple(redirection_hosts),
        dead_hosts=tuple(dead_hosts),
        streams=tuple(streams),
        users=tuple(users),
        settings=tuple(settings),
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
    for key in (
        "proxy_hosts",
        "certificates",
        "access_lists",
        "redirection_hosts",
        "dead_hosts",
        "streams",
        "users",
        "settings",
        "plugin_resources",
        "external_certificates",
    ):
        if key in doc and doc[key] is not None and not isinstance(doc[key], list):
            raise ValidationError(f"{path}.{key} must be a list")


def _plugin_resource_from_mapping(raw: Any, *, plugins: PluginRegistry, path: str) -> DesiredGenericResource:
    item = require_mapping(raw, path=path)
    provider_name = item.get("provider")
    if not isinstance(provider_name, str) or not provider_name:
        raise ValidationError(f"{path}.provider must be a non-empty string")
    provider = plugins.resource_providers.get(provider_name)
    if provider is None:
        raise ValidationError(f"{path}.provider references unknown resource provider {provider_name!r}")
    payload = require_mapping(item.get("payload"), path=f"{path}.payload")
    owner, resource_id = _provider_identity(provider.identity(payload), path=f"{path}.identity")
    provider_payload = mapping_or_empty(provider.desired_payload(payload), path=f"{path}.desired_payload")
    kind = _provider_kind(provider.kind, path=f"{path}.provider.kind")
    return DesiredGenericResource(
        kind=kind,
        natural_key=provider.natural_key(payload),
        meta={"managed_by": "npmctl", "owner": owner, "resource_id": resource_id},
        api_payload=provider_payload,
    )


def _external_certificate_from_mapping(raw: Any, *, plugins: PluginRegistry, path: str) -> DesiredCertificate:
    item = require_mapping(raw, path=path)
    provider_name = item.get("provider")
    if not isinstance(provider_name, str) or not provider_name:
        raise ValidationError(f"{path}.provider must be a non-empty string")
    provider = plugins.certificate_providers.get(provider_name)
    if provider is None:
        raise ValidationError(f"{path}.provider references unknown certificate provider {provider_name!r}")
    reference = item.get("reference")
    if not isinstance(reference, str) or not reference:
        raise ValidationError(f"{path}.reference must be a non-empty string")
    resolved = mapping_or_empty(provider.resolve(reference), path=f"{path}.resolved")
    certificate = {**resolved, **{key: value for key, value in item.items() if key not in {"provider", "reference"}}}
    certificate.setdefault("name", reference)
    return DesiredCertificate.from_mapping(certificate, path=path)


def _provider_identity(raw: Any, *, path: str) -> tuple[str, str]:
    if isinstance(raw, ManagedIdentity):
        return raw.owner, raw.resource_id
    if isinstance(raw, tuple) and len(raw) == 2 and all(isinstance(value, str) and value for value in raw):
        return raw
    if isinstance(raw, dict):
        owner = raw.get("owner")
        resource_id = raw.get("resource_id")
        if isinstance(owner, str) and owner and isinstance(resource_id, str) and resource_id:
            return owner, resource_id
    raise ValidationError(f"{path} must provide owner and resource_id")


def _provider_kind(raw: Any, *, path: str) -> ResourceKind:
    value = raw.value if hasattr(raw, "value") else raw
    try:
        kind = ResourceKind(str(value))
    except ValueError as exc:
        raise ValidationError(f"{path} must be a supported resource kind") from exc
    if kind in {ResourceKind.PROXY_HOST, ResourceKind.CERTIFICATE, ResourceKind.ACCESS_LIST}:
        raise ValidationError(f"{path} must be a generic resource kind")
    return kind


def _append_generic_resource(
    resource: DesiredGenericResource,
    *,
    redirection_hosts: list[DesiredGenericResource],
    dead_hosts: list[DesiredGenericResource],
    streams: list[DesiredGenericResource],
    users: list[DesiredGenericResource],
    settings: list[DesiredGenericResource],
) -> None:
    if resource.kind == ResourceKind.REDIRECTION_HOST:
        redirection_hosts.append(resource)
    elif resource.kind == ResourceKind.DEAD_HOST:
        dead_hosts.append(resource)
    elif resource.kind == ResourceKind.STREAM:
        streams.append(resource)
    elif resource.kind == ResourceKind.USER:
        users.append(resource)
    elif resource.kind == ResourceKind.SETTING:
        settings.append(resource)
    else:  # pragma: no cover - _provider_kind prevents unsupported generic kinds.
        raise ValidationError(f"unsupported plugin resource kind: {resource.kind.value}")


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
