"""npmctl exception taxonomy."""

from __future__ import annotations


class NpmctlError(Exception):
    """Base exception for all npmctl errors."""


class ValidationError(NpmctlError):
    """Input validation failed."""


class MetadataError(ValidationError):
    """Managed metadata was missing or invalid."""


class ConflictError(NpmctlError):
    """A requested mutation would violate ownership or integrity constraints."""


class CapabilityError(NpmctlError):
    """The live NPM API schema does not expose a required operation."""


class ApiError(NpmctlError):
    """The NPM API returned an error or an invalid response."""


class MigrationError(NpmctlError):
    """Desired-state schema migration failed."""
