"""Tesy switch component."""
from __future__ import annotations

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchDeviceClass,
    SwitchEntityDescription,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import TesyEntity
from .const import DOMAIN
from .coordinator import TesyCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Tesy devices from config entry."""

    coordinator = hass.data[DOMAIN][entry.entry_id]
    

    async_add_entities([TesySwitch(
        hass, 
        coordinator, 
        entry, 
        SwitchEntityDescription(
            key="boost",
            name="Boost",
            icon="mdi:rocket-launch-outline",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        lambda entity: entity.is_boost_mode_on,
        lambda entity: entity.async_turn_boost_mode_on,
        lambda entity: entity.async_turn_boost_mode_off,
    )])


class TesySwitch(TesyEntity, SwitchEntity):
    """Represents a toggle switch for an Tesy device."""

    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(
        self,
        hass,
        coordinator: TesyCoordinator,
        entry: ConfigEntry,
        description: SwitchEntityDescription,
        is_on_func,
        async_turn_on_func,
        async_turn_off_func,
    ) -> None:
        """Initialize the switch."""
        super().__init__(hass, coordinator, entry,description)
        self.entity_description = description
        self._attr_name = description.name
        self._is_on_func = is_on_func
        self._async_turn_on_func = async_turn_on_func
        self._async_turn_off_func = async_turn_off_func

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._is_on_func(self)

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        return await self._async_turn_on_func(self)()

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        return await self._async_turn_off_func(self)()