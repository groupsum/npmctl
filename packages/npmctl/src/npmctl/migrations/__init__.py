"""Desired-state migrations."""

from npmctl.migrations.registry import CURRENT_SCHEMA_VERSION, migrate_path, migrate_document, needs_migration

__all__ = ["CURRENT_SCHEMA_VERSION", "migrate_document", "migrate_path", "needs_migration"]
