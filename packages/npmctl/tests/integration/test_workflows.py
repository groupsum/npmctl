from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[4]
WORKFLOWS = ROOT / ".github" / "workflows"


def _workflow(name: str) -> dict:
    return yaml.load((WORKFLOWS / name).read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def test_workflow_trigger_and_gate_semantics() -> None:
    ci = _workflow("ci.yml")
    e2e = _workflow("e2e-npm.yml")
    docs = _workflow("docs-ssot.yml")
    release = _workflow("release.yml")

    assert ci["on"]["push"]["branches"] == ["master"]
    assert "workflow_dispatch" in ci["on"]

    assert e2e["on"]["workflow_run"]["workflows"] == ["CI"]
    assert e2e["on"]["workflow_run"]["types"] == ["completed"]
    assert "workflow_run.conclusion == 'success'" in e2e["jobs"]["e2e"]["if"]

    assert docs["on"]["workflow_run"]["workflows"] == ["CI"]
    assert docs["on"]["workflow_run"]["types"] == ["completed"]
    assert "workflow_run.conclusion == 'success'" in docs["jobs"]["docs-ssot"]["if"]

    assert release["on"]["workflow_run"]["workflows"] == ["Real NPM E2E"]
    assert release["on"]["workflow_run"]["types"] == ["completed"]
    assert "workflow_run.conclusion == 'success'" in release["jobs"]["build"]["if"]
    assert release["jobs"]["publish"]["needs"] == "build"
    assert "startsWith(github.event.workflow_run.head_branch, 'v')" in release["jobs"]["publish"]["if"]
