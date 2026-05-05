"""Access-list client helpers."""

from npmctl.client.base import NpmClient
from npmctl.models import ResourceKind


def list_access_lists(client: NpmClient):
    """List access lists."""

    return client.list_resource(ResourceKind.ACCESS_LIST)
