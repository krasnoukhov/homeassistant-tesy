"""Base entity for the Tesy integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import (
    CONNECTION_NETWORK_MAC,
    DeviceInfo,
    format_mac,
)
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    TESY_DEVICE_TYPES,
    ATTR_DEVICE_ID,
    ATTR_MAC,
    ATTR_BOOST,
    ATTR_CHILD_LOCK,
    ATTR_CURRENT_TARGET_TEMP,
    ATTR_HARDWARE,
    ATTR_MODE,
    ATTR_POWER,
    ATTR_TARGET_TEMP,
    ATTR_SOFTWARE,
    DOMAIN,
    ATTR_API,
)
from .coordinator import TesyCoordinator

import logging

_LOGGER = logging.getLogger(__name__)


def _is_ok(response) -> bool:
    """Return True if a setter reply reports success."""
    return isinstance(response, dict) and response.get(ATTR_API) == "OK"


class TesyEntity(CoordinatorEntity[TesyCoordinator]):
    """Defines a base Tesy entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: TesyCoordinator,
        entry: ConfigEntry,
        description: EntityDescription,
    ) -> None:
        """Initialize a Tesy entity."""
        super().__init__(coordinator)

        self.entity_description = description
        self.hass = hass
        self._entry = entry

        self._attr_unique_id = "-".join(
            [
                coordinator.data[ATTR_MAC],
                description.key,
            ]
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Tesy device."""
        device_model = "Generic"
        if self.coordinator.data[ATTR_DEVICE_ID] in TESY_DEVICE_TYPES:
            device_model = TESY_DEVICE_TYPES[self.coordinator.data[ATTR_DEVICE_ID]][
                "name"
            ]

        return DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    self.coordinator.data[ATTR_MAC],
                )
            },
            # Links the device to others that know the heater's MAC (a router
            # integration, for example); both APIs' formats are normalised.
            connections={
                (CONNECTION_NETWORK_MAC, format_mac(self.coordinator.data[ATTR_MAC]))
            },
            manufacturer="Tesy",
            model=device_model,
            sw_version=self.coordinator.data[ATTR_SOFTWARE],
            hw_version=self.coordinator.data.get(ATTR_HARDWARE),
        )

    @property
    def is_boost_mode_on(self):
        """Return true if boost mode is on."""
        if (
            ATTR_BOOST in self.coordinator.data
            and self.coordinator.data[ATTR_BOOST] == "1"
        ):
            return True
        return False

    async def async_turn_boost_mode_on(self, **kwargs):
        """Turn on boost mode."""

        if self.coordinator.data[ATTR_BOOST] == "0":
            response = await self.coordinator.async_set_boost("1")
            await self.partially_update_data_from_api(response, ATTR_BOOST)

    async def async_turn_boost_mode_off(self, **kwargs):
        """Turn off boost mode."""

        if self.coordinator.data[ATTR_BOOST] == "1":
            response = await self.coordinator.async_set_boost("0")
            await self.partially_update_data_from_api(response, ATTR_BOOST)

    @property
    def is_child_lock_on(self):
        """Return true if child lock is on."""
        return (
            ATTR_CHILD_LOCK in self.coordinator.data
            and self.coordinator.data[ATTR_CHILD_LOCK] == "1"
        )

    async def async_turn_child_lock_on(self, **kwargs):
        """Turn on child lock."""

        if ATTR_CHILD_LOCK not in self.coordinator.data:
            return
        if self.coordinator.data[ATTR_CHILD_LOCK] == "0":
            response = await self.coordinator.async_set_child_lock("1")
            await self.partially_update_data_from_api(response, ATTR_CHILD_LOCK)

    async def async_turn_child_lock_off(self, **kwargs):
        """Turn off child lock."""

        if ATTR_CHILD_LOCK not in self.coordinator.data:
            return
        if self.coordinator.data[ATTR_CHILD_LOCK] == "1":
            response = await self.coordinator.async_set_child_lock("0")
            await self.partially_update_data_from_api(response, ATTR_CHILD_LOCK)

    async def async_set_manual_target(self, value: int) -> None:
        """Set the manual target (tmpT), switching to manual mode if on.

        tmpT is not written if switching to manual mode fails. Failures are
        raised as HomeAssistantError.
        """
        # Just in case if power is missing from json, prevent crashes
        if ATTR_POWER not in self.coordinator.data:
            return

        try:
            if (
                self.coordinator.data[ATTR_POWER] == "1"
                and self.coordinator.data.get(ATTR_MODE) != "0"
            ):
                response = await self.coordinator.async_set_operation_mode("0")
                if not _is_ok(response):
                    raise HomeAssistantError(
                        "Heater did not switch to manual mode; target not set"
                    )
                await self.partially_update_data_from_api(response, ATTR_MODE)

            response = await self.coordinator.async_set_target_temperature(value)
        except ConnectionError as err:
            # The client wraps transport errors in a bare ConnectionError
            reason = str(err) or (
                f"Cannot reach heater: {type(err.__cause__ or err).__name__}"
            )
            raise HomeAssistantError(reason) from err
        except ValueError as err:  # not JSON
            raise HomeAssistantError("Invalid response from heater") from err

        if not _is_ok(response):
            raise HomeAssistantError("Heater rejected the target")
        await self.partially_update_data_from_api(
            response, ATTR_TARGET_TEMP, ATTR_CURRENT_TARGET_TEMP
        )

        # Optimistic, but keep what the heater echoed: it may clamp the value.
        # In manual mode, tmpR always equals tmpT.
        data = self.coordinator.data
        if ATTR_TARGET_TEMP not in response:
            data[ATTR_TARGET_TEMP] = str(value)
        if data.get(ATTR_MODE) == "0" and ATTR_CURRENT_TARGET_TEMP not in response:
            data[ATTR_CURRENT_TARGET_TEMP] = data[ATTR_TARGET_TEMP]
        self.coordinator.async_set_updated_data(data)

    async def partially_update_data_from_api(self, response, *keys):
        if ATTR_API not in response or response[ATTR_API] != "OK":
            return

        updated = {key: response[key] for key in keys if key in response}
        if not updated:
            return

        old_data = self.coordinator.data
        old_data.update(updated)
        self.coordinator.async_set_updated_data(old_data)
        _LOGGER.debug("Partial update: %s", updated)
