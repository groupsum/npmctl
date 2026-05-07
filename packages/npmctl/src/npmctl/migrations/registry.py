"""Desired-state migration registry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from npmctl.errors import MigrationError
from npmctl.loader import EXPECTED_API_VERSION, SUPPORTED_EXTENSIONS
from npmctl.migrations.base import MigrationResult

CURRENT_SCHEMA_VERSION = 2


def needs_migration(document: dict[str, Any]) -> bool:
    """Return true when a document is not at the current schema version."""

    return document.get("apiVersion") != EXPECTED_API_VERSION or document.get("schemaVersion") != CURRENT_SCHEMA_VERSION


def migrate_document(document: dict[str, Any]) -> tuple[dict[str, Any], bool, int | None]:
    """Migrate an in-memory desired-state document to the current schema."""

    if not isinstance(document, dict):
        raise MigrationError("desired-state document must be an object")
    before = document.get("schemaVersion")
    if before == CURRENT_SCHEMA_VERSION and document.get("apiVersion") == EXPECTED_API_VERSION:
        return dict(document), False, CURRENT_SCHEMA_VERSION
    if before not in (None, 0, 1):
        raise MigrationError(f"unsupported desired-state schemaVersion: {before}")
    migrated = dict(document)
    migrated.setdefault("proxy_hosts", [])
    migrated.setdefault("certificates", [])
    migrated.setdefault("access_lists", [])
    migrated.setdefault("dns_records", [])
    migrated["apiVersion"] = EXPECTED_API_VERSION
    migrated["schemaVersion"] = CURRENT_SCHEMA_VERSION
    return migrated, True, before if isinstance(before, int) else None


def migrate_path(path: str | Path, *, write: bool) -> list[MigrationResult]:
    """Migrate a file or directory. Write only when requested."""

    root = Path(path)
    if not root.exists():
        raise MigrationError(f"path does not exist: {root}")
    files = (
        [root]
        if root.is_file()
        else sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS)
    )
    results: list[MigrationResult] = []
    for file_path in files:
        doc = _read_any(file_path)
        migrated, changed, before = migrate_document(doc)
        if changed and write:
            _write_any(file_path, migrated)
        results.append(
            MigrationResult(
                path=file_path,
                changed=changed,
                before_version=before,
                after_version=CURRENT_SCHEMA_VERSION,
                document=migrated,
            )
        )
    return results


def _read_any(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    parsed = json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)
    if parsed is None:
        parsed = {}
    if not isinstance(parsed, dict):
        raise MigrationError(f"{path} must contain an object")
    return parsed


def _write_any(path: Path, doc: dict[str, Any]) -> None:
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
