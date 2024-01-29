"""Base entity for the Tesy integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_MAC,
    ATTR_SOFTWARE,
    DOMAIN,
)
from .coordinator import TesyCoordinator


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
        return DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    self.coordinator.data[ATTR_MAC],
                )
            },
            manufacturer="Tesy",
            sw_version=self.coordinator.data[ATTR_SOFTWARE],
        )
