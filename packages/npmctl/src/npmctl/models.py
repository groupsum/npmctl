"""Typed desired-state and live-resource models."""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, ClassVar

from npmctl.errors import ValidationError
from npmctl.metadata import ManagedIdentity, identity_from_meta, validate_metadata

_DOMAIN_LABEL_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_FORWARD_HOST_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]+$")
_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/ -]{0,127}$")
_VALID_SCHEMES = frozenset({"http", "https"})
_TOGGLE_FIELDS = (
    "enabled",
    "ssl_forced",
    "caching_enabled",
    "block_exploits",
    "allow_websocket_upgrade",
    "http2_support",
    "hsts_enabled",
    "hsts_subdomains",
)


class ResourceKind(StrEnum):
    """Supported NPM resource kinds."""

    PROXY_HOST = "proxy_host"
    CERTIFICATE = "certificate"
    ACCESS_LIST = "access_list"


class PlanAction(StrEnum):
    """Plan operation kinds."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ADOPT = "adopt"
    NOOP = "noop"
    CONFLICT = "conflict"


def canonicalize_domain(value: Any, *, path: str) -> str:
    """Normalize and validate DNS names accepted by NPM."""

    if not isinstance(value, str):
        raise ValidationError(f"{path} must be a string")
    domain = value.strip().lower().rstrip(".")
    if not domain:
        raise ValidationError(f"{path} must not be empty")
    if len(domain) > 253:
        raise ValidationError(f"{path} exceeds 253 characters")
    labels = domain.split(".")
    if any(label == "" for label in labels):
        raise ValidationError(f"{path} contains an empty DNS label")
    for index, label in enumerate(labels):
        if label == "*":
            if index != 0 or len(labels) < 3:
                raise ValidationError(f"{path} wildcard is only allowed as the left-most label")
            continue
        if not _DOMAIN_LABEL_PATTERN.fullmatch(label):
            raise ValidationError(f"{path} contains invalid DNS label {label!r}")
    return domain


def canonical_domain_set(values: Any, *, path: str, allow_empty: bool = False) -> tuple[str, ...]:
    """Normalize a DNS domain list into a stable tuple."""

    if values is None and allow_empty:
        return ()
    if not isinstance(values, list):
        raise ValidationError(f"{path} must be a list")
    if not values and not allow_empty:
        raise ValidationError(f"{path} must contain at least one domain")
    return tuple(sorted({canonicalize_domain(value, path=f"{path}[{index}]") for index, value in enumerate(values)}))


def validate_name(value: Any, *, path: str) -> str:
    """Validate a human stable resource name."""

    if not isinstance(value, str):
        raise ValidationError(f"{path} must be a string")
    name = value.strip()
    if not name or not _NAME_PATTERN.fullmatch(name):
        raise ValidationError(f"{path} must be a non-empty stable name")
    return name


def validate_forward_host(value: Any, *, path: str) -> str:
    """Validate upstream target hostname/IP/container name."""

    if not isinstance(value, str):
        raise ValidationError(f"{path} must be a string")
    host = value.strip()
    if not host:
        raise ValidationError(f"{path} must not be empty")
    if "://" in host or "/" in host or any(char.isspace() for char in host):
        raise ValidationError(f"{path} must be a host/IP/container name without scheme, slash, or spaces")
    try:
        ipaddress.ip_address(host.strip("[]"))
        return host
    except ValueError:
        pass
    if not _FORWARD_HOST_PATTERN.fullmatch(host):
        raise ValidationError(f"{path} contains unsupported characters")
    return host


def validate_port(value: Any, *, path: str) -> int:
    """Validate a TCP port."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{path} must be an integer")
    if value < 1 or value > 65535:
        raise ValidationError(f"{path} must be between 1 and 65535")
    return value


def validate_toggle(value: Any, *, path: str) -> int:
    """Validate NPM integer booleans."""

    if isinstance(value, bool):
        return int(value)
    if value not in (0, 1):
        raise ValidationError(f"{path} must be 0, 1, true, or false")
    return int(value)


def validate_scheme(value: Any, *, path: str) -> str:
    """Validate an upstream scheme."""

    if not isinstance(value, str):
        raise ValidationError(f"{path} must be a string")
    scheme = value.strip().lower()
    if scheme not in _VALID_SCHEMES:
        raise ValidationError(f"{path} must be one of {sorted(_VALID_SCHEMES)}")
    return scheme


def optional_int(value: Any, *, path: str, minimum: int = 0) -> int | None:
    """Validate optional integer fields."""

    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{path} must be an integer")
    if value < minimum:
        raise ValidationError(f"{path} must be >= {minimum}")
    return value


def require_mapping(raw: Any, *, path: str) -> Mapping[str, Any]:
    """Require a mapping."""

    if not isinstance(raw, Mapping):
        raise ValidationError(f"{path} must be an object")
    return raw


def mapping_or_empty(raw: Any, *, path: str) -> dict[str, Any]:
    """Validate an optional mapping."""

    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise ValidationError(f"{path} must be an object")
    return dict(raw)


@dataclass(frozen=True, slots=True)
class DesiredProxyHost:
    """Desired proxy host declaration."""

    kind: ClassVar[ResourceKind] = ResourceKind.PROXY_HOST

    domain_names: tuple[str, ...]
    forward_host: str
    forward_port: int
    meta: dict[str, Any]
    forward_scheme: str = "http"
    access_list_id: int | None = None
    certificate_id: int | None = None
    access_list_ref: str | None = None
    certificate_ref: str | None = None
    ssl_forced: int = 0
    caching_enabled: int = 0
    block_exploits: int = 0
    advanced_config: str = ""
    allow_websocket_upgrade: int = 0
    http2_support: int = 0
    enabled: int = 1
    locations: list[Any] = field(default_factory=list)
    hsts_enabled: int = 0
    hsts_subdomains: int = 0
    use_default_location: bool = True
    ipv6: bool = True

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any], *, path: str) -> DesiredProxyHost:
        """Parse a desired proxy host."""

        raw = require_mapping(raw, path=path)
        missing = [name for name in ("domain_names", "forward_host", "forward_port", "meta") if name not in raw]
        if missing:
            raise ValidationError(f"{path} missing required keys: {', '.join(missing)}")
        toggles = {
            field_name: validate_toggle(
                raw.get(field_name, 1 if field_name == "enabled" else 0), path=f"{path}.{field_name}"
            )
            for field_name in _TOGGLE_FIELDS
        }
        locations = raw.get("locations", [])
        if not isinstance(locations, list):
            raise ValidationError(f"{path}.locations must be a list")
        advanced_config = raw.get("advanced_config", "")
        if not isinstance(advanced_config, str):
            raise ValidationError(f"{path}.advanced_config must be a string")
        use_default_location = raw.get("use_default_location", True)
        ipv6 = raw.get("ipv6", True)
        if not isinstance(use_default_location, bool):
            raise ValidationError(f"{path}.use_default_location must be a boolean")
        if not isinstance(ipv6, bool):
            raise ValidationError(f"{path}.ipv6 must be a boolean")
        access_list_ref = raw.get("access_list_ref")
        certificate_ref = raw.get("certificate_ref")
        if access_list_ref is not None and not isinstance(access_list_ref, str):
            raise ValidationError(f"{path}.access_list_ref must be a string")
        if certificate_ref is not None and not isinstance(certificate_ref, str):
            raise ValidationError(f"{path}.certificate_ref must be a string")
        access_list_id = optional_int(raw.get("access_list_id"), path=f"{path}.access_list_id")
        certificate_id = optional_int(raw.get("certificate_id"), path=f"{path}.certificate_id")
        if access_list_id is not None and access_list_ref is not None:
            raise ValidationError(f"{path} may not set both access_list_id and access_list_ref")
        if certificate_id is not None and certificate_ref is not None:
            raise ValidationError(f"{path} may not set both certificate_id and certificate_ref")
        return cls(
            domain_names=canonical_domain_set(raw["domain_names"], path=f"{path}.domain_names"),
            forward_host=validate_forward_host(raw["forward_host"], path=f"{path}.forward_host"),
            forward_port=validate_port(raw["forward_port"], path=f"{path}.forward_port"),
            forward_scheme=validate_scheme(raw.get("forward_scheme", "http"), path=f"{path}.forward_scheme"),
            access_list_id=access_list_id,
            certificate_id=certificate_id,
            access_list_ref=access_list_ref,
            certificate_ref=certificate_ref,
            ssl_forced=toggles["ssl_forced"],
            caching_enabled=toggles["caching_enabled"],
            block_exploits=toggles["block_exploits"],
            advanced_config=advanced_config,
            meta=validate_metadata(raw["meta"], path=path),
            allow_websocket_upgrade=toggles["allow_websocket_upgrade"],
            http2_support=toggles["http2_support"],
            enabled=toggles["enabled"],
            locations=list(locations),
            hsts_enabled=toggles["hsts_enabled"],
            hsts_subdomains=toggles["hsts_subdomains"],
            use_default_location=use_default_location,
            ipv6=ipv6,
        )

    @property
    def identity(self) -> ManagedIdentity:
        return ManagedIdentity(owner=str(self.meta["owner"]), resource_id=str(self.meta["resource_id"]))

    @property
    def natural_key(self) -> tuple[str, ...]:
        return self.domain_names

    def to_payload(self, *, certificate_id: int | None = None, access_list_id: int | None = None) -> dict[str, Any]:
        """Convert to an NPM API payload."""

        payload = {
            "domain_names": list(self.domain_names),
            "forward_host": self.forward_host,
            "forward_port": self.forward_port,
            "forward_scheme": self.forward_scheme,
            "access_list_id": access_list_id if access_list_id is not None else (self.access_list_id or 0),
            "certificate_id": certificate_id if certificate_id is not None else (self.certificate_id or 0),
            "ssl_forced": self.ssl_forced,
            "caching_enabled": self.caching_enabled,
            "block_exploits": self.block_exploits,
            "advanced_config": self.advanced_config,
            "meta": dict(self.meta),
            "allow_websocket_upgrade": self.allow_websocket_upgrade,
            "http2_support": self.http2_support,
            "enabled": self.enabled,
            "locations": list(self.locations),
            "hsts_enabled": self.hsts_enabled,
            "hsts_subdomains": self.hsts_subdomains,
            "use_default_location": self.use_default_location,
            "ipv6": self.ipv6,
        }
        return payload

    def comparable_payload(self) -> dict[str, Any]:
        payload = self.to_payload()
        if self.certificate_ref is not None:
            payload.pop("certificate_id", None)
        if self.access_list_ref is not None:
            payload.pop("access_list_id", None)
        return payload


@dataclass(frozen=True, slots=True)
class DesiredCertificate:
    """Desired SSL certificate declaration.

    NPM certificate payloads vary by install/version and DNS provider. `api_payload`
    is therefore an explicit pass-through contract validated for shape and merged
    with ownership metadata, name, and domains.
    """

    kind: ClassVar[ResourceKind] = ResourceKind.CERTIFICATE

    name: str
    domain_names: tuple[str, ...]
    meta: dict[str, Any]
    certificate_type: str = "letsencrypt"
    api_payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any], *, path: str) -> DesiredCertificate:
        raw = require_mapping(raw, path=path)
        missing = [name for name in ("name", "domain_names", "meta") if name not in raw]
        if missing:
            raise ValidationError(f"{path} missing required keys: {', '.join(missing)}")
        certificate_type = raw.get("certificate_type", "letsencrypt")
        if not isinstance(certificate_type, str) or not certificate_type.strip():
            raise ValidationError(f"{path}.certificate_type must be a non-empty string")
        return cls(
            name=validate_name(raw["name"], path=f"{path}.name"),
            domain_names=canonical_domain_set(raw["domain_names"], path=f"{path}.domain_names"),
            meta=validate_metadata(raw["meta"], path=path),
            certificate_type=certificate_type.strip(),
            api_payload=mapping_or_empty(raw.get("api_payload"), path=f"{path}.api_payload"),
        )

    @property
    def identity(self) -> ManagedIdentity:
        return ManagedIdentity(owner=str(self.meta["owner"]), resource_id=str(self.meta["resource_id"]))

    @property
    def natural_key(self) -> str:
        return self.name

    def to_payload(self) -> dict[str, Any]:
        payload = dict(self.api_payload)
        payload.update(
            {
                "name": self.name,
                "domain_names": list(self.domain_names),
                "certificate_type": self.certificate_type,
                "meta": dict(self.meta),
            }
        )
        return payload

    def comparable_payload(self) -> dict[str, Any]:
        return self.to_payload()


@dataclass(frozen=True, slots=True)
class DesiredAccessList:
    """Desired NPM access-list declaration."""

    kind: ClassVar[ResourceKind] = ResourceKind.ACCESS_LIST

    name: str
    meta: dict[str, Any]
    api_payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any], *, path: str) -> DesiredAccessList:
        raw = require_mapping(raw, path=path)
        missing = [name for name in ("name", "meta") if name not in raw]
        if missing:
            raise ValidationError(f"{path} missing required keys: {', '.join(missing)}")
        return cls(
            name=validate_name(raw["name"], path=f"{path}.name"),
            meta=validate_metadata(raw["meta"], path=path),
            api_payload=mapping_or_empty(raw.get("api_payload"), path=f"{path}.api_payload"),
        )

    @property
    def identity(self) -> ManagedIdentity:
        return ManagedIdentity(owner=str(self.meta["owner"]), resource_id=str(self.meta["resource_id"]))

    @property
    def natural_key(self) -> str:
        return self.name

    def to_payload(self) -> dict[str, Any]:
        payload = dict(self.api_payload)
        payload.update({"name": self.name, "meta": dict(self.meta)})
        return payload

    def comparable_payload(self) -> dict[str, Any]:
        return self.to_payload()


DesiredResource = DesiredProxyHost | DesiredCertificate | DesiredAccessList


@dataclass(frozen=True, slots=True)
class ExistingResource:
    """Existing resource read from NPM."""

    kind: ResourceKind
    id: int
    raw: dict[str, Any]
    natural_key: Any
    domain_names: tuple[str, ...] = ()
    name: str | None = None
    identity: ManagedIdentity | None = None

    @classmethod
    def from_proxy_host(cls, raw: Mapping[str, Any]) -> ExistingResource:
        item = dict(raw)
        return cls(
            kind=ResourceKind.PROXY_HOST,
            id=_raw_id(item),
            raw=item,
            natural_key=canonical_domain_set(item.get("domain_names", []), path="proxy_host.domain_names"),
            domain_names=canonical_domain_set(item.get("domain_names", []), path="proxy_host.domain_names"),
            identity=identity_from_meta(item.get("meta")),
        )

    @classmethod
    def from_certificate(cls, raw: Mapping[str, Any]) -> ExistingResource:
        item = dict(raw)
        name = str(item.get("name") or item.get("nice_name") or item.get("provider") or f"certificate-{_raw_id(item)}")
        domain_names = canonical_domain_set(
            item.get("domain_names") or item.get("domains") or [], path="certificate.domain_names", allow_empty=True
        )
        return cls(
            kind=ResourceKind.CERTIFICATE,
            id=_raw_id(item),
            raw=item,
            natural_key=name,
            domain_names=domain_names,
            name=name,
            identity=identity_from_meta(item.get("meta")),
        )

    @classmethod
    def from_access_list(cls, raw: Mapping[str, Any]) -> ExistingResource:
        item = dict(raw)
        name = str(item.get("name") or f"access-list-{_raw_id(item)}")
        return cls(
            kind=ResourceKind.ACCESS_LIST,
            id=_raw_id(item),
            raw=item,
            natural_key=name,
            name=name,
            identity=identity_from_meta(item.get("meta")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "id": self.id,
            "natural_key": list(self.natural_key) if isinstance(self.natural_key, tuple) else self.natural_key,
            "name": self.name,
            "domain_names": list(self.domain_names),
            "identity": self.identity.to_dict() if self.identity else None,
        }


def _raw_id(item: Mapping[str, Any]) -> int:
    raw_id = item.get("id")
    if isinstance(raw_id, bool) or not isinstance(raw_id, int) or raw_id < 1:
        raise ValidationError("existing API object must contain positive integer id")
    return raw_id


@dataclass(frozen=True, slots=True)
class DesiredState:
    """Loaded desired-state document set."""

    proxy_hosts: tuple[DesiredProxyHost, ...] = ()
    certificates: tuple[DesiredCertificate, ...] = ()
    access_lists: tuple[DesiredAccessList, ...] = ()
    source_files: tuple[str, ...] = ()
    api_version: str = "npmctl.io/v1"
    schema_version: int = 1

    def resources(self) -> tuple[DesiredResource, ...]:
        return (*self.certificates, *self.access_lists, *self.proxy_hosts)

    def resources_by_kind(self, kind: ResourceKind) -> tuple[DesiredResource, ...]:
        if kind == ResourceKind.PROXY_HOST:
            return self.proxy_hosts
        if kind == ResourceKind.CERTIFICATE:
            return self.certificates
        if kind == ResourceKind.ACCESS_LIST:
            return self.access_lists
        return ()

    @property
    def owners(self) -> frozenset[str]:
        return frozenset(resource.identity.owner for resource in self.resources())


@dataclass(frozen=True, slots=True)
class ExistingState:
    """Existing NPM resource set."""

    proxy_hosts: tuple[ExistingResource, ...] = ()
    certificates: tuple[ExistingResource, ...] = ()
    access_lists: tuple[ExistingResource, ...] = ()

    def resources(self) -> tuple[ExistingResource, ...]:
        return (*self.certificates, *self.access_lists, *self.proxy_hosts)

    def resources_by_kind(self, kind: ResourceKind) -> tuple[ExistingResource, ...]:
        if kind == ResourceKind.PROXY_HOST:
            return self.proxy_hosts
        if kind == ResourceKind.CERTIFICATE:
            return self.certificates
        if kind == ResourceKind.ACCESS_LIST:
            return self.access_lists
        return ()


def resource_kind_of(resource: DesiredResource | ExistingResource) -> ResourceKind:
    if isinstance(resource, ExistingResource):
        return resource.kind
    return resource.kind


def desired_by_resource_id(
    resources: Iterable[DesiredResource],
) -> dict[tuple[ResourceKind, str, str], DesiredResource]:
    out: dict[tuple[ResourceKind, str, str], DesiredResource] = {}
    for resource in resources:
        identity = resource.identity
        out[(resource.kind, identity.owner, identity.resource_id)] = resource
    return out
