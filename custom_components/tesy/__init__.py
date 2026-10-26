"""The Tesy integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_CORE_CONFIG_UPDATE, Platform
from homeassistant.core import Event, HomeAssistant, callback

from .coordinator import TesyCoordinator
from .const import (
    DOMAIN,
    SCAN_INTERVAL,
    SYNC_TIMEZONE,
    UPDATE_INTERVAL,
    USE_OLD_API,
    min_scan_interval,
)

PLATFORMS: list[Platform] = [
    Platform.WATER_HEATER,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.NUMBER,
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tesy from a config entry."""
    coordinator = TesyCoordinator(
        entry.data,
        hass,
        scan_interval=max(
            min_scan_interval(bool(entry.data.get(USE_OLD_API))),
            entry.options.get(SCAN_INTERVAL, UPDATE_INTERVAL),
        ),
    )

    # Raises ConfigEntryNotReady (HA retries setup) if the heater is unreachable
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    if coordinator.supports_timezone:
        await coordinator.async_expected_timezone()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    # Follow-up polls and time zone writes must not outlive the entry.
    entry.async_on_unload(coordinator.async_close)

    if coordinator.supports_timezone:
        # Keep the heater's time zone (it drives the weekly programs) in step
        # with Home Assistant: now, and whenever the HA time zone changes.
        # The writes can be turned off in the options (e.g. HA's own zone is
        # wrong); the expected zone is still followed for the clock sensor.
        sync = entry.options.get(SYNC_TIMEZONE, True)

        @callback
        def _core_config_updated(event: Event) -> None:
            hass.async_create_task(_async_timezone_changed(coordinator, sync))

        # Listen before the start-up sync, so a change during it is not missed;
        # syncs run one at a time and the last one writes the newest zone.
        entry.async_on_unload(
            hass.bus.async_listen(EVENT_CORE_CONFIG_UPDATE, _core_config_updated)
        )
        if sync:
            await _async_timezone_changed(coordinator, sync)

    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply new options (poll interval, time zone sync)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_timezone_changed(coordinator: TesyCoordinator, sync: bool) -> None:
    """Follow HA's time zone; write it to the heater if sync is on.

    Logs instead of failing.
    """
    # Resolve the (possibly new) HA zone first so the clock sensor sees it.
    await coordinator.async_expected_timezone()
    coordinator.async_update_listeners()
    if not sync:
        return
    try:
        await coordinator.async_sync_timezone()
    except (ConnectionError, ValueError) as err:
        _LOGGER.warning("Could not sync the heater time zone: %s", err)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: TesyCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        # Let a request already on its way finish before a reload starts a new
        # coordinator: the heater gets one request at a time.
        coordinator.async_close()
        await coordinator.async_wait_idle()

    return unload_ok
