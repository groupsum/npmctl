from __future__ import annotations

import os

import pytest

from npmctl.client import NpmClient
from npmctl.models import ResourceKind

pytestmark = pytest.mark.npm


@pytest.mark.skipif(os.environ.get("NPMCTL_REAL_NPM") != "1", reason="real NPM E2E is opt-in")
def test_real_npm_access_list_capability_report() -> None:
    client = NpmClient(
        base_url=os.environ["NPM_BASE_URL"], identity=os.environ["NPM_IDENTITY"], secret=os.environ["NPM_SECRET"]
    )
    caps = client.capabilities()
    if not caps.access_lists.list:
        pytest.skip("this NPM schema does not expose access-list list")
    assert isinstance(client.list_resource(ResourceKind.ACCESS_LIST), tuple)
