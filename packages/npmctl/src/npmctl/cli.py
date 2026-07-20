"""npmctl CLI compatibility facade backed by wyrmctl."""

from __future__ import annotations

from typing import Sequence

from wyrmctl import cli as _implementation
from wyrmctl.profile import NPMCTL_PROFILE, use_profile

globals().update({name: value for name, value in vars(_implementation).items() if name not in {"main", "build_parser"}})


def _plugin_registry_cls():
    global _PLUGIN_REGISTRY_IMPL
    if _PLUGIN_REGISTRY_IMPL is None:
        from wyrmctl.plugins import PluginRegistry
        _PLUGIN_REGISTRY_IMPL = PluginRegistry
    return _PLUGIN_REGISTRY_IMPL


def _npm_client_cls():
    global NpmClient
    if NpmClient is None:
        from wyrmctl.client import NpmClient as _NpmClient
        NpmClient = _NpmClient
    return NpmClient


def build_parser():
    with use_profile(NPMCTL_PROFILE):
        return _implementation.build_parser()


def main(argv: Sequence[str] | None = None) -> int:
    original_dispatch = _implementation._dispatch
    original_registry = _implementation._PLUGIN_REGISTRY_IMPL
    _implementation._dispatch = globals().get("_dispatch", original_dispatch)
    _implementation._PLUGIN_REGISTRY_IMPL = globals().get("_PLUGIN_REGISTRY_IMPL", original_registry)
    original_client = _implementation.NpmClient
    _implementation.NpmClient = globals().get("NpmClient", original_client)
    try:
        with use_profile(NPMCTL_PROFILE):
            return _implementation.main(argv)
    finally:
        _implementation._dispatch = original_dispatch
        _implementation._PLUGIN_REGISTRY_IMPL = original_registry
        _implementation.NpmClient = original_client