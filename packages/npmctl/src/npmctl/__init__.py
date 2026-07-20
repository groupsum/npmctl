"""npmctl compatibility distribution backed by wyrmctl."""

from __future__ import annotations

import importlib
import pkgutil
import sys

from wyrmctl import __version__
from wyrmctl.profile import NPMCTL_PROFILE, set_profile

set_profile(NPMCTL_PROFILE)
_wyrmctl = importlib.import_module("wyrmctl")
for _module in pkgutil.walk_packages(_wyrmctl.__path__, "wyrmctl."):
    if _module.name in {"wyrmctl.cli", "wyrmctl.__main__"}:
        continue
    _legacy_name = "npmctl" + _module.name[len("wyrmctl"):]
    _loaded = importlib.import_module(_module.name)
    sys.modules.setdefault(_legacy_name, _loaded)
    if _legacy_name.count(".") == 1:
        _root = _legacy_name.split(".", 1)[1]
        setattr(sys.modules[__name__], _root, _loaded)

__all__ = ["__version__"]