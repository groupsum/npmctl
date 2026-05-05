#!/usr/bin/env bash
set -euo pipefail
uv run ruff check .
uv run ruff format --check .
uv run yamllint .
uv run python scripts/validate_schemas.py
uv run pytest
uv run ssot validate . --write-report
uv run python tools/render_ssot_docs.py --check
