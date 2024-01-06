"""Tesy sensor component."""
from __future__ import annotations

import logging
_LOGGER = logging.getLogger(__name__)


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
    TESY_DEVICE_TYPES,
    ATTR_PARAMETERS,
    ATTR_DEVICE_ID,
    DOMAIN,
    ATTR_LONG_COUNTER,
)
from .coordinator import TesyCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Tesy devices from config entry."""

    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TesySensor(
        hass, 
        coordinator, 
        entry, 
        SensorEntityDescription(
            key="energy_consumed",
            name="Energy Consumed",
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            icon="mdi:lightning-bolt",
        ),
        0.01,
        None,
    )])

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
        suggested_precision: int | None,
        options: list | None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(hass, coordinator, entry, description)

        self.description: description
        self._attr_name = description.name
 
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
        #Prevent crashes if energy counter is missing
        if ATTR_LONG_COUNTER not in self.coordinator.data:
            return 0
        
        
        if ";" not in self.coordinator.data[ATTR_LONG_COUNTER]:
            #For fingle tank heaters, we need to have power walue configured
            configured_power=self.coordinator.get_config_power()
            _LOGGER.debug("Configured power: %s",configured_power )
            energy_kwh=(int(self.coordinator.data[ATTR_LONG_COUNTER])*configured_power)/3600.0
            return energy_kwh
        else:
            #Prevent crashes if Additional parameters are missing
            if ATTR_PARAMETERS not in self.coordinator.data:
                return 0
            
            power_dict=self.coordinator.data[ATTR_LONG_COUNTER].split(";")
            pNF=self.coordinator.data[ATTR_PARAMETERS]
            watt1 = int(pNF[38 + 0 * 2:40 + 0 * 2], 16) * 20
            watt2 = int(pNF[38 + 1 * 2:40 + 1 * 2], 16) * 20
            tmp_kwh1=(int(power_dict[0])*watt1)/3600.0
            tmp_kwh2=(int(power_dict[1])*watt2)/3600.0

            return tmp_kwh1+tmp_kwh2
        

    