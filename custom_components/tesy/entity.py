"""Base entity for the Tesy integration."""
from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import TesyCoordinator


class TesyEntity(CoordinatorEntity[TesyCoordinator]):
    """Defines a base Tesy entity."""

    _attr_has_entity_name = True
