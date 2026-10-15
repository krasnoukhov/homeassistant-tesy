"""Tesy water heater component."""

from typing import Any
from custom_components.tesy.coordinator import TesyCoordinator

from homeassistant.components.water_heater import (
    STATE_ECO,
    STATE_PERFORMANCE,
    WaterHeaterEntity,
    WaterHeaterEntityDescription,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_WHOLE,
    STATE_OFF,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    TESY_DEVICE_TYPES,
    ATTR_CURRENT_TEMP,
    ATTR_CURRENT_TARGET_TEMP,
    ATTR_DEVICE_ID,
    ATTR_IS_HEATING,
    ATTR_MODE,
    ATTR_POWER,
    ATTR_TARGET_TEMP,
    DOMAIN,
    TESY_MODE_P1,
    TESY_MODE_P2,
    TESY_MODE_P3,
    TESY_MODE_EC2,
    TESY_MODE_EC3,
)

from .entity import TesyEntity
from .helpers import TESY_MODE_TO_OPERATION, max_showers, tesy_mode, to_float

OPERATION_LIST = [
    STATE_OFF,
    STATE_PERFORMANCE,
    TESY_MODE_P1,
    TESY_MODE_P2,
    TESY_MODE_P3,
    STATE_ECO,
    TESY_MODE_EC2,
    TESY_MODE_EC3,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create Tesy water heater in HASS."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            TesyWaterHeater(
                hass,
                coordinator,
                entry,
                WaterHeaterEntityDescription(
                    key="water_heater",
                    translation_key="heater",
                ),
            )
        ]
    )


class TesyWaterHeater(TesyEntity, WaterHeaterEntity):
    """Representation of an Tesy water heater."""

    _attr_operation_list = OPERATION_LIST
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_precision = PRECISION_WHOLE
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
        | WaterHeaterEntityFeature.ON_OFF
    )

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: TesyCoordinator,
        entry: ConfigEntry,
        description: Any,
    ) -> None:
        super().__init__(hass, coordinator, entry, description)

        # Default values
        self._attr_min_temp = 15
        self._attr_max_temp = 75

        if self.coordinator.data[ATTR_DEVICE_ID] in TESY_DEVICE_TYPES:
            self._attr_min_temp = TESY_DEVICE_TYPES[
                self.coordinator.data[ATTR_DEVICE_ID]
            ]["min_setpoint"]
            self._attr_max_temp = TESY_DEVICE_TYPES[
                self.coordinator.data[ATTR_DEVICE_ID]
            ]["max_setpoint"]

            # if heater only supports showers, get its maximum depending on model, position
            if (
                "use_showers"
                in TESY_DEVICE_TYPES[self.coordinator.data[ATTR_DEVICE_ID]]
                and TESY_DEVICE_TYPES[self.coordinator.data[ATTR_DEVICE_ID]][
                    "use_showers"
                ]
                == True
            ):
                self._attr_max_temp = max_showers(
                    self.coordinator.data, self._attr_max_temp
                )

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return to_float(self.coordinator.data.get(ATTR_CURRENT_TEMP))

    @property
    def current_operation(self):
        """Return current operation."""

        if (
            ATTR_POWER not in self.coordinator.data
            or ATTR_MODE not in self.coordinator.data
        ):
            return STATE_OFF

        # if powered off
        if self.coordinator.data[ATTR_POWER] != "1":
            return STATE_OFF

        # Unknown modes are reported as off
        return TESY_MODE_TO_OPERATION.get(self.coordinator.data[ATTR_MODE], STATE_OFF)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        # Just in case if power is missing from json, prevent crashes
        if ATTR_POWER not in self.coordinator.data:
            return

        if self.coordinator.data[ATTR_POWER] == "1":
            if self.coordinator.data[ATTR_MODE] != "0":
                response = await self.coordinator.async_set_operation_mode("0")
                await self.partially_update_data_from_api(response, ATTR_MODE)

        response = await self.coordinator.async_set_target_temperature(
            kwargs.get(ATTR_TEMPERATURE)
        )
        await self.partially_update_data_from_api(
            response, ATTR_TARGET_TEMP, ATTR_CURRENT_TARGET_TEMP
        )
        # Optimistic: in manual mode, tmpR always equals tmpT
        new_temp = kwargs.get(ATTR_TEMPERATURE)
        if new_temp is not None:
            self.coordinator.data[ATTR_CURRENT_TARGET_TEMP] = new_temp
            self.coordinator.async_set_updated_data(self.coordinator.data)

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new target operation mode."""

        # Just in case if power is missing from json, prevent crashes
        if ATTR_POWER not in self.coordinator.data:
            return

        if operation_mode == STATE_OFF:
            response = await self.coordinator.async_set_power("0")
            await self.partially_update_data_from_api(response, ATTR_POWER)
        else:
            # Raises ValueError for an unknown mode, before anything is sent
            new_mode = tesy_mode(operation_mode)

            if self.coordinator.data[ATTR_POWER] == "0":
                response = await self.coordinator.async_set_power("1")
                await self.partially_update_data_from_api(response, ATTR_POWER)

            response = await self.coordinator.async_set_operation_mode(new_mode)
            await self.partially_update_data_from_api(
                response,
                ATTR_MODE,
                ATTR_TARGET_TEMP,
                ATTR_CURRENT_TARGET_TEMP,
                ATTR_POWER,
            )

            if (
                operation_mode in (STATE_ECO, TESY_MODE_EC2, TESY_MODE_EC3)
                and not self.coordinator.is_old_api
            ):
                response = await self.coordinator.async_set_target_temperature(
                    self._attr_max_temp
                )
                await self.partially_update_data_from_api(
                    response, ATTR_CURRENT_TARGET_TEMP
                )

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """Turn on water heater."""
        response = await self.coordinator.async_set_power("1")
        await self.partially_update_data_from_api(response, ATTR_POWER)

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn off water heater."""
        response = await self.coordinator.async_set_power("0")
        await self.partially_update_data_from_api(response, ATTR_POWER)

    @property
    def target_temperature(self):
        """Return the target temperature."""
        return to_float(self.coordinator.data.get(ATTR_CURRENT_TARGET_TEMP))

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the state attributes."""
        return {
            "is_heating": ATTR_IS_HEATING in self.coordinator.data
            and self.coordinator.data[ATTR_IS_HEATING] == "1",
            "target_temp_step": 1,
        }
