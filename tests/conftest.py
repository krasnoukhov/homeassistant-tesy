"""Mock all homeassistant.* modules so tests run without a full HA installation."""

import os
import sys
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Minimal stub classes replacing the real HA base classes
# ---------------------------------------------------------------------------


class _CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator

    async def async_added_to_hass(self):
        pass

    def _handle_coordinator_update(self):
        pass  # real impl calls async_write_ha_state()


class _SensorEntity:
    pass


class _RestoreEntity:
    async def async_added_to_hass(self):
        pass

    async def async_get_last_sensor_data(self):
        return None


class _RestoreSensor(_SensorEntity, _RestoreEntity):
    async def async_added_to_hass(self):
        await _RestoreEntity.async_added_to_hass(self)

    async def async_get_last_sensor_data(self):
        return None


def _callback(func):
    """HA @callback decorator — return the function unchanged."""
    return func


# TesyEntity stub: mirrors the real __init__ signature so sensor.py can
# instantiate TesyEnergySensor without a full HA stack.
class _TesyEntity(_CoordinatorEntity):
    def __init__(self, hass, coordinator, entry, description):
        super().__init__(coordinator)
        self.hass = hass
        self._entry = entry
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.data.get('MAC', 'test')}-{description.key}"
        )


# ---------------------------------------------------------------------------
# Build mock modules
# ---------------------------------------------------------------------------

_sensor_mod = MagicMock()
_sensor_mod.SensorEntity = _SensorEntity
_sensor_mod.RestoreSensor = _RestoreSensor
_sensor_mod.SensorDeviceClass = MagicMock()
_sensor_mod.SensorStateClass = MagicMock()
_sensor_mod.SensorEntityDescription = MagicMock

_core_mod = MagicMock()
_core_mod.HomeAssistant = MagicMock
_core_mod.callback = _callback

# Submodule stubs so the tesy package __init__.py doesn't drag in
# coordinator → tesy.py → requests and other third-party deps.
_entity_submod = MagicMock()
_entity_submod.TesyEntity = _TesyEntity

_coordinator_submod = MagicMock()
_coordinator_submod.TesyCoordinator = MagicMock

sys.modules.update(
    {
        "requests": MagicMock(),
        "homeassistant": MagicMock(),
        "homeassistant.components": MagicMock(),
        "homeassistant.components.sensor": _sensor_mod,
        "homeassistant.config_entries": MagicMock(),
        "homeassistant.const": MagicMock(),
        "homeassistant.core": _core_mod,
        "homeassistant.exceptions": MagicMock(),
        "homeassistant.helpers": MagicMock(),
        "homeassistant.helpers.entity_platform": MagicMock(),
        "homeassistant.helpers.device_registry": MagicMock(),
        "homeassistant.helpers.entity": MagicMock(),
        "homeassistant.helpers.update_coordinator": MagicMock(),
        # Pre-populate tesy sub-packages so their real files never load
        "custom_components.tesy.entity": _entity_submod,
        "custom_components.tesy.coordinator": _coordinator_submod,
    }
)

# Make the repo root importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
