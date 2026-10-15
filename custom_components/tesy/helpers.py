"""Helpers for the Tesy integration that do not depend on Home Assistant."""

from __future__ import annotations

from typing import Any

from .const import ATTR_MAX_SHOWERS


def to_float(value: Any) -> float | None:
    """Return value as float, or None if it is missing or not numeric."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def max_showers(data: dict[str, Any], default: int) -> int:
    """Return the maximum showers reported by the device, or default."""
    value = str(data.get(ATTR_MAX_SHOWERS, ""))
    return int(value) if value.isdecimal() else default
