"""Tests for TesyEnergySensor energy accumulation logic."""

from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.tesy.sensor import TesyEnergySensor
from custom_components.tesy.const import ATTR_IS_HEATING, ATTR_LONG_COUNTER

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_sensor(api_data: dict, power: int = 2000) -> TesyEnergySensor:
    """Create a TesyEnergySensor with a mocked coordinator."""
    coordinator = MagicMock()
    coordinator.data = {
        "MAC": "AA:BB:CC:DD:EE:FF",
        "wsw": "1.0",
        "id": "2000",
        **api_data,
    }
    coordinator.get_config_power.return_value = power

    description = MagicMock()
    description.key = "energy_consumed"
    description.device_class = None
    description.state_class = None
    description.native_unit_of_measurement = None
    description.icon = None

    return TesyEnergySensor(
        hass=MagicMock(),
        coordinator=coordinator,
        entry=MagicMock(),
        description=description,
        suggested_display_precision=2,
        options=None,
    )


@contextmanager
def at_time(dt: datetime):
    """Patch datetime.now() inside sensor.py to return a fixed time."""
    with patch("custom_components.tesy.sensor.datetime") as mock_dt:
        mock_dt.now.return_value = dt
        yield mock_dt


def poll(sensor: TesyEnergySensor, now: datetime, api_data: dict | None = None):
    """Simulate one coordinator poll at the given time."""
    if api_data is not None:
        sensor.coordinator.data = {
            "MAC": "AA:BB:CC:DD:EE:FF",
            "wsw": "1.0",
            "id": "2000",
            **api_data,
        }
    with at_time(now):
        sensor._handle_coordinator_update()


T0 = datetime(2026, 4, 15, 9, 0, 0, tzinfo=timezone.utc)
T30 = datetime(2026, 4, 15, 9, 0, 30, tzinfo=timezone.utc)
T60 = datetime(2026, 4, 15, 9, 1, 0, tzinfo=timezone.utc)
T90 = datetime(2026, 4, 15, 9, 1, 30, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Accumulation logic
# ---------------------------------------------------------------------------


class TestEnergyAccumulation:
    def test_accumulates_energy_when_heating(self):
        """30 seconds at 3600 W should add exactly 0.03 kWh."""
        sensor = make_sensor({"ht": "1"}, power=3600)
        sensor._last_update = T0

        poll(sensor, T30)

        expected = (3600 * 30) / 3_600_000  # 0.03 kWh
        assert abs(sensor._energy_kwh - expected) < 1e-9

    def test_no_accumulation_when_not_heating(self):
        """Energy must not increase when ht == '0'."""
        sensor = make_sensor({"ht": "0"}, power=3600)
        sensor._last_update = T0

        poll(sensor, T30)

        assert sensor._energy_kwh == 0.0

    def test_multiple_polls_accumulate(self):
        """Three consecutive heating polls should sum correctly."""
        sensor = make_sensor({"ht": "1"}, power=3600)
        sensor._last_update = T0

        poll(sensor, T30)
        poll(sensor, T60)
        poll(sensor, T90)

        expected = (3600 * 90) / 3_600_000  # 3 × 30 s = 90 s → 0.09 kWh
        assert abs(sensor._energy_kwh - expected) < 1e-9

    def test_heating_stops_mid_session(self):
        """Energy only accumulates during heating intervals."""
        sensor = make_sensor({"ht": "1"}, power=3600)
        sensor._last_update = T0

        poll(sensor, T30)  # heating: +0.03 kWh
        poll(sensor, T60, api_data={"ht": "0"})  # not heating: +0
        poll(sensor, T90, api_data={"ht": "0"})  # not heating: +0

        expected = (3600 * 30) / 3_600_000  # only first interval
        assert abs(sensor._energy_kwh - expected) < 1e-9

    def test_energy_attributed_to_poll_timestamp(self):
        """
        Core regression test: energy detected at 10:00:30 (after the hour boundary)
        should NOT retroactively appear in the 9:xx bucket.  With the new approach
        each poll stamps its own delta, so energy appears at exactly the time HA
        records the state change.
        """
        sensor = make_sensor({"ht": "1"}, power=3600)

        before_hour = datetime(2026, 4, 15, 9, 59, 30, tzinfo=timezone.utc)
        on_hour = datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc)
        after_hour = datetime(2026, 4, 15, 10, 0, 30, tzinfo=timezone.utc)

        sensor._last_update = before_hour

        # Poll exactly at the hour boundary — 30 s of heating goes here
        poll(sensor, on_hour)
        kwh_at_boundary = sensor._energy_kwh
        assert abs(kwh_at_boundary - (3600 * 30) / 3_600_000) < 1e-9

        # Poll 30 s after the boundary — another 30 s
        poll(sensor, after_hour)
        assert abs(sensor._energy_kwh - (3600 * 60) / 3_600_000) < 1e-9

    def test_first_poll_after_startup_skips_accumulation(self):
        """If _last_update is None (before async_added_to_hass), no energy is added."""
        sensor = make_sensor({"ht": "1"}, power=3600)
        assert sensor._last_update is None

        poll(sensor, T30)

        assert sensor._energy_kwh == 0.0


# ---------------------------------------------------------------------------
# Double-tank fallback
# ---------------------------------------------------------------------------


class TestDoubleTank:
    def test_uses_pwc_t_for_double_tank(self):
        """Double-tank devices must still use the original pwc_t calculation."""
        # parNF bytes 38-41: two heater powers encoded as hex * 20
        # watt1 = 0x78 * 20 = 120 * 20 = 2400 W
        # watt2 = 0x3C * 20 =  60 * 20 = 1200 W
        pnf = "00" * 19 + "783C" + "00" * 10  # 38 zero-bytes then 78 3C

        sensor = make_sensor(
            {"ht": "1", "pwc_t": "3600;1800", "parNF": pnf},
            power=0,
        )
        sensor._last_update = T0
        poll(sensor, T30)

        # pwc_t-based: (3600 * 2400 + 1800 * 1200) / 3_600_000
        expected = (3600 * 2400 + 1800 * 1200) / 3_600_000
        assert abs(sensor.native_value - expected) < 1e-6

    def test_double_tank_does_not_accumulate_via_ht(self):
        """Double-tank energy must not be double-counted via the ht path."""
        pnf = "00" * 19 + "783C" + "00" * 10

        sensor = make_sensor(
            {"ht": "1", "pwc_t": "3600;1800", "parNF": pnf},
            power=0,
        )
        sensor._last_update = T0
        poll(sensor, T30)

        # _energy_kwh accumulator must stay at 0 for double-tank
        assert sensor._energy_kwh == 0.0


# ---------------------------------------------------------------------------
# State restoration
# ---------------------------------------------------------------------------


class TestStateRestoration:
    async def test_restores_previous_value_on_startup(self):
        """On HA restart the sensor must pick up where it left off."""
        sensor = make_sensor({"ht": "0"}, power=2000)

        last_state = MagicMock()
        last_state.native_value = "1.23456"
        sensor.async_get_last_sensor_data = AsyncMock(return_value=last_state)

        with at_time(T0):
            await sensor.async_added_to_hass()

        assert abs(sensor._energy_kwh - 1.23456) < 1e-9
        assert sensor._last_update == T0

    async def test_starts_at_zero_on_first_run(self):
        """If no previous state exists, energy starts at 0."""
        sensor = make_sensor({"ht": "0"}, power=2000)
        sensor.async_get_last_sensor_data = AsyncMock(return_value=None)

        with at_time(T0):
            await sensor.async_added_to_hass()

        assert sensor._energy_kwh == 0.0

    async def test_handles_corrupt_restored_value(self):
        """A non-numeric restored value must not crash the sensor."""
        sensor = make_sensor({"ht": "0"}, power=2000)

        last_state = MagicMock()
        last_state.native_value = "not-a-number"
        sensor.async_get_last_sensor_data = AsyncMock(return_value=last_state)

        with at_time(T0):
            await sensor.async_added_to_hass()  # should not raise

        assert sensor._energy_kwh == 0.0
