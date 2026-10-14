"""Extended features, enabled per heater model.

Weekly programs were developed and tested on the ModEco 2 (id 2004). Other
models keep the basic behaviour of the integration until they are verified:
add their id here once they are.

A feature is enabled only if the model lists it *and* the device reports the
fields it needs, so a firmware without them still gets the basic behaviour.
"""

from __future__ import annotations

from typing import Any

FEATURE_SCHEDULE = "schedule"  # weekly programs P1-P3, tesy.set_schedule

# Device type id (``id`` in /api?name=_all) -> features verified on it.
EXTENDED_MODELS: dict[str, frozenset[str]] = {
    "2004": frozenset({FEATURE_SCHEDULE}),  # ModEco 2
}

_DAYS = ("MO", "TU", "WE", "TH", "FR", "SA", "SU")

# Fields a feature needs in the device data.
_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    FEATURE_SCHEDULE: tuple(f"prgP{p}{d}" for p in (1, 2, 3) for d in _DAYS),
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
    )
