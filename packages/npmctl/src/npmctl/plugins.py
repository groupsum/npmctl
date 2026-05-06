"""Extension and plugin contracts for npmctl."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
from typing import Any, Protocol

from npmctl.models import ResourceKind


class ResourceProvider(Protocol):
    """Provider contract for custom resource kinds."""

    kind: ResourceKind

    def identity(self, payload: dict[str, Any]) -> tuple[str, str]:
        """Return owner and resource id for a payload."""

    def natural_key(self, payload: dict[str, Any]) -> Any:
        """Return the resource natural key."""

    def desired_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return the provider-specific API payload."""


class CertificateProvider(Protocol):
    """Provider contract for external certificate resolution."""

    name: str

    def resolve(self, reference: str) -> dict[str, Any]:
        """Resolve a certificate reference into an NPM-compatible payload."""


@dataclass(slots=True)
class PluginRegistry:
    """In-memory plugin registry used by tests and embedded consumers."""

    resource_providers: dict[str, ResourceProvider]
    certificate_providers: dict[str, CertificateProvider]

    def __init__(self) -> None:
        self.resource_providers = {}
        self.certificate_providers = {}

    def register_resource_provider(self, name: str, provider: ResourceProvider) -> None:
        self.resource_providers[name] = provider

    def register_certificate_provider(self, name: str, provider: CertificateProvider) -> None:
        self.certificate_providers[name] = provider

    def to_dict(self) -> dict[str, list[str]]:
        return {
            "resource_providers": sorted(self.resource_providers),
            "certificate_providers": sorted(self.certificate_providers),
        }

    @classmethod
    def discover(cls, *, entry_points: metadata.EntryPoints | None = None) -> PluginRegistry:
        """Load providers exposed through npmctl entry point groups."""

        registry = cls()
        groups = entry_points if entry_points is not None else metadata.entry_points()
        _load_group(registry, groups, "npmctl.resource_providers", "resource")
        _load_group(registry, groups, "npmctl.certificate_providers", "certificate")
        return registry


def _load_group(registry: PluginRegistry, groups: metadata.EntryPoints, group: str, provider_type: str) -> None:
    for entry_point in groups.select(group=group):
        provider = entry_point.load()
        if isinstance(provider, type):
            provider = provider()
        if provider_type == "resource":
            _validate_resource_provider(entry_point.name, provider)
            registry.register_resource_provider(entry_point.name, provider)
        else:
            _validate_certificate_provider(entry_point.name, provider)
            registry.register_certificate_provider(entry_point.name, provider)


def _validate_resource_provider(name: str, provider: Any) -> None:
    for attr in ("kind", "identity", "natural_key", "desired_payload"):
        if not hasattr(provider, attr):
            raise ValueError(f"resource provider {name!r} missing {attr}")
    kind = getattr(provider, "kind")
    if not isinstance(kind, str) and not hasattr(kind, "value"):
        raise ValueError(f"resource provider {name!r} has invalid kind")


def _validate_certificate_provider(name: str, provider: Any) -> None:
    for attr in ("name", "resolve"):
        if not hasattr(provider, attr):
            raise ValueError(f"certificate provider {name!r} missing {attr}")
