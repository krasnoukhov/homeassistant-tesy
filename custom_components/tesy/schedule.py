"""Weekly program (schedule) helpers for the Tesy local API.

Devices on the ESP32 module expose three weekly programs as 21 fields,
``prgP{1..3}{MO..SU}``. Each value is a 48-character hex string: 24 bytes, one
per hour of the day, where every byte is the target temperature for that hour
(``0x32`` = 50 °C). ``FF`` marks an hour that has no program entry.

Shower models (BelliSlimo) store showers instead, counted down from ``FF``:
``0xFE`` = 1 shower, ``0xFD`` = 2. ``FF`` is still an hour with no entry, which
the panel shows as anti-freeze (``*``).

The fields can be written one day at a time with
``/api?name=prgP3MO&set=<48 hex chars>``.

This module has no Home Assistant dependencies so it can be unit tested alone.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

DAYS = ("MO", "TU", "WE", "TH", "FR", "SA", "SU")
ALL_DAYS = tuple(day.lower() for day in DAYS)
PROGRAMS = (1, 2, 3)
HOURS_PER_DAY = 24
EMPTY_SLOT = 0xFF

# Bounds accepted by the device for a scheduled hour. 14 °C means "heating off"
# for that hour (MyTESY shows a snowflake); 15-75 °C are real setpoints.
HEATING_OFF_TEMP = 14
MIN_SLOT_TEMP = HEATING_OFF_TEMP
MAX_SLOT_TEMP = 75

# Lowest showers for a scheduled hour on shower models; the highest is the
# heater's maximum (tmpMX). 0 showers would be FF, an empty hour.
MIN_SLOT_SHOWERS = 1

# Mode values ("mode" field) that run a weekly program, mapped to the program.
PROGRAM_MODES = {"1": 1, "2": 2, "3": 3}

# Local device time, reported in the "date" field.
DEVICE_DATE_FIELD = "date"
DEVICE_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def schedule_key(program: int, day: str) -> str:
    """Return the API field name for a program and day, e.g. ``prgP1MO``."""
    if program not in PROGRAMS:
        raise ValueError(f"Unknown program {program}")
    day = day.upper()
    if day not in DAYS:
        raise ValueError(f"Unknown day {day}")
    return f"prgP{program}{day}"


def whole_number(value: Any) -> int:
    """Return value as an int; reject fractions instead of truncating them.

    Accepts ints, numeric strings (``"2"``) and integral floats (``2.0``, as
    UI selectors may send them).
    """
    if isinstance(value, bool):
        raise ValueError(f"Expected a whole number, got {value!r}")
    number = float(value)  # ValueError / TypeError on non-numbers
    if not number.is_integer():
        raise ValueError(f"Expected a whole number, got {value!r}")
    return int(number)


def days_or_all(days: list[str]) -> list[str]:
    """Return the days to write; none picked (the UI sends []) means all."""
    return list(days) or list(ALL_DAYS)


def write_failure_message(
    program: int, written: list[str], day: str, reason: str
) -> str:
    """Error for a failed day of a multi-day write, naming the days written.

    Days are written one request at a time, so the earlier ones stay written.
    """
    done = f"wrote {', '.join(d.upper() for d in written)}, " if written else ""
    return f"P{program}: {done}failed at {day.upper()}: {reason}"


def decode_day(value: str, showers: bool = False) -> list[int | None]:
    """Decode a 48-char hex day into 24 hourly values (None = empty).

    The values are temperatures, or showers on shower models (showers True).
    """
    if not isinstance(value, str) or len(value) != HOURS_PER_DAY * 2:
        raise ValueError(f"Invalid schedule value: {value!r}")
    raw = bytes.fromhex(value)  # ValueError on bad hex
    if len(raw) != HOURS_PER_DAY:  # fromhex skips whitespace
        raise ValueError(f"Invalid schedule value: {value!r}")
    if showers:
        return [None if byte == EMPTY_SLOT else EMPTY_SLOT - byte for byte in raw]
    return [None if byte == EMPTY_SLOT else byte for byte in raw]


def encode_day(values: list[int | None], max_showers: int | None = None) -> str:
    """Encode 24 hourly values (None = empty) into the device format.

    The values are temperatures, or showers (1 to max_showers) when the
    heater's maximum showers is given.
    """
    if len(values) != HOURS_PER_DAY:
        raise ValueError(f"Expected {HOURS_PER_DAY} hourly values, got {len(values)}")
    result = bytearray()
    for value in values:
        if value is None:
            result.append(EMPTY_SLOT)
            continue
        value = int(value)
        if max_showers is not None:
            if not MIN_SLOT_SHOWERS <= value <= max_showers:
                raise ValueError(
                    f"Showers {value} outside {MIN_SLOT_SHOWERS}-{max_showers}"
                )
            result.append(EMPTY_SLOT - value)
            continue
        if not MIN_SLOT_TEMP <= value <= MAX_SLOT_TEMP:
            raise ValueError(
                f"Temperature {value} outside {MIN_SLOT_TEMP}-{MAX_SLOT_TEMP} °C"
            )
        result.append(value)
    return result.hex().upper()


def has_schedules(data: dict[str, Any]) -> bool:
    """Return True if the device reports weekly programs."""
    return schedule_key(1, DAYS[0]) in data


def get_program(
    data: dict[str, Any], program: int, showers: bool = False
) -> dict[str, list] | None:
    """Return one program as ``{"mo": [24 values], ...}``, or None if missing.

    The values are showers on shower models (showers True).
    """
    result: dict[str, list[int | None]] = {}
    for day in DAYS:
        value = data.get(schedule_key(program, day))
        if value is None:
            return None
        try:
            result[day.lower()] = decode_day(value, showers)
        except ValueError:
            return None
    return result


def device_now(data: dict[str, Any]) -> datetime | None:
    """Return the device local time from the ``date`` field."""
    value = data.get(DEVICE_DATE_FIELD)
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, DEVICE_DATE_FORMAT)
    except ValueError:
        return None


def scheduled_target(
    data: dict[str, Any], program: int, now: datetime | None = None
) -> int | None:
    """Return the program's target for the current hour of the device clock.

    Returns None when the time or the program is unknown, or the hour is empty.
    """
    if now is None:
        now = device_now(data)
    if now is None:
        return None
    value = data.get(schedule_key(program, DAYS[now.weekday()]))
    if value is None:
        return None
    try:
        return decode_day(value)[now.hour]
    except ValueError:
        return None


def active_program(data: dict[str, Any]) -> int | None:
    """Return the program number the device is running, or None."""
    if str(data.get("pwr")) == "0":
        return None  # powered off: the mode is kept but nothing runs
    return PROGRAM_MODES.get(str(data.get("mode")))


def active_target(
    data: dict[str, Any], now: datetime | None = None, use_schedule: bool = True
) -> float | None:
    """Return the target the device is working towards right now.

    ``tmpR`` holds it in every mode, including a weekly program, where it may
    already be the next hour's value while the heater warms up ahead of it.
    While a program runs and the heater is idle, the ModEco 2 (id 2004)
    firmware reports a placeholder below the slot range instead (``9``); the
    target is then taken from the program for the current hour. With
    use_schedule False (models without verified program support) ``tmpR`` is
    returned as is.
    """
    value = data.get("tmpR")
    try:
        reported = float(value)
    except (TypeError, ValueError):
        reported = None

    program = active_program(data)
    if (
        program is not None
        and use_schedule
        and has_schedules(data)
        and (reported is None or reported < MIN_SLOT_TEMP)
    ):
        target = scheduled_target(data, program, now)
        return None if target is None else float(target)
    return reported
