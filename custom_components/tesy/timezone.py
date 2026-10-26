"""Device clock and time zone helpers for the Tesy local API.

The ESP32 module takes UTC from the network and converts it to local time with
a POSIX TZ string held in ``tz`` (``EET-2EEST,M3.5.0/3,M10.5.0/4`` for Kyiv).
That field can be written with ``/api?name=tz&set=<string>``; the clock itself
cannot be set over the API.

The POSIX string for an IANA zone is the footer line of its TZif v2+ file, so
it is read from the same tz database that Python's ``zoneinfo`` uses. The
footer only describes the rules after the file's last explicit transition, so
it is checked against the zone for the coming months and rejected if the two
disagree (Africa/Casablanca, for example, keeps its Ramadan changes in the
transition table): such a zone cannot be expressed in one POSIX string.

This module has no Home Assistant dependencies so it can be unit tested alone.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from importlib import resources
from pathlib import Path
import re
import zoneinfo

TZ_FIELD = "tz"
DATE_FIELD = "date"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Clock offset (device local time vs Home Assistant local time) that counts as
# a problem. Polling and network delays stay well below this.
MAX_CLOCK_OFFSET = 300

_POSIX_TZ = re.compile(r"^[A-Za-z<][-+A-Za-z0-9<>,./:]*$")
_IANA_NAME = re.compile(r"^[A-Za-z0-9_+-]+(/[A-Za-z0-9_+-]+)*$")


def posix_tz_from_tzif(content: bytes) -> str | None:
    """Return the POSIX TZ footer of a TZif v2+ file, or None."""
    if not content.startswith(b"TZif") or len(content) < 5 or content[4:5] < b"2":
        return None
    if not content.endswith(b"\n"):
        return None
    start = content.rfind(b"\n", 0, len(content) - 1)
    if start < 0:
        return None
    footer = content[start + 1 : -1].decode("ascii", "ignore")
    return footer if footer and _POSIX_TZ.match(footer) else None


# ---- POSIX TZ evaluation (enough to check a string against the tz database)

_NAME = r"(?:<[^>]+>|[A-Za-z]{3,})"
_OFFSET = r"[+-]?\d{1,3}(?::\d{1,2}){0,2}"
_RULE = r"(?:J\d{1,3}|\d{1,3}|M\d{1,2}\.\d\.\d)(?:/" + _OFFSET + ")?"
_POSIX_FULL = re.compile(
    rf"^(?P<std>{_NAME})(?P<std_off>{_OFFSET})"
    rf"(?:(?P<dst>{_NAME})(?P<dst_off>{_OFFSET})?"
    rf"(?:,(?P<start>{_RULE}),(?P<end>{_RULE}))?)?$"
)


def _seconds(value: str) -> int:
    sign = -1 if value.startswith("-") else 1
    parts = [int(p) for p in value.lstrip("+-").split(":")]
    parts += [0] * (3 - len(parts))
    return sign * (parts[0] * 3600 + parts[1] * 60 + parts[2])


def _rule_date(rule: str, year: int) -> date:
    if rule.startswith("J"):  # Julian day 1-365, Feb 29 never counted
        day = int(rule[1:])
        result = date(year, 1, 1) + timedelta(days=day - 1)
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        return result + timedelta(days=1) if leap and day >= 60 else result
    if rule.startswith("M"):  # Mm.w.d: day d (0 = Sunday) of week w (5 = last)
        month, week, weekday = (int(p) for p in rule[1:].split("."))
        first = date(year, month, 1)
        day = first + timedelta(days=(weekday - (first.isoweekday() % 7)) % 7)
        day += timedelta(weeks=week - 1)
        while day.month != month:
            day -= timedelta(weeks=1)
        return day
    return date(year, 1, 1) + timedelta(days=int(rule))  # zero-based, leap counted


def _transition(rule: str, year: int, utcoffset: int) -> datetime:
    """UTC instant of a rule in a year; the rule time is in local time."""
    day, _, at = rule.partition("/")
    local = datetime.combine(_rule_date(day, year), datetime.min.time())
    local += timedelta(seconds=_seconds(at) if at else 7200)
    return (local - timedelta(seconds=utcoffset)).replace(tzinfo=timezone.utc)


def posix_utcoffset(posix: str, when: datetime) -> int | None:
    """UTC offset in seconds that a POSIX TZ string gives at an instant."""
    match = _POSIX_FULL.match(posix or "")
    if not match:
        return None
    std = -_seconds(match["std_off"])  # POSIX offsets are west-positive
    if not match["dst"]:
        return std
    dst = -_seconds(match["dst_off"]) if match["dst_off"] else std + 3600
    start_rule = match["start"] or "M3.2.0"  # POSIX default (US rules)
    end_rule = match["end"] or "M11.1.0"
    when = when.astimezone(timezone.utc)
    for year in (when.year - 1, when.year, when.year + 1):
        start = _transition(start_rule, year, std)
        end = _transition(end_rule, year, dst)
        if end <= start:  # southern hemisphere: DST spans the new year
            end = _transition(end_rule, year + 1, dst)
        if start <= when < end:
            return dst
    return std


def posix_matches_zone(
    posix: str, name: str, start: datetime | None = None, days: int = 400
) -> bool:
    """Return True if the POSIX string agrees with the zone, hourly, for days."""
    try:
        zone = zoneinfo.ZoneInfo(name)
    except (zoneinfo.ZoneInfoNotFoundError, ValueError):
        return False
    when = (start or datetime.now(timezone.utc)).astimezone(timezone.utc)
    when = when.replace(minute=30, second=0, microsecond=0)
    for _ in range(days * 24):
        expected = when.astimezone(zone).utcoffset()
        if expected is None or posix_utcoffset(posix, when) != expected.total_seconds():
            return False
        when += timedelta(hours=1)
    return True


# Transition times POSIX.1 allows (0-24 h). The tz database also uses the
# extension to negative and over-24 h times (America/Nuuk "/-1",
# Asia/Jerusalem "/26"); the heater firmware is not known to handle those, so
# such zones are not synced.
_MAX_RULE_TIME = 24 * 3600


def posix_rule_times_supported(posix: str) -> bool:
    """Return True if the string's transition times are within 0-24 h."""
    match = _POSIX_FULL.match(posix or "")
    if not match:
        return False
    for rule in (match["start"], match["end"]):
        _, _, at = (rule or "").partition("/")
        if at and not 0 <= _seconds(at) <= _MAX_RULE_TIME:
            return False
    return True


def _tzif_candidates(name: str):
    parts = name.split("/")
    for root in zoneinfo.TZPATH:
        yield Path(root, *parts)
    try:
        yield resources.files("tzdata.zoneinfo").joinpath(*parts)
    except ModuleNotFoundError:
        return


def posix_tz_for(name: str | None, now: datetime | None = None) -> str | None:
    """Return the POSIX TZ string for an IANA zone name such as Europe/Kyiv.

    None if there is none, if it does not reproduce the zone's offsets for
    the coming months, or if it uses transition times outside 0-24 h (the zone
    then cannot be synced to the heater).
    """
    if not name or not _IANA_NAME.match(name) or ".." in name:
        return None
    for path in _tzif_candidates(name):
        try:
            content = path.read_bytes()
        except (OSError, ValueError):
            continue
        result = posix_tz_from_tzif(content)
        if result:
            if not posix_rule_times_supported(result):
                return None
            return result if posix_matches_zone(result, name, now) else None
    return None


def device_time(data: dict) -> datetime | None:
    """Return the device local time from the ``date`` field (naive)."""
    value = data.get(DATE_FIELD)
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        return None


def clock_offset(data: dict, local_now: datetime) -> float | None:
    """Seconds the device clock is ahead (+) of Home Assistant's local time."""
    device = device_time(data)
    if device is None:
        return None
    return (device - local_now.replace(tzinfo=None)).total_seconds()


def clock_problems(
    data: dict, expected_tz: str | None, local_now: datetime
) -> list[str]:
    """Return the clock problems found: ``timezone`` and/or ``offset``."""
    problems = []
    current_tz = data.get(TZ_FIELD)
    if expected_tz and current_tz is not None and current_tz != expected_tz:
        problems.append("timezone")
    offset = clock_offset(data, local_now)
    if offset is not None and abs(offset) > MAX_CLOCK_OFFSET:
        problems.append("offset")
    return problems
