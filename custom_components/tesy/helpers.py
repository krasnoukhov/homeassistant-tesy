"""Helpers for the Tesy integration that do not depend on Home Assistant."""

from __future__ import annotations

from typing import Any

from .const import (
    ATTR_MAX_SHOWERS,
    TESY_MODE_P1,
    TESY_MODE_P2,
    TESY_MODE_P3,
    TESY_MODE_EC2,
    TESY_MODE_EC3,
)

# Same values as homeassistant.components.water_heater STATE_PERFORMANCE/STATE_ECO
STATE_PERFORMANCE = "performance"
STATE_ECO = "eco"

# Operation mode -> Tesy "mode" value
OPERATION_TO_TESY_MODE = {
    STATE_PERFORMANCE: "0",
    TESY_MODE_P1: "1",
    TESY_MODE_P2: "2",
    TESY_MODE_P3: "3",
    STATE_ECO: "4",
    TESY_MODE_EC2: "5",
    TESY_MODE_EC3: "6",
}
TESY_MODE_TO_OPERATION = {
    tesy: operation for operation, tesy in OPERATION_TO_TESY_MODE.items()
}


def tesy_mode(operation_mode: str) -> str:
    """Return the Tesy "mode" value for an operation mode."""
    if operation_mode not in OPERATION_TO_TESY_MODE:
        raise ValueError(f"Unsupported operation mode: {operation_mode}")
    return OPERATION_TO_TESY_MODE[operation_mode]


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
