from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SSOT_DOCS = ROOT / "docs" / "ssot"
REGISTRY = ROOT / ".ssot" / "registry.json"


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = ", ".join(str(item) for item in value)
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *["| " + " | ".join(_cell(value) for value in row) + " |" for row in rows],
    ]


def _render_index(registry: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# SSOT index",
            "",
            f"Features: {len(registry.get('features', []))}",
            f"Claims: {len(registry.get('claims', []))}",
            f"Tests: {len(registry.get('tests', []))}",
            f"Evidence: {len(registry.get('evidence', []))}",
            f"Profiles: {len(registry.get('profiles', []))}",
            f"Boundaries: {len(registry.get('boundaries', []))}",
            f"Releases: {len(registry.get('releases', []))}",
            "",
            "- [Features](features.md)",
            "- [Claims](claims.md)",
            "- [Tests](tests.md)",
            "- [ADRs](adrs.md)",
            "- [Specs](specs.md)",
            "",
        ]
    )


def _render_features(registry: dict[str, Any]) -> str:
    features = sorted(registry.get("features", []), key=lambda row: row["id"])
    rows = [
        [
            row["id"],
            row["title"],
            row["implementation_status"],
            row.get("plan", {}).get("horizon"),
            row.get("plan", {}).get("target_claim_tier"),
            row.get("claim_ids", []),
            row.get("test_ids", []),
        ]
        for row in features
    ]
    return "\n".join(
        [
            "# Features",
            "",
            f"Generated entries: {len(features)}",
            "",
            *_table(["id", "title", "implementation_status", "horizon", "target_tier", "claims", "tests"], rows),
            "",
        ]
    )


def _render_claims(registry: dict[str, Any]) -> str:
    claims = sorted(registry.get("claims", []), key=lambda row: row["id"])
    rows = [
        [
            row["id"],
            row["title"],
            row["status"],
            row["tier"],
            row["kind"],
            row.get("feature_ids", []),
            row.get("test_ids", []),
            row.get("evidence_ids", []),
        ]
        for row in claims
    ]
    return "\n".join(
        [
            "# Claims",
            "",
            f"Generated entries: {len(claims)}",
            "",
            *_table(["id", "title", "status", "tier", "kind", "features", "tests", "evidence"], rows),
            "",
        ]
    )


def _render_tests(registry: dict[str, Any]) -> str:
    tests = sorted(registry.get("tests", []), key=lambda row: row["id"])
    rows = [
        [
            row["id"],
            row["title"],
            row["status"],
            row["kind"],
            row.get("path", ""),
            row.get("feature_ids", []),
            row.get("claim_ids", []),
            row.get("evidence_ids", []),
        ]
        for row in tests
    ]
    return "\n".join(
        [
            "# Tests",
            "",
            f"Generated entries: {len(tests)}",
            "",
            *_table(["id", "title", "status", "kind", "test_path", "features", "claims", "evidence"], rows),
            "",
        ]
    )


def _render_adrs(registry: dict[str, Any]) -> str:
    adrs = sorted(registry.get("adrs", []), key=lambda row: row["id"])
    rows = [[row["id"], row["number"], row["title"], row["status"]] for row in adrs]
    return "\n".join(
        [
            "# ADRs",
            "",
            f"Generated entries: {len(adrs)}",
            "",
            *_table(["id", "number", "title", "status"], rows),
            "",
        ]
    )


def _render_specs(registry: dict[str, Any]) -> str:
    specs = sorted(registry.get("specs", []), key=lambda row: row["id"])
    rows = [[row["id"], row["number"], row["title"], row["status"], row["kind"]] for row in specs]
    return "\n".join(
        [
            "# Specs",
            "",
            f"Generated entries: {len(specs)}",
            "",
            *_table(["id", "number", "title", "status", "kind"], rows),
            "",
        ]
    )


def render_all() -> dict[Path, str]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {
        SSOT_DOCS / "index.md": _render_index(registry),
        SSOT_DOCS / "features.md": _render_features(registry),
        SSOT_DOCS / "claims.md": _render_claims(registry),
        SSOT_DOCS / "tests.md": _render_tests(registry),
        SSOT_DOCS / "adrs.md": _render_adrs(registry),
        SSOT_DOCS / "specs.md": _render_specs(registry),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = render_all()
    if args.check:
        stale = [
            path
            for path, content in rendered.items()
            if not path.exists() or path.read_text(encoding="utf-8") != content
        ]
        if stale:
            names = ", ".join(str(path.relative_to(ROOT)) for path in stale)
            raise SystemExit(f"SSOT docs are stale; run scripts/render_ssot_docs.py ({names})")
        return 0
    SSOT_DOCS.mkdir(parents=True, exist_ok=True)
    for path, content in rendered.items():
        path.write_text(content, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
