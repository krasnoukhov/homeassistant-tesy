"""The Tesy integration."""

from __future__ import annotations

import logging

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_CORE_CONFIG_UPDATE, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .card import CARD_PATH, CARD_URL, TesyCardVersionView, TesyCardView, card_hash
from .coordinator import TesyCoordinator
from .lovelace_resource import plan_removal, plan_resource
from .const import (
    DOMAIN,
    SCAN_INTERVAL,
    UPDATE_INTERVAL,
)

PLATFORMS: list[Platform] = [
    Platform.WATER_HEATER,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
]

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
CARD_DATA = f"{DOMAIN}_card"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the tesy-boiler-card.

    The Lovelace card ships with the integration: no separate install needed.
    It is registered as a dashboard resource once a heater model that supports
    it is set up (see _async_load_card).
    """
    if hass.http is None:
        return True
    content = await hass.async_add_executor_job(CARD_PATH.read_bytes)
    version = card_hash(content)
    hass.http.register_view(TesyCardView(content))
    hass.http.register_view(TesyCardVersionView(version))
    hass.data[CARD_DATA] = {"version": version, "loaded": False}
    return True


def _lovelace_resources(hass: HomeAssistant):
    """Return (resource mode, resource collection) of the dashboards, if any."""
    data = hass.data.get("lovelace")
    if data is None:
        return None, None
    if isinstance(data, dict):  # older Home Assistant
        return data.get("resource_mode") or data.get("mode"), data.get("resources")
    mode = getattr(data, "resource_mode", None) or getattr(data, "mode", None)
    return mode, getattr(data, "resources", None)


def _card_url(hass: HomeAssistant) -> str | None:
    card = hass.data.get(CARD_DATA)
    return None if card is None else f"{CARD_URL}?v={card['version']}"


async def _async_load_card(hass: HomeAssistant) -> None:
    """Add the card to the frontend, once.

    Storage-mode dashboards get a resource whose URL carries the card's hash,
    kept up to date on every start: nothing to add by hand, and an updated card
    is loaded instead of a cached copy (the card itself reloads pages opened
    before the update). YAML mode cannot be changed from here, so the card is
    added to every page instead.
    """
    card = hass.data.get(CARD_DATA)
    if card is None or card["loaded"]:
        return
    card["loaded"] = True
    url = _card_url(hass)
    mode, resources = _lovelace_resources(hass)
    if mode == "storage" and hasattr(resources, "async_create_item"):
        try:
            await resources.async_get_info()  # loads the stored resources
            plan = plan_resource(list(resources.async_items()), url)
            for other in plan.foreign_urls:
                _LOGGER.warning(
                    "Dashboard resource %s also loads the Tesy card and may load "
                    "an old copy; remove it in Settings → Dashboards → Resources",
                    other,
                )
            for item_id in plan.delete_ids:
                await resources.async_delete_item(item_id)
            if plan.update_id:
                await resources.async_update_item(
                    plan.update_id, {"res_type": "module", "url": url}
                )
            elif plan.create:
                await resources.async_create_item({"res_type": "module", "url": url})
            if plan.changes:
                _LOGGER.info("Tesy card resource set to %s", url)
            return
        except Exception:  # noqa: BLE001 - never block setup over the card
            _LOGGER.warning(
                "Could not register the Tesy card as a dashboard resource; "
                "loading it on every page instead",
                exc_info=True,
            )
    add_extra_js_url(hass, url)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tesy from a config entry."""
    coordinator = TesyCoordinator(
        entry.data,
        hass,
        scan_interval=entry.options.get(SCAN_INTERVAL, UPDATE_INTERVAL),
    )

    try:
        await coordinator.async_validate_input()
    except ConnectionError as connection_error:
        raise ConfigEntryAuthFailed from connection_error

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    if coordinator.supports_timezone:
        await coordinator.async_expected_timezone()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    if coordinator.supports_card:
        await _async_load_card(hass)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    # Follow-up polls and time zone writes must not outlive the entry.
    entry.async_on_unload(coordinator.async_close)

    if coordinator.supports_timezone:
        # Keep the heater's time zone (it drives the weekly programs) in step
        # with Home Assistant: now, and whenever the HA time zone changes.
        await _async_sync_timezone(coordinator)

        @callback
        def _core_config_updated(event: Event) -> None:
            hass.async_create_task(_async_sync_timezone(coordinator))

        entry.async_on_unload(
            hass.bus.async_listen(EVENT_CORE_CONFIG_UPDATE, _core_config_updated)
        )

    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Apply a new poll interval."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_sync_timezone(coordinator: TesyCoordinator) -> None:
    """Sync the heater time zone, logging instead of failing."""
    # Resolve the (possibly new) HA zone first so the clock sensor sees it.
    await coordinator.async_expected_timezone()
    coordinator.async_update_listeners()
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


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove the card resource together with the last heater."""
    others = [
        e
        for e in hass.config_entries.async_entries(DOMAIN)
        if e.entry_id != entry.entry_id
    ]
    url = _card_url(hass)
    mode, resources = _lovelace_resources(hass)
    if others or url is None or mode != "storage":
        return
    if not hasattr(resources, "async_delete_item"):
        return
    try:
        await resources.async_get_info()
        for item_id in plan_removal(list(resources.async_items()), url):
            await resources.async_delete_item(item_id)
    except Exception:  # noqa: BLE001 - removal must not fail over the card
        _LOGGER.warning("Could not remove the Tesy card resource", exc_info=True)
