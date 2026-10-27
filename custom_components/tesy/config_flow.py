"""Config flow for Tesy integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import AbortFlow
import homeassistant.helpers.config_validation as cv

from .const import (
    ATTR_MAC,
    DOMAIN,
    IP_ADDRESS,
    HEATER_POWER,
    MAX_SCAN_INTERVAL,
    SCAN_INTERVAL,
    SYNC_TIMEZONE,
    min_scan_interval,
    UPDATE_INTERVAL,
    ATTR_DEVICE_ID,
    TESY_DEVICE_TYPES,
    USE_OLD_API,
)
from .coordinator import TesyCoordinator

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(IP_ADDRESS): cv.string,
        vol.Required(HEATER_POWER): cv.positive_int,
        vol.Required(USE_OLD_API): cv.boolean,
    }
)

RECONFIGURE_FIELDS = (IP_ADDRESS, HEATER_POWER)
# Entries made before the power was asked for have none: left empty, the
# power in use (the client's default) is kept.
RECONFIGURE_SCHEMA = vol.Schema(
    {
        vol.Required(IP_ADDRESS): cv.string,
        vol.Optional(HEATER_POWER): cv.positive_int,
    }
)


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from USER_SCHEMA with values provided by the user.
    """

    coordinator = TesyCoordinator(data, hass)
    result = await coordinator.async_validate_input()

    title = "Tesy"

    if ATTR_DEVICE_ID in result and result[ATTR_DEVICE_ID] in TESY_DEVICE_TYPES:
        title = TESY_DEVICE_TYPES[result[ATTR_DEVICE_ID]]["name"]

    return {"title": title, "unique_id": result[ATTR_MAC]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tesy."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Options: poll interval."""
        return TesyOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=USER_SCHEMA, errors={}
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)

            await self.async_set_unique_id(info["unique_id"])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=info["title"], data=user_input)
        except ConnectionError:
            errors["base"] = "cannot_connect"
        except AbortFlow as abort_flow_error:
            errors["base"] = abort_flow_error.reason
        except Exception as exception_error:  # pylint: disable=broad-except
            _LOGGER.exception(f"Unexpected exception {exception_error}")
            errors["base"] = "unknown"

        data_schema = self.add_suggested_values_to_schema(USER_SCHEMA, user_input)
        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_reconfigure(self, user_input=None):
        """Change the IP address or heater power of an existing heater.

        The API type is kept: the old API reports the MAC in another format,
        so the heater could not be matched to the entry.
        """
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        errors = {}

        if user_input is not None:
            data = {**entry.data, **user_input}
            try:
                info = await validate_input(self.hass, data)
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except Exception as exception_error:  # pylint: disable=broad-except
                _LOGGER.exception(f"Unexpected exception {exception_error}")
                errors["base"] = "unknown"
            else:
                # Another heater answers at this address: keep the entry as is
                if entry.unique_id and info["unique_id"] != entry.unique_id:
                    errors["base"] = "wrong_device"
                else:
                    # A loaded entry is reloaded by its update listener (which
                    # starts at once); one that is not, e.g. retrying at the
                    # old address, has no listener.
                    loaded = entry.state is ConfigEntryState.LOADED
                    self.hass.config_entries.async_update_entry(entry, data=data)
                    if not loaded and entry.disabled_by is None:
                        self.hass.config_entries.async_schedule_reload(entry.entry_id)
                    return self.async_abort(reason="reconfigure_successful")

        data_schema = self.add_suggested_values_to_schema(
            RECONFIGURE_SCHEMA,
            user_input or {key: entry.data.get(key) for key in RECONFIGURE_FIELDS},
        )
        return self.async_show_form(
            step_id="reconfigure", data_schema=data_schema, errors=errors
        )


class TesyOptionsFlow(config_entries.OptionsFlow):
    """Let the user pick how often the heater is polled."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        """Keep the entry (older HA versions do not set config_entry)."""
        self._entry = entry

    async def async_step_init(self, user_input=None):
        """Show and store the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        old_api = bool(self._entry.data.get(USE_OLD_API))
        minimum = min_scan_interval(old_api)
        current = max(minimum, self._entry.options.get(SCAN_INTERVAL, UPDATE_INTERVAL))
        fields: dict[Any, Any] = {
            vol.Required(SCAN_INTERVAL, default=current): vol.All(
                vol.Coerce(int),
                vol.Range(min=minimum, max=MAX_SCAN_INTERVAL),
            )
        }
        if not old_api:  # the old API has no time zone field
            fields[
                vol.Required(
                    SYNC_TIMEZONE,
                    default=self._entry.options.get(SYNC_TIMEZONE, True),
                )
            ] = cv.boolean
        schema = vol.Schema(fields)
        return self.async_show_form(step_id="init", data_schema=schema)
