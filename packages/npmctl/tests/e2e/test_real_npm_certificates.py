from __future__ import annotations

import os

import pytest

from npmctl.client import NpmClient

pytestmark = pytest.mark.npm


@pytest.mark.skipif(os.environ.get("NPMCTL_REAL_NPM") != "1", reason="real NPM E2E is opt-in")
def test_real_npm_certificate_capability_report() -> None:
    client = NpmClient(
        base_url=os.environ["NPM_BASE_URL"], identity=os.environ["NPM_IDENTITY"], secret=os.environ["NPM_SECRET"]
    )
    caps = client.capabilities()
    if not caps.certificates.list:
        pytest.skip("this NPM schema does not expose certificate list")
    assert isinstance(
        client.list_resource(__import__("npmctl.models", fromlist=["ResourceKind"]).ResourceKind.CERTIFICATE), tuple
    )
