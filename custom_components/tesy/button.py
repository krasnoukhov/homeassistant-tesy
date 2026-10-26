"""Tesy button component."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
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
    entities: list[ButtonEntity] = []

    if ATTR_ENERGY_RESETTABLE in coordinator.data:
        entities.append(
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
        )

    if coordinator.supports_timezone:
        entities.append(
            TesySyncTimezoneButton(
                hass,
                coordinator,
                entry,
                ButtonEntityDescription(
                    key="sync_timezone",
                    translation_key="sync_timezone",
                    icon="mdi:clock-check-outline",
                    entity_category=EntityCategory.CONFIG,
                ),
            )
        )

    async_add_entities(entities)


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


class TesySyncTimezoneButton(TesyEntity, ButtonEntity):
    """Write Home Assistant's time zone to the heater.

    The integration also does this on start-up and when the HA time zone
    changes; the button forces it after the clock was changed on the panel or
    in MyTESY.
    """

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            await self.coordinator.async_sync_timezone(force=True)
        except (ConnectionError, ValueError) as err:
            raise HomeAssistantError(f"Failed to sync the time zone: {err}") from err
