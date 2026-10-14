"""DataUpdateCoordinator for the Tesy integration."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .features import FEATURE_CARD, FEATURE_SCHEDULE, FEATURE_TIMEZONE, device_features
from .tesy import Tesy
from .timezone import TZ_FIELD, posix_tz_for
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

    def __init__(
        self,
        data: dict[str, Any],
        hass: HomeAssistant,
        scan_interval: int = UPDATE_INTERVAL,
    ) -> None:
        """Initialize."""
        if data.get(USE_OLD_API):
            self._client = TesyOldApi(data)
        else:
            self._client = Tesy(data)
        self._posix_tz_cache: dict[str, str | None] = {}
        self._refresh_unsub = None
        self._commands_in_flight = 0
        self._closed = False
        self._tz_lock = asyncio.Lock()
        # One request to the heater at a time: polls and commands never overlap,
        # so a read started before a write cannot report the pre-write state.
        self._io_lock = asyncio.Lock()
        # When the last _all reply arrived: its date is the heater clock then.
        self.data_received_at: datetime | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
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
        async with self._io_lock:
            if self._closed:  # unloading: no new request to the heater
                return self.data
            data = await self.hass.async_add_executor_job(self._get_data)
            if self._closed:  # unloaded while waiting for the reply: drop it
                return self.data
            self.data_received_at = dt_util.utcnow()
        return data

    async def _async_command(self, func, *args) -> Any:
        """Send a command to the heater and read its state back soon after.

        The reply only echoes the written field; the heating state, active
        target, device time and the like follow on the next poll. Every command
        goes through here, so none of them waits for the regular poll.

        A pending poll is cancelled before the command is sent and scheduled
        again once no command is in flight, so a batch (a schedule written day
        by day, however slowly) is read back once, after its last write.
        """
        self.async_cancel_refresh()
        self._commands_in_flight += 1
        try:
            async with self._io_lock:
                if self._closed:  # unloading began while this waited its turn
                    raise ConnectionError("The Tesy integration is unloading")
                return await self.hass.async_add_executor_job(func, *args)
        finally:
            self._commands_in_flight -= 1
            if not self._commands_in_flight:
                self.async_refresh_soon()

    @callback
    def async_close(self) -> None:
        """Entry unloading: no more follow-up polls or time zone writes.

        A command still running when the entry unloads would otherwise schedule
        a poll after the unload, from a coordinator nothing uses any more.
        """
        self._closed = True
        self.async_cancel_refresh()

    async def async_wait_idle(self) -> None:
        """Wait until no request to the heater is in flight.

        A request cannot be cancelled once its thread has started; unloading
        waits for it, so a reloaded entry never talks to the heater at the same
        time. Its result is dropped (see _async_update_data).
        """
        async with self._io_lock:
            pass

    @callback
    def async_cancel_refresh(self) -> None:
        """Cancel a pending follow-up poll (before a command, or on unload)."""
        if self._refresh_unsub:
            self._refresh_unsub()
            self._refresh_unsub = None

    # Set target temperature in manual mode
    async def async_set_target_temperature(self, val: int) -> None:
        """Set target temperature for Tesy component."""
        return await self._async_command(self._client.set_target_temperature, val)

    # Turn power ON/OFF
    async def async_set_power(self, val: str) -> None:
        """Set power for Tesy component."""
        return await self._async_command(self._client.set_power, val)

    # Turn boost ON/OFF
    async def async_set_boost(self, val: str) -> None:
        """Set boost for Tesy component."""
        return await self._async_command(self._client.set_boost, val)

    # Turn operation mode
    async def async_set_operation_mode(self, val: str) -> None:
        """Set mode for Tesy component."""
        return await self._async_command(self._client.set_operation_mode, val)

    # Set child lock
    async def async_set_child_lock(self, val: str) -> None:
        """Set child lock for Tesy component."""
        return await self._async_command(self._client.set_child_lock, val)

    async def async_set_schedule(self, key: str, val: str) -> dict[str, Any]:
        """Write one day of a weekly program."""
        if self.is_old_api:
            raise NotImplementedError("Schedules are not supported by the old API")
        return await self._async_command(self._client.set_schedule, key, val)

    @callback
    def async_refresh_soon(self, delay: float = 2.0) -> None:
        """Poll the heater shortly after a command (debounced).

        Several commands in a row (e.g. a schedule written day by day) lead to
        one poll after the last of them.
        """
        self.async_cancel_refresh()
        if self._closed:
            return

        @callback
        def _run(_now) -> None:
            self._refresh_unsub = None
            if not self._closed:
                # async_refresh, not async_request_refresh: this timer already
                # batches commands; the coordinator's 10 s request debounce on
                # top would delay a second command's readback.
                self.hass.async_create_task(self.async_refresh())

        self._refresh_unsub = async_call_later(self.hass, delay, _run)

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

    @property
    def supports_timezone(self) -> bool:
        """Return True if time zone sync is enabled for this heater."""
        return FEATURE_TIMEZONE in self.features

    @property
    def supports_card(self) -> bool:
        """Return True if the thermostat card supports this heater."""
        return FEATURE_CARD in self.features

    @property
    def expected_timezone(self) -> str | None:
        """POSIX TZ string for Home Assistant's zone, once resolved."""
        return self._posix_tz_cache.get(self.hass.config.time_zone)

    async def async_expected_timezone(self) -> str | None:
        """Return the POSIX TZ string matching Home Assistant's time zone."""
        name = self.hass.config.time_zone
        if name not in self._posix_tz_cache:
            self._posix_tz_cache[name] = await self.hass.async_add_executor_job(
                posix_tz_for, name
            )
        return self._posix_tz_cache[name]

    async def async_sync_timezone(self, force: bool = False) -> bool:
        """Write Home Assistant's time zone to the device if it differs.

        With force (the Sync time zone button) it is written even if the last
        poll showed the right zone: it may have been changed on the panel or in
        MyTESY since. Returns True if the device was written.
        """
        # One sync at a time: two HA zone changes in a row must not race, the
        # last one wins. The zone is looked up again inside the lock.
        async with self._tz_lock:
            return await self._async_sync_timezone_locked(force)

    async def _async_sync_timezone_locked(self, force: bool) -> bool:
        if self._closed or not self.supports_timezone:
            return False
        expected = await self.async_expected_timezone()
        if self._closed:  # unloaded while the zone was being looked up
            return False
        if expected is None:
            raise ValueError(
                f"{self.hass.config.time_zone} cannot be expressed as a POSIX "
                "time zone for the heater (no rule string, or it does not match "
                "the zone's coming changes); set the clock on the heater panel"
            )
        if not force and self.data.get(TZ_FIELD) == expected:
            return False

        # The follow-up poll also brings the device time (date) in the new zone.
        response = await self._async_command(self._client.set_timezone, expected)
        if response.get(ATTR_API) != "OK" or response.get(TZ_FIELD) != expected:
            raise ConnectionError(f"Heater rejected time zone {expected}: {response}")

        _LOGGER.info(
            "Tesy time zone changed from %s to %s", self.data.get(TZ_FIELD), expected
        )
        self.data[TZ_FIELD] = expected
        self.async_set_updated_data(self.data)
        return True

    async def async_reset_energy_counter(self) -> dict[str, Any]:
        """Reset the resettable energy counter."""
        return await self._async_command(self._client.reset_energy_counter)

    def _get_data(self) -> dict[str, Any]:
        """Get new sensor data using Tesy API."""
        try:
            return self._client.get_data()
        except ConnectionError as http_error:
            raise UpdateFailed from http_error

    def get_config_power(self) -> int:
        return self._client._heater_power

    @property
    def is_old_api(self) -> bool:
        """Return True if the device is accessed via the old (unofficial) API."""
        return isinstance(self._client, TesyOldApi)
