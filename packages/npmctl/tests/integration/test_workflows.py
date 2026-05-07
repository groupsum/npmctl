from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[4]
WORKFLOWS = ROOT / ".github" / "workflows"


def _workflow(name: str) -> dict:
    return yaml.load((WORKFLOWS / name).read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def test_workflow_trigger_and_gate_semantics() -> None:
    ci = _workflow("ci.yml")
    matrix = _workflow("python-matrix.yml")
    live_npm = _workflow("live-npm-gate.yml")
    docs = _workflow("docs-ssot.yml")
    release = _workflow("release.yml")

    assert ci["on"]["push"]["branches"] == ["master"]
    assert "workflow_dispatch" in ci["on"]

    assert matrix["on"]["push"]["branches"] == ["master", "v*"]
    assert "workflow_dispatch" in matrix["on"]
    assert matrix["jobs"]["pytest"]["strategy"]["matrix"]["python-version"] == [
        "3.10",
        "3.11",
        "3.12",
        "3.13",
    ]

    assert live_npm["name"] == "Live NPM Gate"
    assert "workflow_dispatch" in live_npm["on"]
    assert "workflow_run" not in live_npm["on"]

    assert docs["on"]["workflow_run"]["workflows"] == ["CI"]
    assert docs["on"]["workflow_run"]["types"] == ["completed"]
    assert "workflow_run.conclusion == 'success'" in docs["jobs"]["docs-ssot"]["if"]

    dispatch_inputs = release["on"]["workflow_dispatch"]["inputs"]
    assert dispatch_inputs["publish_github_release"]["type"] == "boolean"
    assert dispatch_inputs["publish_pypi"]["type"] == "boolean"
    assert "workflow_run" not in release["on"]
    assert "ci.yml" in release["jobs"]["gates"]["steps"][0]["run"]
    assert "docs-ssot.yml" in release["jobs"]["gates"]["steps"][0]["run"]
    assert "python-matrix.yml" in release["jobs"]["gates"]["steps"][0]["run"]
    assert "live-npm-gate.yml" in release["jobs"]["gates"]["steps"][0]["run"]
    assert release["jobs"]["build"]["needs"] == ["prepare", "gates"]
    assert release["jobs"]["publish"]["needs"] == ["prepare", "build"]
