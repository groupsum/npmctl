from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
import yaml

from npmctl.cli import main

pytestmark = pytest.mark.npm


@pytest.mark.skipif(os.environ.get("NPMCTL_REAL_NPM") != "1", reason="real NPM E2E is opt-in")
def test_real_npm_plan_apply_adopt_proxy_host(tmp_path: Path) -> None:
    domain = f"npmctl-ci-{uuid.uuid4().hex[:10]}.example.invalid"
    doc = {
        "apiVersion": "npmctl.io/v1",
        "schemaVersion": 1,
        "proxy_hosts": [
            {
                "domain_names": [domain],
                "forward_host": "127.0.0.1",
                "forward_port": 8080,
                "meta": {"managed_by": "npmctl", "owner": "ci", "resource_id": f"proxy.{domain}"},
            }
        ],
    }
    path = tmp_path / "desired.yaml"
    path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    common = [
        "--base-url",
        os.environ["NPM_BASE_URL"],
        "--identity",
        os.environ["NPM_IDENTITY"],
        "--secret",
        os.environ["NPM_SECRET"],
    ]
    assert main([*common, "plan", str(path)]) == 0
    assert main([*common, "apply", str(path)]) == 0
    assert main([*common, "apply", str(path)]) == 0
