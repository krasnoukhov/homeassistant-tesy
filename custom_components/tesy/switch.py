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
from .const import DOMAIN, LOGGER
from .coordinator import TesyCoordinator

ENTITY_DESCRIPTIONS = (
    {
        "desc": SwitchEntityDescription(
            key="away",
            name="Away",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        "is_on": lambda entity: entity.is_away_mode_on,
        "async_turn_on": lambda entity: entity.async_turn_away_mode_on,
        "async_turn_off": lambda entity: entity.async_turn_away_mode_off,
    },
    {
        "desc": SwitchEntityDescription(
            key="boost",
            name="Boost",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        "is_on": lambda entity: entity.is_boost_mode_on,
        "async_turn_on": lambda entity: entity.async_turn_boost_mode_on,
        "async_turn_off": lambda entity: entity.async_turn_boost_mode_off,
    },
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Tesy devices from config entry."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[TesySwitch] = []

    for Tesy_id in coordinator.data["devices"]:
        for entity_info in ENTITY_DESCRIPTIONS:
            entities.append(
                TesySwitch(
                    coordinator,
                    Tesy_id,
                    entity_info["desc"],
                    entity_info["is_on"],
                    entity_info["async_turn_on"],
                    entity_info["async_turn_off"],
                )
            )

    async_add_entities(entities)


class TesySwitch(TesyEntity, SwitchEntity):
    """Represents a toggle switch for an Tesy device."""

    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(
        self,
        coordinator: TesyCoordinator,
        Tesy_id,
        entity_description: SwitchEntityDescription,
        is_on_func,
        async_turn_on_func,
        async_turn_off_func,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, Tesy_id)
        self.entity_description = entity_description
        self._attr_name = entity_description.name
        self._is_on_func = is_on_func
        self._async_turn_on_func = async_turn_on_func
        self._async_turn_off_func = async_turn_off_func
        self._attr_unique_id = self._base_unique_id + "_" + entity_description.key
        LOGGER.debug("Created switch with unique ID %s", self._attr_unique_id)

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