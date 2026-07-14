"""Contract-envelope checks that never rewrite source documents."""

from __future__ import annotations

from typing import Any

from npmctl.contracts.registry import ContractRegistry
from npmctl.errors import ContractCompatibilityError

API_VERSION = "npmctl.com/v1"


def check_document(document: dict[str, Any], registry: ContractRegistry, *, strict: bool = False) -> list[str]:
    if document.get("apiVersion") != API_VERSION:
        raise ContractCompatibilityError("UNSUPPORTED_API_VERSION", f"apiVersion must be {API_VERSION!r}")
    kind = document.get("kind")
    version = document.get("schemaVersion")
    if not isinstance(kind, str) or not kind:
        raise ContractCompatibilityError("MISSING_CONTRACT_KIND", "kind must be a non-empty string")
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise ContractCompatibilityError("INVALID_SCHEMA_VERSION", "schemaVersion must be a positive integer")
    return registry.require_readable(kind, version, strict=strict)
