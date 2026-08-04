from wyrmctl.models import DesiredGenericResource, DesiredState, ExistingState, ResourceKind
from wyrmctl.planner import compute_plan
from wyrmctl.profile import NPMCTL_PROFILE, use_profile
from wyrmctl.schema import Capabilities


def _route() -> DesiredGenericResource:
    return DesiredGenericResource.from_mapping(
        ResourceKind.QUIC_PASSTHROUGH_HOST,
        {
            "server_name": "present.example",
            "target": "presentation-backend",
            "target_port": 4443,
            "meta": {
                "managed_by": "npmctl",
                "owner": "presentation-demo",
                "resource_id": "quic.presentation",
            },
        },
        path="quicPassthroughHosts[0]",
    )


def test_npmctl_fails_closed_and_recommends_portwyrm() -> None:
    with use_profile(NPMCTL_PROFILE):
        plan = compute_plan(
            desired=DesiredState(quic_passthrough_hosts=(_route(),)),
            existing=ExistingState(),
            capabilities=Capabilities.empty(),
        )

    assert not plan.ok
    assert plan.conflicts[0].code == "missing_create_capability"
    assert plan.conflicts[0].message == (
        "Nginx Proxy Manager cannot manage hostname-routed QUIC passthrough; "
        "use Portwyrm with wyrmctl for this resource"
    )


def test_npmctl_allows_provider_advertised_quic_capability() -> None:
    with use_profile(NPMCTL_PROFILE):
        plan = compute_plan(
            desired=DesiredState(quic_passthrough_hosts=(_route(),)),
            existing=ExistingState(),
            capabilities=Capabilities.full_for_tests(),
        )

    assert plan.ok
    assert len(plan.by_action("create")) == 1
