"""Tesy water heater component."""

from typing import Any
from custom_components.tesy.coordinator import TesyCoordinator

from homeassistant.components.water_heater import (
    STATE_ECO,
    STATE_PERFORMANCE,
    WaterHeaterEntity,
    WaterHeaterEntityEntityDescription,
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
    ATTR_DEVICE_ID,
    ATTR_MAX_SHOWERS,
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

import logging

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

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
                WaterHeaterEntityEntityDescription(
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
                tmp_max = self.coordinator.data[ATTR_MAX_SHOWERS]
                self._attr_max_temp = (
                    int(tmp_max) if tmp_max.isdecimal() else self._attr_max_temp
                )

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return float(self.coordinator.data[ATTR_CURRENT_TEMP])

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

        mode = self.coordinator.data[ATTR_MODE]

        if mode == "0":
            return STATE_PERFORMANCE
        if mode == "1":
            return TESY_MODE_P1
        if mode == "2":
            return TESY_MODE_P2
        if mode == "3":
            return TESY_MODE_P3
        if mode == "4":
            return STATE_ECO
        if mode == "5":
            return TESY_MODE_EC2
        if mode == "6":
            return TESY_MODE_EC3

        # Handle unknown state
        return STATE_OFF

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        # Just in case if power is missing from json, prevent crashes
        if ATTR_POWER not in self.coordinator.data:
            return

        if self.coordinator.data[ATTR_POWER] == "1":
            if self.coordinator.data[ATTR_MODE] != STATE_PERFORMANCE:
                response = await self.coordinator.async_set_operation_mode("0")
                await self.partially_update_data_from_api(response, ATTR_MODE)

        response = await self.coordinator.async_set_target_temperature(
            kwargs.get(ATTR_TEMPERATURE)
        )
        await self.partially_update_data_from_api(response, ATTR_TARGET_TEMP)
        # await self.coordinator.async_request_refresh()

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new target operation mode."""

        # Just in case if power is missing from json, prevent crashes
        if ATTR_POWER not in self.coordinator.data:
            return

        if operation_mode == STATE_OFF and self.coordinator.data[ATTR_POWER] == "1":
            response = await self.coordinator.async_set_power("0")
            await self.partially_update_data_from_api(response, ATTR_POWER)
        else:
            if self.coordinator.data[ATTR_POWER] == "0":
                response = await self.coordinator.async_set_power("1")
                await self.partially_update_data_from_api(response, ATTR_POWER)

            if operation_mode == STATE_PERFORMANCE:
                new_mode = "0"
                # await self.coordinator.async_set_operation_mode("0")
            if operation_mode == TESY_MODE_P1:
                new_mode = "1"
                # await self.coordinator.async_set_operation_mode("1")
            if operation_mode == TESY_MODE_P2:
                new_mode = "2"
                # await self.coordinator.async_set_operation_mode("2")
            if operation_mode == TESY_MODE_P3:
                new_mode = "3"
                # await self.coordinator.async_set_operation_mode("3")
            if operation_mode == STATE_ECO:
                new_mode = "4"
                # await self.coordinator.async_set_operation_mode("4")
            if operation_mode == TESY_MODE_EC2:
                new_mode = "4"
                # await self.coordinator.async_set_operation_mode("5")
            if operation_mode == TESY_MODE_EC3:
                new_mode = "6"
                # await self.coordinator.async_set_operation_mode("6")

            response = await self.coordinator.async_set_operation_mode(new_mode)
            await self.partially_update_data_from_api(response, ATTR_MODE)

        # await self.coordinator.async_request_refresh()

    async def turn_on(self, **_kwargs: Any) -> None:
        """Turn on water heater."""
        response = await self.coordinator.async_set_power("1")
        await self.partially_update_data_from_api(response, ATTR_POWER)
        # await self.coordinator.async_request_refresh()

    async def turn_off(self, **_kwargs: Any) -> None:
        """Turn off water heater."""
        response = await self.coordinator.async_set_power("0")
        await self.partially_update_data_from_api(response, ATTR_POWER)
        # await self.coordinator.async_request_refresh()

    @property
    def target_temperature(self):
        """Return the target temperature."""
        # Return setpoint do
        return float(self.coordinator.data[ATTR_TARGET_TEMP])

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the state attributes."""
        return {
            "is_heating": ATTR_IS_HEATING in self.coordinator.data
            and self.coordinator.data[ATTR_IS_HEATING] == "1",
            "target_temp_step": 1,
        }
