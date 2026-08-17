"""Tesy button component."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import TesyEntity
from .const import ATTR_API, ATTR_ENERGY_RESETTABLE, DOMAIN
from .coordinator import TesyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Tesy buttons from config entry."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    if ATTR_ENERGY_RESETTABLE not in coordinator.data:
        return

    async_add_entities(
        [
            TesyResetButton(
                hass,
                coordinator,
                entry,
                ButtonEntityDescription(
                    key="energy_reset",
                    translation_key="energy_reset",
                    icon="mdi:restart",
                ),
            )
        ]
    )


class TesyResetButton(TesyEntity, ButtonEntity):
    """Represents a reset button for the resettable energy counter."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: TesyCoordinator,
        entry: ConfigEntry,
        description: ButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(hass, coordinator, entry, description)

    async def async_press(self) -> None:
        """Handle the button press."""
        response = await self.coordinator.async_reset_energy_counter()
        if response.get(ATTR_API) != "OK":
            raise HomeAssistantError("Failed to reset the energy counter")
