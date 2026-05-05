from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    for path in sorted((ROOT / "schemas").rglob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            json.load(handle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
