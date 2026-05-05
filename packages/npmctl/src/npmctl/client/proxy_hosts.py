"""Proxy-host client helpers."""

from npmctl.client.base import NpmClient
from npmctl.models import ResourceKind


def list_proxy_hosts(client: NpmClient):
    """List proxy hosts."""

    return client.list_resource(ResourceKind.PROXY_HOST)
