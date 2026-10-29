"""Tesy number component."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_DEVICE_ID,
    ATTR_TARGET_TEMP,
    DOMAIN,
    TESY_DEVICE_TYPES,
    UNIT_SHOWERS,
)
from .coordinator import TesyCoordinator
from .entity import TesyEntity
from .helpers import max_showers, to_float, uses_showers


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize Tesy devices from config entry."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Only shower models: the water heater sets the target on the others
    if not uses_showers(coordinator.data.get(ATTR_DEVICE_ID), coordinator.is_old_api):
        return

    async_add_entities(
        [
            TesyTargetShowersNumber(
                hass,
                coordinator,
                entry,
                NumberEntityDescription(
                    key="target_showers",
                    translation_key="target_showers",
                ),
            )
        ]
    )


class TesyTargetShowersNumber(TesyEntity, NumberEntity):
    """Target showers (tmpT) of a shower model."""

    _attr_native_step = 1
    _attr_native_unit_of_measurement = UNIT_SHOWERS

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: TesyCoordinator,
        entry: ConfigEntry,
        description: NumberEntityDescription,
    ) -> None:
        super().__init__(hass, coordinator, entry, description)

        device_type = TESY_DEVICE_TYPES[coordinator.data[ATTR_DEVICE_ID]]
        self._attr_native_min_value = device_type["min_setpoint"]
        self._default_max = device_type["max_setpoint"]

    @property
    def native_max_value(self) -> float:
        """Return the maximum showers, which depend on size and position."""
        return max_showers(self.coordinator.data, self._default_max)

    @property
    def native_value(self) -> float | None:
        """Return the manual target; the Active Target sensor shows tmpR."""
        return to_float(self.coordinator.data.get(ATTR_TARGET_TEMP))

    async def async_set_native_value(self, value: float) -> None:
        """Set the target showers, switching to manual mode like the heater."""
        await self.async_set_manual_target(round(value))
