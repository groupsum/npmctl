"""Desired-state migrations."""

from npmctl.migrations.builtin import BUILTIN_MIGRATIONS
from npmctl.migrations.graph import MigrationGraph, MigrationStep
from npmctl.migrations.manifest import MigrationManifest, reject_migration_only_operations
from npmctl.migrations.executor import execute_migration
from npmctl.migrations.planner import plan_schema_migration
from npmctl.migrations.registry import CURRENT_SCHEMA_VERSION, migrate_document, migrate_path, needs_migration

__all__ = [
    "BUILTIN_MIGRATIONS",
    "CURRENT_SCHEMA_VERSION",
    "MigrationGraph",
    "MigrationManifest",
    "execute_migration",
    "plan_schema_migration",
    "MigrationStep",
    "migrate_document",
    "migrate_path",
    "needs_migration",
    "reject_migration_only_operations",
]
