"""CLI configuration file support."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from npmctl.errors import ValidationError

CONFIG_FIELDS = frozenset({"base_url", "identity", "secret", "timeout", "output"})


def load_config(path: str | None) -> dict[str, Any]:
    """Load npmctl TOML config values."""

    if not path:
        return {}
    config_path = Path(path)
    try:
        parsed = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValidationError(f"failed to read config file {config_path}: {exc}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ValidationError(f"failed to parse config file {config_path}: {exc}") from exc
    if not isinstance(parsed, dict):  # pragma: no cover - tomllib.loads always returns a dict
        raise ValidationError("config file must contain a TOML table")
    raw = parsed.get("npmctl", parsed)
    if not isinstance(raw, dict):
        raise ValidationError("config file [npmctl] must be a table")
    return {key: raw[key] for key in CONFIG_FIELDS if key in raw}


def apply_config(args: Any, values: dict[str, Any]) -> None:
    """Fill unset argparse fields from config values."""

    for field_name, value in values.items():
        current = getattr(args, field_name, None)
        if current in (None, ""):
            setattr(args, field_name, value)
