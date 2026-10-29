"""Extended features, enabled per heater model.

Weekly programs, time zone sync and the read-back after commands were
developed and tested on the ModEco 2 (id 2004), and later verified on the
BelliSlimo (id 2002), whose programs are in showers. Other models keep
the basic behaviour of the integration until they are verified: add their id
here once they are.

A feature is enabled only if the model lists it *and* the device reports the
fields it needs, so a firmware without them still gets the basic behaviour.
"""

from __future__ import annotations

import re
from typing import Any, Callable

FEATURE_SCHEDULE = "schedule"  # weekly programs P1-P3, tesy.set_schedule
FEATURE_TIMEZONE = "timezone"  # time zone sync, clock problem sensor
FEATURE_READBACK = "readback"  # poll ~2 s after a command

# Device type id (``id`` in /api?name=_all) -> features verified on it.
EXTENDED_MODELS: dict[str, frozenset[str]] = {
    "2004": frozenset(
        {FEATURE_SCHEDULE, FEATURE_TIMEZONE, FEATURE_READBACK}
    ),  # ModEco 2
    "2002": frozenset(
        {FEATURE_SCHEDULE, FEATURE_TIMEZONE, FEATURE_READBACK}
    ),  # BelliSlimo
}

_DAYS = ("MO", "TU", "WE", "TH", "FR", "SA", "SU")

# Fields a feature needs in the device data.
_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    FEATURE_SCHEDULE: tuple(f"prgP{p}{d}" for p in (1, 2, 3) for d in _DAYS),
    FEATURE_TIMEZONE: ("tz",),
}

# Older firmware (BelliSlimo Wi-Fi 0.26) reports ``tz`` as a number ("180"),
# not a POSIX string; writing a POSIX string there is untested.
_NUMERIC_TZ = re.compile(r"\s*[+-]?\d+\s*")

# Checks on the field values a feature needs, beyond them being present.
_VALUE_CHECKS: dict[str, Callable[[dict[str, Any]], bool]] = {
    FEATURE_TIMEZONE: lambda data: not _NUMERIC_TZ.fullmatch(str(data["tz"])),
}


def device_features(data: dict[str, Any] | None) -> frozenset[str]:
    """Return the extended features enabled for this device."""
    if not data:
        return frozenset()
    listed = EXTENDED_MODELS.get(str(data.get("id")), frozenset())
    return frozenset(
        feature
        for feature in listed
        if all(field in data for field in _REQUIRED_FIELDS.get(feature, ()))
        and _VALUE_CHECKS.get(feature, lambda _data: True)(data)
    )
