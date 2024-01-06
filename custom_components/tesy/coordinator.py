"""DataUpdateCoordinator for the Tesy integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .tesy import Tesy
from .const import (
    ATTR_API,
    DOMAIN,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class TesyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Tesy Coordinator class."""

    def __init__(self, data: dict[str, Any], hass: HomeAssistant) -> None:
        """Initialize."""
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

    def _get_data(self) -> dict[str, Any]:
        """Get new sensor data using Tesy API."""
        try:
            return self._client.get_data()
        except ConnectionError as http_error:
            raise UpdateFailed from http_error

    async def _async_update_data(self) -> dict[str, Any]:
        """Get new sensor data for Tesy component."""
        return await self.hass.async_add_executor_job(self._get_data)

    def _set_target_temperature(self, val: int) -> None:
        """Set target temperature using Tesy API."""
        return self._client.set_target_temperature(val)

    async def async_set_target_temperature(self, val: int) -> None:
        """Set target temperature for Tesy component."""
        return await self.hass.async_add_executor_job(self._set_target_temperature, val)

    def _set_power(self, val: str) -> None:
        """Set power using Tesy API."""
        return self._client.set_power(val)
    
    def _set_operation_mode(self, val: str) -> None:
        """Set mode using Tesy API."""
        return self._client.set_operation_mode(val)
    

    async def async_set_power(self, val: str) -> None:
        """Set power for Tesy component."""
        return await self.hass.async_add_executor_job(self._set_power, val)
    
    async def async_set_boost(self, val: str) -> None:
        """Set boost for Tesy component."""
        return await self.hass.async_add_executor_job(self._client.set_boost(val), val)
    
    async def async_set_operation_mode(self, val: str) -> None:
        """Set mode for Tesy component."""
        return await self.hass.async_add_executor_job(self._set_operation_mode, val)
