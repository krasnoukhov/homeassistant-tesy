"""DataUpdateCoordinator for the Tesy integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .features import FEATURE_SCHEDULE, device_features
from .tesy import Tesy
from .tesy_oldapi import TesyOldApi
from .const import (
    ATTR_API,
    ATTR_CHILD_LOCK,
    DOMAIN,
    UPDATE_INTERVAL,
    USE_OLD_API,
)
import logging

_LOGGER = logging.getLogger(__name__)


class TesyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Tesy Coordinator class."""

    def __init__(self, data: dict[str, Any], hass: HomeAssistant) -> None:
        """Initialize."""
        if data.get(USE_OLD_API):
            self._client = TesyOldApi(data)
        else:
            self._client = Tesy(data)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    def _validate(self) -> None:
        """Validate using Tesy API."""
        result = self._client.get_data()
        if result.get(ATTR_API) != "OK":
            raise ConnectionError
        return result

    async def async_validate_input(self) -> None:
        """Validate Tesy component."""
        return await self.hass.async_add_executor_job(self._validate)

    # Async update Data
    async def _async_update_data(self) -> dict[str, Any]:
        """Get new sensor data for Tesy component."""
        return await self.hass.async_add_executor_job(self._get_data)

    # Set target temperature in manual mode
    async def async_set_target_temperature(self, val: int) -> None:
        """Set target temperature for Tesy component."""
        return await self.hass.async_add_executor_job(
            self._client.set_target_temperature, val
        )

    # Turn power ON/OFF
    async def async_set_power(self, val: str) -> None:
        """Set power for Tesy component."""
        return await self.hass.async_add_executor_job(self._client.set_power, val)

    # Turn boost ON/OFF
    async def async_set_boost(self, val: str) -> None:
        """Set boost for Tesy component."""
        return await self.hass.async_add_executor_job(self._client.set_boost, val)

    # Turn operation mode
    async def async_set_operation_mode(self, val: str) -> None:
        """Set mode for Tesy component."""
        return await self.hass.async_add_executor_job(
            self._client.set_operation_mode, val
        )

    # Set child lock
    async def async_set_child_lock(self, val: str) -> None:
        """Set child lock for Tesy component."""
        return await self.hass.async_add_executor_job(self._client.set_child_lock, val)

    async def async_set_schedule(self, key: str, val: str) -> dict[str, Any]:
        """Write one day of a weekly program."""
        if self.is_old_api:
            raise NotImplementedError("Schedules are not supported by the old API")
        return await self.hass.async_add_executor_job(
            self._client.set_schedule, key, val
        )

    async def async_reset_energy_counter(self) -> dict[str, Any]:
        """Reset the resettable energy counter."""
        return await self.hass.async_add_executor_job(self._client.reset_energy_counter)

    def _get_data(self) -> dict[str, Any]:
        """Get new sensor data using Tesy API."""
        try:
            result = self._client.get_data()
        except ConnectionError as http_error:
            cause = http_error.__cause__ or http_error
            _LOGGER.debug("Cannot reach heater: %r", cause)
            raise UpdateFailed(
                f"Cannot reach heater: {type(cause).__name__}"
            ) from http_error
        except (ValueError, KeyError, TypeError, AttributeError) as err:
            # Non-JSON or malformed response
            raise UpdateFailed(f"Invalid response from heater: {err!r}") from err
        # Report only the type or api value: the payload includes the MAC address
        if not isinstance(result, dict):
            raise UpdateFailed(f"Invalid response from heater: {type(result).__name__}")
        if result.get(ATTR_API) != "OK":
            raise UpdateFailed(
                f"Invalid response from heater: api={result.get(ATTR_API)!r}"
            )
        return result

    def get_config_power(self) -> int:
        return self._client._heater_power

    @property
    def is_old_api(self) -> bool:
        """Return True if the device is accessed via the old (unofficial) API."""
        return isinstance(self._client, TesyOldApi)

    @property
    def features(self) -> frozenset[str]:
        """Extended features enabled for this heater model (see features.py)."""
        if self.is_old_api:
            return frozenset()
        return device_features(self.data)

    @property
    def supports_schedule(self) -> bool:
        """Return True if weekly programs are enabled for this heater."""
        return FEATURE_SCHEDULE in self.features
