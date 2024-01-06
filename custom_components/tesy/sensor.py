"""Tesy sensor component."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import TesyEntity
from .const import (
    DOMAIN,
    ATTR_LONG_COUNTER,
)
from .coordinator import TesyCoordinator
import logging

_LOGGER = logging.getLogger(__name__)


DESCRIPTION = {
    "desc": SensorEntityDescription(
        key="energy_consumed",
        name="Energy Consumed",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:water-thermometer",
    ),
    "native_value": lambda entity: entity.coordinator.data[ATTR_LONG_COUNTER],
    "suggested_precision": None,
    "options": None,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Tesy devices from config entry."""

    coordinator = hass.data[DOMAIN][entry.entry_id]
    #async_add_entities([TesySensor(hass, coordinator, entry, DESCRIPTION)])
    async_add_entities([TesySensor(
        hass, 
        coordinator, 
        entry, 
        DESCRIPTION["desc"],
        DESCRIPTION["native_value"],
        DESCRIPTION["suggested_precision"],
        DESCRIPTION["options"])]
    )

class TesySensor(TesyEntity, SensorEntity):
    """Represents a sensor for an Tesy water heater controller."""

    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: TesyCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
        native_value_func,
        suggested_precision: int | None,
        options: list | None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(hass, coordinator, entry, description)

        self.description: description
        self._attr_name = description.name
        self._native_value_func = native_value_func
        #self._attr_unique_id = self._base_unique_id + "_" + description.key
        #_LOGGER.debug("Created sensor with unique ID %s", self._attr_unique_id)
 
        if description.device_class is not None:
            self._attr_device_class = description.device_class

        if description.state_class is not None:
            self._attr_state_class = description.state_class

        if description.native_unit_of_measurement is not None:
            self._attr_native_unit_of_measurement = (
                description.native_unit_of_measurement
            )

        if description.icon is not None:
            self._attr_icon = description.icon

        if suggested_precision is not None:
            self._attr_suggested_display_precision = suggested_precision

        if options is not None:
            self._attr_options = options

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._native_value_func(self)