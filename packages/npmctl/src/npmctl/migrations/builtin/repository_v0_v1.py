"""Legacy repository layout to NpmctlRepository schema 1."""

from __future__ import annotations

from typing import Any


def migrate(document: dict[str, Any]) -> dict[str, Any]:
    name = str(document.get("name") or "npmctl-repository")
    return {
        "apiVersion": "npmctl.com/v1",
        "kind": "NpmctlRepository",
        "schemaVersion": 1,
        "metadata": {"name": name},
        "spec": dict(document.get("spec") or {}),
    }
