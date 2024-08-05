"""Base entity for the Tesy integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    TESY_DEVICE_TYPES,
    ATTR_DEVICE_ID,
    ATTR_MAC,
    ATTR_BOOST,
    ATTR_SOFTWARE,
    DOMAIN,
    ATTR_API,
)
from .coordinator import TesyCoordinator

import logging

_LOGGER = logging.getLogger(__name__)


class TesyEntity(CoordinatorEntity[TesyCoordinator]):
    """Defines a base Tesy entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: TesyCoordinator,
        entry: ConfigEntry,
        description: EntityDescription,
    ) -> None:
        """Initialize a Tesy entity."""
        super().__init__(coordinator)

        self.entity_description = description
        self.hass = hass
        self._entry = entry

        self._attr_unique_id = "-".join(
            [
                coordinator.data[ATTR_MAC],
                description.key,
            ]
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Tesy device."""
        device_model = "Generic"
        if self.coordinator.data[ATTR_DEVICE_ID] in TESY_DEVICE_TYPES:
            device_model = TESY_DEVICE_TYPES[self.coordinator.data[ATTR_DEVICE_ID]][
                "name"
            ]

        return DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    self.coordinator.data[ATTR_MAC],
                )
            },
            manufacturer="Tesy",
            model=device_model,
            sw_version=self.coordinator.data[ATTR_SOFTWARE],
        )

    @property
    def is_boost_mode_on(self):
        """Return true if boost mode is on."""
        if (
            ATTR_BOOST in self.coordinator.data
            and self.coordinator.data[ATTR_BOOST] == "1"
        ):
            return True
        return False

    async def async_turn_boost_mode_on(self, **kwargs):
        """Turn on boost mode."""

        if self.coordinator.data[ATTR_BOOST] == "0":
            response = await self.coordinator.async_set_boost("1")
            await self.partially_update_data_from_api(response, ATTR_BOOST)

    async def async_turn_boost_mode_off(self, **kwargs):
        """Turn off boost mode."""

        if self.coordinator.data[ATTR_BOOST] == "1":
            response = await self.coordinator.async_set_boost("0")
            await self.partially_update_data_from_api(response, ATTR_BOOST)

    async def partially_update_data_from_api(self, response, key):
        old_data = self.coordinator.data
        if ATTR_API in response and response[ATTR_API] == "OK" and key in response:
            old_data[key] = response[key]
            self.coordinator.async_set_updated_data(old_data)
            _LOGGER.debug("Partial update: setting %s to %s", key, response[key])
