"""Tesy binary sensor component."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import TesyCoordinator
from .entity import TesyEntity
from .timezone import TZ_FIELD, clock_offset, clock_problems, device_time


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Tesy binary sensors from config entry."""
    coordinator: TesyCoordinator = hass.data[DOMAIN][entry.entry_id]

    if not coordinator.supports_timezone:
        return

    async_add_entities(
        [
            TesyClockProblemSensor(
                hass,
                coordinator,
                entry,
                BinarySensorEntityDescription(
                    key="clock_problem",
                    translation_key="clock_problem",
                    device_class=BinarySensorDeviceClass.PROBLEM,
                    entity_category=EntityCategory.DIAGNOSTIC,
                    icon="mdi:clock-alert-outline",
                ),
            )
        ]
    )


class TesyClockProblemSensor(TesyEntity, BinarySensorEntity):
    """On when the heater clock or time zone disagrees with Home Assistant.

    The weekly programs run on the heater clock, so a wrong clock makes them
    switch at the wrong hour.
    """

    # Change on every poll; keep them out of history.
    _unrecorded_attributes = frozenset({"device_time", "offset_seconds"})

    def _reference_time(self):
        """HA local time when the heater reported its date (last poll).

        Comparing the snapshot with the current time would make a healthy clock
        look late by the age of the data, up to a whole poll interval.
        """
        received = self.coordinator.data_received_at
        return dt_util.as_local(received) if received else dt_util.now()

    @property
    def is_on(self) -> bool:
        """Return True if there is a clock problem."""
        return bool(
            clock_problems(
                self.coordinator.data,
                self.coordinator.expected_timezone,
                self._reference_time(),
            )
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return clock details."""
        data = self.coordinator.data
        now = self._reference_time()
        device = device_time(data)
        offset = clock_offset(data, now)
        expected = self.coordinator.expected_timezone
        return {
            "problems": clock_problems(data, expected, now),
            "device_time": device.isoformat() if device else None,
            "offset_seconds": None if offset is None else round(offset),
            "timezone": data.get(TZ_FIELD),
            "expected_timezone": expected,
        }
