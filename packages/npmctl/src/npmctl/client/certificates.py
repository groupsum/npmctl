"""Certificate client helpers."""

from npmctl.client.base import NpmClient
from npmctl.models import ResourceKind


def list_certificates(client: NpmClient):
    """List SSL certificates."""

    return client.list_resource(ResourceKind.CERTIFICATE)
