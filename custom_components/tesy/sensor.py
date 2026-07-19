"""Tesy sensor component."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfEnergy,
    UnitOfTemperature,
    UnitOfTime,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import TesyEntity
from .const import (
    ATTR_PARAMETERS,
    ATTR_CDT,
    ATTR_CURRENT_TARGET_TEMP,
    ATTR_ENERGY_RESETTABLE,
    ATTR_ERROR,
    ATTR_RSSI,
    ATTR_UPTIME,
    DOMAIN,
    ATTR_LONG_COUNTER,
    ATTR_CURRENT_TEMP,
)
from .coordinator import TesyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Tesy devices from config entry."""

    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            TesyTemperatureSensor(
                hass,
                coordinator,
                entry,
                SensorEntityDescription(
                    key="temperature",
                    name="Temperature",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                    icon="mdi:thermometer",
                ),
                1,
                None,
            ),
            TesyEnergySensor(
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
                2,
                None,
            ),
            TesyCdtSensor(
                hass,
                coordinator,
                entry,
                SensorEntityDescription(
                    key="cdt",
                    name="Ready In",
                    device_class=SensorDeviceClass.DURATION,
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement=UnitOfTime.MINUTES,
                    icon="mdi:clock",
                ),
                None,
                None,
            ),
            TesyTargetTempSensor(
                hass,
                coordinator,
                entry,
                SensorEntityDescription(
                    key="current_target_temperature",
                    name="Target Temperature",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                    icon="mdi:thermometer",
                ),
                1,
                None,
            ),
            TesyErrorSensor(
                hass,
                coordinator,
                entry,
                SensorEntityDescription(
                    key="error_status",
                    name="Error Status",
                    icon="mdi:alert-circle-outline",
                ),
                None,
                None,
            ),
            TesyRssiSensor(
                hass,
                coordinator,
                entry,
                SensorEntityDescription(
                    key="wifi_signal",
                    name="WiFi Signal",
                    device_class=SensorDeviceClass.SIGNAL_STRENGTH,
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
                    icon="mdi:wifi",
                ),
                0,
                None,
            ),
            TesyUptimeSensor(
                hass,
                coordinator,
                entry,
                SensorEntityDescription(
                    key="uptime",
                    name="Uptime",
                    device_class=SensorDeviceClass.DURATION,
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement=UnitOfTime.SECONDS,
                    icon="mdi:clock-outline",
                ),
                None,
                None,
            ),
            TesyResettableEnergySensor(
                hass,
                coordinator,
                entry,
                SensorEntityDescription(
                    key="energy_consumed_resettable",
                    name="Energy Consumed (Resettable)",
                    device_class=SensorDeviceClass.ENERGY,
                    state_class=SensorStateClass.TOTAL_INCREASING,
                    native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
                    icon="mdi:lightning-bolt",
                ),
                2,
                None,
            ),
        ]
    )


class TesySensor(TesyEntity, SensorEntity):
    """Represents a sensor for a Tesy water heater controller."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: TesyCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
        suggested_display_precision: int | None,
        options: list | None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(hass, coordinator, entry, description)

        self.entity_description = description
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

        if suggested_display_precision is not None:
            self._attr_suggested_display_precision = suggested_display_precision

        if options is not None:
            self._attr_options = options


class TesyEnergySensor(TesySensor):
    @property
    def native_value(self):
        """Return the state of the sensor."""
        # Prevent crashes if energy counter is missing
        if ATTR_LONG_COUNTER not in self.coordinator.data:
            return None

        if ";" not in self.coordinator.data[ATTR_LONG_COUNTER]:
            # For single tank heaters, we need to have power value configured
            configured_power = self.coordinator.get_config_power()
            energy_kwh = (
                int(self.coordinator.data[ATTR_LONG_COUNTER]) * configured_power
            ) / (3600.0 * 1000)
            return energy_kwh
        else:
            # Prevent crashes if Additional parameters are missing
            if ATTR_PARAMETERS not in self.coordinator.data:
                return None

            power_dict = self.coordinator.data[ATTR_LONG_COUNTER].split(";")
            pNF = self.coordinator.data[ATTR_PARAMETERS]
            watt1 = int(pNF[38 + 0 * 2 : 40 + 0 * 2], 16) * 20
            watt2 = int(pNF[38 + 1 * 2 : 40 + 1 * 2], 16) * 20
            tmp_kwh1 = (int(power_dict[0]) * watt1) / (3600.0 * 1000)
            tmp_kwh2 = (int(power_dict[1]) * watt2) / (3600.0 * 1000)

            return tmp_kwh1 + tmp_kwh2


class TesyTemperatureSensor(TesySensor):
    @property
    def native_value(self):
        """Return the state of the sensor."""
        if ATTR_CURRENT_TEMP not in self.coordinator.data:
            return None
        return float(self.coordinator.data[ATTR_CURRENT_TEMP])


class TesyCdtSensor(TesySensor):
    @property
    def native_value(self):
        """Return the countdown in minutes until the heater will be ready."""
        if ATTR_CDT not in self.coordinator.data:
            return None
        return int(self.coordinator.data[ATTR_CDT])


class TesyTargetTempSensor(TesySensor):
    @property
    def native_value(self):
        """Return the current target temperature."""
        if ATTR_CURRENT_TARGET_TEMP not in self.coordinator.data:
            return None
        return float(self.coordinator.data[ATTR_CURRENT_TARGET_TEMP])


class TesyErrorSensor(TesySensor):
    @property
    def native_value(self):
        """Return the error status code."""
        if ATTR_ERROR not in self.coordinator.data:
            return None
        return self.coordinator.data[ATTR_ERROR]


class TesyRssiSensor(TesySensor):
    @property
    def native_value(self):
        """Return the WiFi signal strength."""
        if ATTR_RSSI not in self.coordinator.data:
            return None
        return int(self.coordinator.data[ATTR_RSSI])


class TesyUptimeSensor(TesySensor):
    @property
    def native_value(self):
        """Return the device uptime in seconds."""
        if ATTR_UPTIME not in self.coordinator.data:
            return None
        return int(self.coordinator.data[ATTR_UPTIME])


class TesyResettableEnergySensor(TesySensor):
    @property
    def native_value(self):
        """Return the energy consumed since last reset."""
        if ATTR_ENERGY_RESETTABLE not in self.coordinator.data:
            return None

        pwc_u = self.coordinator.data[ATTR_ENERGY_RESETTABLE]
        if not isinstance(pwc_u, dict) or "utc" not in pwc_u:
            return None

        utc = pwc_u["utc"]
        if ";" not in utc:
            configured_power = self.coordinator.get_config_power()
            energy_kwh = (int(utc) * configured_power) / (3600.0 * 1000)
            return energy_kwh
        else:
            if ATTR_PARAMETERS not in self.coordinator.data:
                return None

            power_dict = utc.split(";")
            pNF = self.coordinator.data[ATTR_PARAMETERS]
            watt1 = int(pNF[38 + 0 * 2 : 40 + 0 * 2], 16) * 20
            watt2 = int(pNF[38 + 1 * 2 : 40 + 1 * 2], 16) * 20
            tmp_kwh1 = (int(power_dict[0]) * watt1) / (3600.0 * 1000)
            tmp_kwh2 = (int(power_dict[1]) * watt2) / (3600.0 * 1000)

            return tmp_kwh1 + tmp_kwh2
