"""Tesy sensor component."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


from homeassistant.components.sensor import (
    RestoreSensor,
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
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import TesyEntity
from .const import (
    ATTR_IS_HEATING,
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
                    translation_key="temperature",
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
                    translation_key="energy_consumed",
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
                    translation_key="ready_in",
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
                    key="target_temperature",
                    translation_key="target_temperature",
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
                    translation_key="error_status",
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
                    translation_key="wifi_signal",
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
                    translation_key="uptime",
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
                    translation_key="energy_consumed_resettable",
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


class TesyEnergySensor(TesySensor, RestoreSensor):
    """Energy sensor that accumulates kWh in real-time from the is-heating flag.

    The boiler's pwc_t counter (cumulative seconds heated) is only updated every
    few hours by the firmware. Using it directly causes energy to be attributed to
    the wrong hourly bucket in HA's energy dashboard. Instead, this sensor tracks
    energy by observing the ht (is-heating) flag on every 30-second poll and
    accumulating power × elapsed_time, giving accurate per-hour attribution.

    For double-tank devices the per-tank ht mapping is unknown, so the original
    pwc_t counter is kept for those.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: TesyCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
        suggested_display_precision: int | None,
        options: list | None,
    ) -> None:
        super().__init__(
            hass, coordinator, entry, description, suggested_display_precision, options
        )
        self._energy_kwh: float = 0.0
        self._last_update: datetime | None = None

    async def async_added_to_hass(self) -> None:
        """Restore previous energy total on startup."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_sensor_data()) is not None:
            try:
                self._energy_kwh = float(last_state.native_value or 0)
            except (TypeError, ValueError):
                pass
        self._last_update = datetime.now(timezone.utc)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Accumulate energy based on heating state, then write HA state."""
        now = datetime.now(timezone.utc)
        data = self.coordinator.data

        is_double_tank = ";" in data.get(ATTR_LONG_COUNTER, "")

        if not is_double_tank and self._last_update is not None:
            elapsed = (now - self._last_update).total_seconds()
            if data.get(ATTR_IS_HEATING) == "1":
                power_w = self.coordinator.get_config_power()
                self._energy_kwh += (power_w * elapsed) / 3_600_000.0

        self._last_update = now
        super()._handle_coordinator_update()

    @property
    def native_value(self):
        """Return the state of the sensor."""
        data = self.coordinator.data

        # Double-tank: fall back to pwc_t counter (per-tank ht mapping unknown)
        if ";" in data.get(ATTR_LONG_COUNTER, ""):
            if ATTR_PARAMETERS not in data:
                return None
            power_dict = data[ATTR_LONG_COUNTER].split(";")
            pNF = data[ATTR_PARAMETERS]
            watt1 = int(pNF[38 + 0 * 2 : 40 + 0 * 2], 16) * 20
            watt2 = int(pNF[38 + 1 * 2 : 40 + 1 * 2], 16) * 20
            tmp_kwh1 = (int(power_dict[0]) * watt1) / (3600.0 * 1000)
            tmp_kwh2 = (int(power_dict[1]) * watt2) / (3600.0 * 1000)
            return tmp_kwh1 + tmp_kwh2

        # Single-tank: return real-time accumulated value
        return round(self._energy_kwh, 6)


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
        cdt = self.coordinator.data[ATTR_CDT]
        if self._last_cdt is not None and self._last_cdt == cdt:
            return self._attr_native_value
        self._last_cdt = cdt
        self._attr_native_value = dt_util.utcnow() + timedelta(minutes=int(cdt))
        return self._attr_native_value


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
