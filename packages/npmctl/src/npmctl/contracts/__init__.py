"""Public contract compatibility API."""

from npmctl.contracts.builtin import BUILTIN_CONTRACTS, build_builtin_registry
from npmctl.contracts.canonical import canonical_json, canonicalize, semantic_digest
from npmctl.contracts.compatibility import API_VERSION, check_document
from npmctl.contracts.registry import ContractRegistry
from npmctl.contracts.types import ContractSupport, DocumentEnvelope

__all__ = [
    "API_VERSION",
    "BUILTIN_CONTRACTS",
    "ContractRegistry",
    "ContractSupport",
    "DocumentEnvelope",
    "build_builtin_registry",
    "canonical_json",
    "canonicalize",
    "check_document",
    "semantic_digest",
]
