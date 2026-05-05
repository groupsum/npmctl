from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "ssot" / "index.md"


def render() -> str:
    registry = json.loads((ROOT / ".ssot" / "registry.json").read_text(encoding="utf-8"))
    return "\n".join(
        [
            "# SSOT index",
            "",
            f"Features: {len(registry.get('features', []))}",
            f"Claims: {len(registry.get('claims', []))}",
            f"Tests: {len(registry.get('tests', []))}",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render()
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != content:
            raise SystemExit("SSOT docs are stale; run scripts/render_ssot_docs.py")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
