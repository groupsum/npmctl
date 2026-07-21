from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[4]
WORKFLOWS = ROOT / ".github" / "workflows"
ACTIONS = ROOT / ".github" / "actions"


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
        "3.14",
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
    gate_run = next(step["run"] for step in release["jobs"]["gates"]["steps"] if "ci.yml" in step.get("run", ""))
    assert "docs-ssot.yml" in gate_run
    assert "python-matrix.yml" in gate_run
    assert "live-npm-gate.yml" in gate_run
    prepare_steps = release["jobs"]["prepare"]["steps"]
    bump_script = next(step["run"] for step in prepare_steps if step.get("name") == "Bump release metadata")
    commit_script = next(step["run"] for step in prepare_steps if step.get("name") == "Commit release metadata")
    provider_pyprojects = [
        "packages/npmctl-cloudflare/pyproject.toml",
        "packages/npmctl-digitalocean/pyproject.toml",
        "packages/npmctl-godaddy/pyproject.toml",
        "packages/npmctl-namecheap/pyproject.toml",
        "packages/npmctl-route53/pyproject.toml",
    ]
    for pyproject in provider_pyprojects:
        assert pyproject in bump_script
        assert pyproject in commit_script
    assert release["jobs"]["build"]["needs"] == ["prepare", "gates"]
    assert release["jobs"]["publish"]["needs"] == ["prepare", "build"]
    assert release["jobs"]["publish"]["environment"] == "pypi"
    publish_steps = release["jobs"]["publish"]["steps"]
    pypi_steps = [step for step in publish_steps if step.get("uses", "").startswith("pypa/")]
    assert len(pypi_steps) == 2
    trusted_publishing_step, token_fallback_step = pypi_steps
    assert trusted_publishing_step["id"] == "pypi-trusted-publishing"
    assert trusted_publishing_step["continue-on-error"] == "true"
    assert trusted_publishing_step["with"]["skip-existing"] == "true"
    assert "steps.pypi-trusted-publishing.outcome == 'failure'" in token_fallback_step["if"]
    assert token_fallback_step["with"]["password"] == "${{ secrets.PYPI_API_TOKEN }}"
    assert token_fallback_step["with"]["skip-existing"] == "true"
    gh_release_index = next(
        index for index, step in enumerate(publish_steps) if step.get("uses", "").startswith("softprops/")
    )
    token_fallback_index = publish_steps.index(token_fallback_step)
    assert gh_release_index > token_fallback_index
    assert "inputs.publish_github_release" in publish_steps[gh_release_index]["if"]

    release_build = yaml.load(
        (ACTIONS / "npmctl-release-build" / "action.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader
    )
    build_script = release_build["runs"]["steps"][0]["run"]
    assert "uv build --package npmctl\n" in build_script
    for package in [
        "npmctl-cloudflare",
        "npmctl-digitalocean",
        "npmctl-godaddy",
        "npmctl-namecheap",
        "npmctl-route53",
    ]:
        assert f"uv build --package {package}" in build_script


def test_governed_api_namespace_uses_npmctl_com() -> None:
    schema = json.loads((ROOT / "schemas" / "npmctl" / "desired-state.v2.schema.json").read_text(encoding="utf-8"))
    facade = (ROOT / "packages" / "npmctl" / "src" / "npmctl" / "__init__.py").read_text(encoding="utf-8")
    cli = (ROOT / "packages" / "npmctl" / "src" / "npmctl" / "cli.py").read_text(encoding="utf-8")
    legacy_domain = "npmctl" + ".io"

    assert schema["properties"]["apiVersion"]["const"] == "npmctl.com/v1"
    assert schema["properties"]["schemaVersion"]["const"] == 2
    assert "NPMCTL_PROFILE" in facade
    assert "set_profile(NPMCTL_PROFILE)" in facade
    assert "use_profile(NPMCTL_PROFILE)" in cli

    checked_paths = [
        ROOT / "README.md",
        ROOT / "packages" / "npmctl" / "README.md",
        ROOT / "docs",
        ROOT / "examples",
        ROOT / "schemas",
        ROOT / "packages" / "npmctl" / "src",
        ROOT / "packages" / "npmctl" / "tests",
    ]
    matches = []
    for path in checked_paths:
        files = path.rglob("*") if path.is_dir() else [path]
        for candidate in files:
            if candidate.is_file() and candidate.suffix.lower() in {".json", ".md", ".py", ".toml", ".yaml", ".yml"}:
                if legacy_domain in candidate.read_text(encoding="utf-8"):
                    matches.append(candidate.relative_to(ROOT).as_posix())

    assert matches == []
