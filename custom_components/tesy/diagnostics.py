"""Diagnostics support for the Tesy integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, TO_REDACT
from .coordinator import TesyCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return the entry settings and the heater's last reply, without personal data."""
    diagnostics: dict[str, Any] = {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
    }

    # Not loaded (e.g. the heater is unreachable): only the settings are known
    coordinator: TesyCoordinator | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator is not None:
        diagnostics.update(
            {
                "old_api": coordinator.is_old_api,
                "features": sorted(coordinator.features),
                "last_update_success": coordinator.last_update_success,
                "data": async_redact_data(coordinator.data or {}, TO_REDACT),
            }
        )
    return diagnostics
