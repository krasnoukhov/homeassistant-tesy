"""Tesy water heater component."""
from typing import Any

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
    ATTR_CURRENT_TEMP,
    ATTR_IS_HEATING,
    ATTR_MODE,
    ATTR_POWER,
    ATTR_TARGET_TEMP,
    DOMAIN,
)
from .entity import TesyEntity

# NOTE: more modes not implemented
OPERATION_LIST = [STATE_OFF, STATE_PERFORMANCE]

DESCRIPTION = WaterHeaterEntityEntityDescription(
    key="water_heater",
    translation_key="heater",
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create Tesy water heater in HASS."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([TesyWaterHeater(hass, coordinator, config_entry, DESCRIPTION)])


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
    _attr_min_temp = 16
    _attr_max_temp = 75

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return float(self.coordinator.data[ATTR_CURRENT_TEMP])

    @property
    def current_operation(self):
        """Return current operation."""
        state = STATE_OFF
        mode = self.coordinator.data[ATTR_MODE]

        if self.coordinator.data[ATTR_POWER] != "1":
            return state

        if mode == "0":
            state = STATE_PERFORMANCE
        if mode == "1":
            state = "Program"
        if mode == "3":
            state = STATE_ECO

        return state

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        await self.coordinator.async_set_target_temperature(
            kwargs.get(ATTR_TEMPERATURE)
        )
        await self.coordinator.async_request_refresh()

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new target operation mode."""
        if operation_mode == STATE_PERFORMANCE:
            await self.turn_on()
        else:
            await self.turn_off()

    async def turn_on(self, **_kwargs: Any) -> None:
        """Turn on water heater."""
        await self.coordinator.async_set_power("1")
        await self.coordinator.async_request_refresh()

    async def turn_off(self, **_kwargs: Any) -> None:
        """Turn off water heater."""
        await self.coordinator.async_set_power("0")
        await self.coordinator.async_request_refresh()

    @property
    def target_temperature(self):
        """Return the target temperature."""
        return float(self.coordinator.data[ATTR_TARGET_TEMP])

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the state attributes."""
        return {"is_heating": self.coordinator.data[ATTR_IS_HEATING] == "1"}
