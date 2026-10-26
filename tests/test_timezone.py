"""Tests for device clock / time zone helpers (no Home Assistant needed)."""

from datetime import datetime, timedelta, timezone as dt_timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest import TestCase

_PATH = Path(__file__).parents[1] / "custom_components" / "tesy" / "timezone.py"
_SPEC = spec_from_file_location("tesy_timezone", _PATH)
tz = module_from_spec(_SPEC)
_SPEC.loader.exec_module(tz)

# Value reported by a ModEco 2 (id 2004) set up for Kyiv / Sofia.
KYIV = "EET-2EEST,M3.5.0/3,M10.5.0/4"
LOCAL_NOW = datetime(2026, 10, 13, 23, 48, 50, tzinfo=dt_timezone(timedelta(hours=3)))


def data(date="2026-10-13 23:48:48", zone=KYIV):
    return {"date": date, "tz": zone}


class PosixTzTest(TestCase):
    """Derive the POSIX string from the tz database."""

    def test_kyiv_matches_device(self):
        self.assertEqual(tz.posix_tz_for("Europe/Kyiv"), KYIV)
        self.assertEqual(tz.posix_tz_for("Europe/Sofia"), KYIV)

    def test_other_zones(self):
        self.assertEqual(tz.posix_tz_for("UTC"), "UTC0")
        self.assertEqual(tz.posix_tz_for("Europe/Berlin"), "CET-1CEST,M3.5.0,M10.5.0/3")

    def test_rejects_bad_names(self):
        for name in (None, "", "../etc/passwd", "Europe/../../etc", "Nowhere/City"):
            self.assertIsNone(tz.posix_tz_for(name))

    def test_footer_parsing(self):
        self.assertEqual(
            tz.posix_tz_from_tzif(b"TZif2...\n" + KYIV.encode() + b"\n"), KYIV
        )
        self.assertIsNone(
            tz.posix_tz_from_tzif(b"TZif\0...\nUTC0\n")
        )  # v1 has no footer
        self.assertIsNone(tz.posix_tz_from_tzif(b"nope"))
        self.assertIsNone(tz.posix_tz_from_tzif(b"TZif2...\nbad value\n"))


class ClockProblemTest(TestCase):
    """Detect a wrong time zone or a drifting clock."""

    def test_in_sync(self):
        self.assertEqual(tz.clock_problems(data(), KYIV, LOCAL_NOW), [])
        self.assertEqual(tz.clock_offset(data(), LOCAL_NOW), -2.0)

    def test_wrong_timezone(self):
        # Module left on Berlin time: local clock one hour behind Kyiv.
        stale = data(date="2026-10-13 22:48:48", zone="CET-1CEST,M3.5.0,M10.5.0/3")
        self.assertEqual(
            tz.clock_problems(stale, KYIV, LOCAL_NOW), ["timezone", "offset"]
        )

    def test_drift_without_internet(self):
        drifted = data(date="2026-10-13 23:40:00")
        self.assertEqual(tz.clock_problems(drifted, KYIV, LOCAL_NOW), ["offset"])

    def test_unknown_values_are_not_problems(self):
        self.assertEqual(tz.clock_problems({}, KYIV, LOCAL_NOW), [])
        self.assertEqual(tz.clock_problems(data(), None, LOCAL_NOW), [])
        self.assertIsNone(tz.clock_offset({"date": "garbage"}, LOCAL_NOW))


class PosixEvaluationTest(TestCase):
    """The POSIX string is checked against the tz database before a sync."""

    def test_offsets_around_transitions(self):
        utc = dt_timezone.utc
        # Kyiv: EEST until 2026-10-25 01:00 UTC (04:00 local), then EET.
        self.assertEqual(
            tz.posix_utcoffset(KYIV, datetime(2026, 10, 25, 0, 59, tzinfo=utc)), 10800
        )
        self.assertEqual(
            tz.posix_utcoffset(KYIV, datetime(2026, 10, 25, 1, 0, tzinfo=utc)), 7200
        )
        # Back to EEST on 2027-03-28 01:00 UTC (03:00 local).
        self.assertEqual(
            tz.posix_utcoffset(KYIV, datetime(2027, 3, 28, 0, 59, tzinfo=utc)), 7200
        )
        self.assertEqual(
            tz.posix_utcoffset(KYIV, datetime(2027, 3, 28, 1, 0, tzinfo=utc)), 10800
        )
        sydney = "AEST-10AEDT,M10.1.0,M4.1.0/3"  # DST spans the new year
        self.assertEqual(
            tz.posix_utcoffset(sydney, datetime(2027, 1, 15, tzinfo=utc)), 39600
        )
        self.assertEqual(
            tz.posix_utcoffset(sydney, datetime(2027, 6, 15, tzinfo=utc)), 36000
        )
        self.assertEqual(
            tz.posix_utcoffset("IST-5:30", datetime(2027, 6, 15, tzinfo=utc)), 19800
        )
        self.assertIsNone(
            tz.posix_utcoffset("garbage!", datetime(2027, 6, 15, tzinfo=utc))
        )

    def test_string_must_match_the_zone(self):
        start = datetime(2026, 10, 14, 10, 0, tzinfo=dt_timezone.utc)
        self.assertTrue(tz.posix_matches_zone(KYIV, "Europe/Kyiv", start))
        # A fixed offset for a zone with DST changes is rejected...
        self.assertFalse(tz.posix_matches_zone("EET-2", "Europe/Kyiv", start))
        # ...as are rules that disagree with the zone (US dates for Europe).
        self.assertFalse(
            tz.posix_matches_zone("EET-2EEST,M3.2.0,M11.1.0", "Europe/Kyiv", start)
        )
        self.assertFalse(tz.posix_matches_zone(KYIV, "No/Such_Zone", start))

    def test_unusual_transition_times_are_not_synced(self):
        start = datetime(2026, 10, 14, 10, 0, tzinfo=dt_timezone.utc)
        # Negative (Nuuk "/-1") and over-24 h (Jerusalem "/26") switch times.
        self.assertIsNone(tz.posix_tz_for("America/Nuuk", start))
        self.assertIsNone(tz.posix_tz_for("Asia/Jerusalem", start))
        self.assertFalse(tz.posix_rule_times_supported("IST-2IDT,M3.4.4/26,M10.5.0"))
        # 24:00 is within POSIX (America/Santiago).
        self.assertTrue(
            tz.posix_rule_times_supported("<-04>4<-03>,M9.1.6/24,M4.1.6/24")
        )
        self.assertTrue(tz.posix_rule_times_supported(KYIV))

    def test_whole_tz_database_resolves(self):
        start = datetime(2026, 10, 14, 10, 0, tzinfo=dt_timezone.utc)
        for name in (
            "Europe/Kyiv",
            "America/New_York",
            "Australia/Sydney",
            "America/Santiago",
        ):
            with self.subTest(name=name):
                self.assertIsNotNone(tz.posix_tz_for(name, start))
