"""Route 53 DNS response models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class Route53Zone:
    """One Route 53 hosted zone."""

    zone_id: str
    name: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> Route53Zone:
        return cls(zone_id=str(raw.get("Id", "")).split("/")[-1], name=_dns_name(str(raw.get("Name", ""))))


@dataclass(frozen=True, slots=True)
class Route53Record:
    """One Route 53 resource record set."""

    name: str
    type: str
    values: tuple[str, ...]
    ttl: int | None = None

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> Route53Record:
        records = raw.get("ResourceRecords", [])
        alias_target = raw.get("AliasTarget")
        values = tuple(str(item.get("Value", "")) for item in records if isinstance(item, Mapping))
        if not values and isinstance(alias_target, Mapping):
            values = (str(alias_target.get("DNSName", "")),)
        return cls(
            name=_dns_name(str(raw.get("Name", ""))),
            type=str(raw.get("Type", "")).upper(),
            values=values,
            ttl=_optional_int(raw.get("TTL")),
        )

    def to_dict(self) -> dict[str, str | int | tuple[str, ...] | None]:
        return {
            "id": None,
            "name": self.name,
            "type": self.type,
            "value": self.values[0] if self.values else "",
            "values": self.values,
            "ttl": self.ttl,
        }


def _dns_name(value: str) -> str:
    return value.strip().lower().rstrip(".")


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)
