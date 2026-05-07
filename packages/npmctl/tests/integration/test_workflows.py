from __future__ import annotations

import json
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
    publish_steps = release["jobs"]["publish"]["steps"]
    pypi_step = next(step for step in publish_steps if step.get("uses", "").startswith("pypa/"))
    assert pypi_step["with"]["skip-existing"] == "true"


def test_lander_deploy_workflow_is_dispatch_only_and_idempotent() -> None:
    workflow = _workflow("deploy-lander.yml")

    assert workflow["name"] == "Deploy npmctl.com Lander"
    assert set(workflow["on"]) == {"workflow_dispatch"}
    assert workflow["jobs"]["deploy"]["runs-on"]["group"] == "deployment"

    steps = workflow["jobs"]["deploy"]["steps"]
    assert all("cobycloud/actions" not in step.get("uses", "") for step in steps)

    deploy_script = next(step["run"] for step in steps if step.get("name") == "Deploy lander service")
    assert "docker compose version" in deploy_script
    assert "command -v docker-compose" in deploy_script
    assert "docker ps -a --filter name=npmctl_lander" in deploy_script
    assert "docker rm -f" in deploy_script
    assert "deploy/lander/compose.yml up -d --build lander" in deploy_script

    connect_script = next(step["run"] for step in steps if step.get("name") == "Connect NPM to lander network")
    assert "jc21/nginx-proxy-manager:2.10.4" in connect_script
    assert 'docker network connect npmctl_lander_net "$npm_container"' in connect_script

    verify_script = next(step["run"] for step in steps if step.get("name") == "Verify lander container")
    assert "docker inspect -f '{{.State.Running}}' npmctl_lander" in verify_script
    assert "Hello from the npmctl lander." in verify_script


def test_lander_compose_contract_and_static_page() -> None:
    compose = yaml.load(
        (ROOT / "deploy" / "lander" / "compose.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader
    )
    site = (ROOT / "deploy" / "lander" / "site" / "index.html").read_text(encoding="utf-8")

    assert "name" not in compose
    assert compose["version"] == "3.8"
    assert compose["services"]["lander"]["container_name"] == "npmctl_lander"
    assert compose["services"]["lander"]["networks"] == ["npmctl_lander_net"]
    assert compose["networks"]["npmctl_lander_net"]["name"] == "npmctl_lander_net"
    assert "wget -qO-" in compose["services"]["lander"]["healthcheck"]["test"][1]
    assert "npmctl.com" in site
    assert "Hello from the npmctl lander." in site


def test_governed_api_namespace_uses_npmctl_com() -> None:
    schema = json.loads((ROOT / "schemas" / "npmctl" / "desired-state.v1.schema.json").read_text(encoding="utf-8"))
    loader = (ROOT / "packages" / "npmctl" / "src" / "npmctl" / "loader.py").read_text(encoding="utf-8")
    model = (ROOT / "packages" / "npmctl" / "src" / "npmctl" / "models.py").read_text(encoding="utf-8")
    legacy_domain = "npmctl" + ".io"

    assert schema["properties"]["apiVersion"]["const"] == "npmctl.com/v1"
    assert 'EXPECTED_API_VERSION = "npmctl.com/v1"' in loader
    assert 'api_version: str = "npmctl.com/v1"' in model

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
