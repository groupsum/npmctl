"""CLI output formatting."""

from __future__ import annotations

import json
import sys
from typing import Any

from npmctl.planner import Plan


def write_output(output: str, payload: Any, text: str) -> None:
    """Write JSON or text output to stdout."""

    if output == "json":
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True))
        sys.stdout.write("\n")
    else:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")


def write_error(output: str, code: str, message: str) -> None:
    """Write JSON or text error output to stderr."""

    if output == "json":
        sys.stderr.write(
            json.dumps({"ok": False, "error": {"code": code, "message": message}}, indent=2, sort_keys=True)
        )
        sys.stderr.write("\n")
    else:
        sys.stderr.write(f"{code}: {message}\n")


def format_plan_text(plan: Plan) -> str:
    """Format a plan for humans."""

    payload = plan.to_dict()
    lines = [f"plan ok: {str(plan.ok).lower()}", f"existing: {payload['existing_count']}"]
    for key, value in payload["summary"].items():
        lines.append(f"{key}: {value}")
    for operation in plan.operations:
        rid = operation.resource_id or "-"
        lines.append(f"  {operation.action.value:<6} {operation.kind.value:<12} {rid} {operation.reason}")
        for field, values in operation.diff.items():
            lines.append(f"    ~ {field}: {values.get('actual')!r} -> {values.get('desired')!r}")
    for conflict in plan.conflicts:
        lines.append(f"  ! {conflict.code}: {conflict.message}")
    return "\n".join(lines)
