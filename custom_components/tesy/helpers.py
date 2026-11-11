"""Helpers for the Tesy integration that do not depend on Home Assistant."""

from __future__ import annotations

from typing import Any

from .const import (
    ATTR_CDT,
    ATTR_ERROR,
    ATTR_IS_HEATING,
    ATTR_MAX_SHOWERS,
    ATTR_POWER,
    DOMAIN,
    TESY_DEVICE_TYPES,
    TESY_MODE_P1,
    TESY_MODE_P2,
    TESY_MODE_P3,
    TESY_MODE_EC2,
    TESY_MODE_EC3,
    UNIT_SHOWERS,
)

# Error codes that mean "no error", as in the MyTESY app ("00" on the new
# API, "0" on the old one)
NO_ERROR = ("0", "00")

# Failed polls in a row that keep the last data instead of making the device
# unavailable
MAX_TOLERATED_FAILED_POLLS = 1

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
    # A zero maximum would make the Eco modes set a target of zero showers
    if not value.isdecimal() or int(value) == 0:
        return default
    return int(value)


def uses_showers(device_id: Any, old_api: bool) -> bool:
    """Return True if the device reports hot water in showers, not degrees.

    Only the new API is covered: old API shower devices report different
    fields (cur_shower, ref_shower, max_shower) that are not mapped yet.
    """
    if old_api:
        return False
    device_type = TESY_DEVICE_TYPES.get(str(device_id), {})
    return bool(device_type.get("use_showers", False))


def is_heating(data: dict[str, Any], power_just_on: bool = False) -> bool | None:
    """Return True while a heating element is on, or None if unknown.

    Right after power-on the heater still reports the previous flag for about
    a second, so it isn't trusted until the next poll.
    """
    value = str(data.get(ATTR_IS_HEATING, "")).strip()
    if value not in ("0", "1"):
        return None
    if power_just_on:
        return False
    # Like the MyTESY app, a heater that is switched off is not heating
    if str(data.get(ATTR_POWER, "1")) == "0":
        return False
    return value == "1"


def has_error(data: dict[str, Any]) -> bool | None:
    """Return True if the heater reports an error, or None if unknown.

    Same rule as the MyTESY app: any code other than 0 / 00. The code is not
    decoded, since its numbering differs per model and isn't documented.
    """
    value = data.get(ATTR_ERROR)
    value = "" if value is None else str(value).strip()
    if not value:
        return None
    return value not in NO_ERROR


def ready_in(data: dict[str, Any]) -> int | None:
    """Return the minutes until the heater reaches its target, or None.

    ``cdt`` counts down while heating. While idle the BelliSlimo leaves a
    minute or two in it, so a heater that reports it isn't heating (``ht``
    0) is ready now. Without ``ht`` the countdown is shown as reported.

    While the heater is switched off the BelliSlimo keeps calculating ``cdt``
    (and reports ``ht`` 1): the time it would need to reach the target once
    switched on, which moves as the water cools or is used. It's shown as is.
    """
    value = str(data.get(ATTR_CDT, "")).strip()
    if not value.isdecimal():
        return None
    if str(data.get(ATTR_IS_HEATING, "")).strip() == "0":
        return 0
    return int(value)


def shower_unit(translations: dict[str, str]) -> str:
    """Return the shower unit word from the "common" translations.

    Falls back to the English unit if the language has none.
    """
    return translations.get(f"component.{DOMAIN}.common.shower_unit", UNIT_SHOWERS)


def tolerate_failed_poll(failed_polls: int, has_data: bool) -> bool:
    """Return True if a failed poll keeps the last data.

    `failed_polls` counts the failed polls in a row, including this one. Without
    data (the first poll) there is nothing to keep.
    """
    return has_data and failed_polls <= MAX_TOLERATED_FAILED_POLLS
