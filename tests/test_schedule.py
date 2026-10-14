"""Tests for weekly program helpers (no Home Assistant needed)."""

from datetime import datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest import TestCase

_PATH = Path(__file__).parents[1] / "custom_components" / "tesy" / "schedule.py"
_SPEC = spec_from_file_location("tesy_schedule", _PATH)
schedule = module_from_spec(_SPEC)
_SPEC.loader.exec_module(schedule)

# Factory programs read from a ModEco 2 (id 2004, hsw 200407, wsw 0.29).
P1 = "0E0E323232321919191928284B4B4B4B3232323232320E0E"
P2 = "14144B4B4B4B323232323232323232323232323232321313"
EMPTY = "FF" * 24


def device_data(mode="0", date="2026-10-13 22:47:31", tmp_r="75"):
    """Build an /api?name=_all payload like the one a ModEco 2 returns."""
    data = {"mode": mode, "date": date, "tmpT": "75", "tmpR": tmp_r}
    for day in schedule.DAYS:
        data[f"prgP1{day}"] = P1
        data[f"prgP2{day}"] = P2
        data[f"prgP3{day}"] = EMPTY
    return data


class ScheduleCodecTest(TestCase):
    """Encode and decode the 24-byte day format."""

    def test_decode_factory_program(self):
        self.assertEqual(
            schedule.decode_day(P1),
            [14, 14, 50, 50, 50, 50, 25, 25, 25, 25, 40, 40]
            + [75, 75, 75, 75, 50, 50, 50, 50, 50, 50, 14, 14],
        )

    def test_empty_hours_are_none(self):
        self.assertEqual(schedule.decode_day(EMPTY), [None] * 24)

    def test_round_trip(self):
        for value in (P1, P2, EMPTY):
            self.assertEqual(schedule.encode_day(schedule.decode_day(value)), value)

    def test_encode_matches_value_accepted_by_device(self):
        hours = [14] * 24
        for hour in (6, 7, 8, 18, 19, 20, 21):
            hours[hour] = 60
        self.assertEqual(
            schedule.encode_day(hours),
            "0E0E0E0E0E0E3C3C3C0E0E0E0E0E0E0E0E0E3C3C3C3C0E0E",
        )

    def test_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            schedule.encode_day([50] * 23)
        with self.assertRaises(ValueError):
            schedule.encode_day([80] + [50] * 23)
        with self.assertRaises(ValueError):
            schedule.decode_day("0E0E")
        with self.assertRaises(ValueError):
            # 48 chars, but fromhex skips the spaces: only 23 bytes
            schedule.decode_day("0E" * 23 + "  ")

    def test_whole_number(self):
        self.assertEqual(schedule.whole_number(2), 2)
        self.assertEqual(schedule.whole_number("2"), 2)
        self.assertEqual(schedule.whole_number(2.0), 2)
        for bad in (2.9, "50.7", "x", True):
            with self.assertRaises(ValueError):
                schedule.whole_number(bad)
        with self.assertRaises(TypeError):
            schedule.whole_number(None)

    def test_schedule_key(self):
        self.assertEqual(schedule.schedule_key(3, "mo"), "prgP3MO")
        with self.assertRaises(ValueError):
            schedule.schedule_key(4, "MO")


class ActiveTargetTest(TestCase):
    """Work out the target the heater is heading for."""

    def test_manual_mode_uses_tmp_r(self):
        self.assertEqual(schedule.active_target(device_data(mode="0")), 75.0)

    def test_eco_mode_uses_tmp_r(self):
        self.assertEqual(
            schedule.active_target(device_data(mode="4", tmp_r="70")), 70.0
        )

    def test_program_ignores_placeholder_and_uses_schedule(self):
        # Tuesday 22:47: P1 has 14 °C at 22:00, P2 has 19 °C; tmpR reports 9.
        self.assertEqual(schedule.active_target(device_data(mode="1", tmp_r="9")), 14.0)
        self.assertEqual(schedule.active_target(device_data(mode="2", tmp_r="9")), 19.0)

    def test_boost_in_program_uses_tmp_r(self):
        # P1 at 23:57 with Boost on: firmware reports the real target (75).
        data = device_data(mode="1", date="2026-10-13 23:57:03", tmp_r="75")
        data["bst"] = "1"
        self.assertEqual(schedule.active_target(data), 75.0)
        data.update({"bst": "0", "tmpR": "9"})
        self.assertEqual(schedule.active_target(data), 14.0)

    def test_program_uses_reported_target(self):
        # Friday 02:05 in P2: the firmware reports the real target in tmpR.
        data = device_data(mode="2", date="2026-10-16 02:05:50", tmp_r="75")
        self.assertEqual(schedule.active_target(data), 75.0)

    def test_program_heating_ahead_uses_reported_target(self):
        # 23:59, the P1 slot is 14 °C, but the heater already works towards a
        # higher target (75 °C) and reports it in tmpR.
        data = device_data(mode="1", date="2026-10-13 23:59:00", tmp_r="75")
        self.assertEqual(schedule.active_target(data), 75.0)

    def test_program_missing_tmp_r_uses_schedule(self):
        data = device_data(mode="2", tmp_r=None)
        self.assertEqual(schedule.active_target(data), 19.0)

    def test_program_hour_lookup(self):
        data = device_data(mode="1", date="2026-10-13 13:05:00", tmp_r="9")
        self.assertEqual(schedule.active_target(data), 75.0)

    def test_empty_program_hour_is_unknown(self):
        self.assertIsNone(schedule.active_target(device_data(mode="3", tmp_r="9")))

    def test_device_without_programs_falls_back_to_tmp_r(self):
        # Old API data has no prg fields; keep the previous behaviour.
        self.assertEqual(schedule.active_target({"mode": "1", "tmpR": "55"}), 55.0)

    def test_powered_off_runs_no_program(self):
        data = device_data(mode="1", tmp_r="9")
        data["pwr"] = "0"
        self.assertIsNone(schedule.active_program(data))
        self.assertEqual(schedule.active_target(data), 9.0)
        data["pwr"] = "1"
        self.assertEqual(schedule.active_program(data), 1)

    def test_unverified_model_keeps_tmp_r(self):
        # Programs reported, but not enabled for the model: basic behaviour.
        data = device_data(mode="1", tmp_r="9")
        self.assertEqual(schedule.active_target(data, use_schedule=False), 9.0)

    def test_unknown_clock_is_unknown(self):
        # Placeholder in tmpR and no device time: the target is unknown.
        data = device_data(mode="1", date="garbage", tmp_r="9")
        self.assertIsNone(schedule.active_target(data))
        # A real tmpR does not need the clock.
        data["tmpR"] = "75"
        self.assertEqual(schedule.active_target(data), 75.0)

    def test_weekday_mapping(self):
        data = device_data(mode="3")
        data["prgP3SU"] = "32" * 24
        sunday = datetime(2026, 10, 18, 12, 0)
        self.assertEqual(schedule.scheduled_target(data, 3, sunday), 50)
        self.assertIsNone(
            schedule.scheduled_target(data, 3, datetime(2026, 10, 19, 12, 0))
        )

    def test_get_program(self):
        program = schedule.get_program(device_data(), 2)
        self.assertEqual(list(program), ["mo", "tu", "we", "th", "fr", "sa", "su"])
        self.assertEqual(program["mo"][2], 75)
        self.assertIsNone(schedule.get_program({}, 1))


class ServiceHelpersTest(TestCase):
    def test_no_days_means_all_days(self):
        self.assertEqual(
            schedule.days_or_all([]), ["mo", "tu", "we", "th", "fr", "sa", "su"]
        )
        self.assertEqual(schedule.days_or_all(["sa", "su"]), ["sa", "su"])

    def test_failure_message_names_written_days(self):
        self.assertEqual(
            schedule.write_failure_message(2, ["MO"], "tu", "timeout"),
            "P2: wrote MO, failed at TU: timeout",
        )
        self.assertEqual(
            schedule.write_failure_message(1, [], "mo", "timeout"),
            "P1: failed at MO: timeout",
        )
