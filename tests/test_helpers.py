"""Tests for the Tesy helpers."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType
from unittest import TestCase


def load_helpers_module():
    """Load the helpers module without requiring a Home Assistant installation."""
    module_names = (
        "custom_components",
        "custom_components.tesy",
        "custom_components.tesy.const",
    )
    previous_modules = {name: sys.modules.get(name) for name in module_names}

    package = ModuleType("custom_components")
    package.__path__ = []
    integration_package = ModuleType("custom_components.tesy")
    integration_package.__path__ = []
    constants = ModuleType("custom_components.tesy.const")

    values = {
        "ATTR_MAX_SHOWERS": "tmpMX",
        "TESY_MODE_P1": "p1",
        "TESY_MODE_P2": "p2",
        "TESY_MODE_P3": "p3",
        "TESY_MODE_EC2": "ec2",
        "TESY_MODE_EC3": "ec3",
    }
    for name, value in values.items():
        setattr(constants, name, value)

    try:
        sys.modules["custom_components"] = package
        sys.modules["custom_components.tesy"] = integration_package
        sys.modules["custom_components.tesy.const"] = constants

        module_path = (
            Path(__file__).parents[1] / "custom_components" / "tesy" / "helpers.py"
        )
        spec = spec_from_file_location(
            "custom_components.tesy.helpers",
            module_path,
        )
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for name, previous_module in previous_modules.items():
            if previous_module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous_module


HELPERS = load_helpers_module()


class ToFloatTest(TestCase):
    """Test conversion of reported temperatures."""

    def test_converts_numeric_values(self):
        """Convert numeric strings and numbers."""
        self.assertEqual(HELPERS.to_float("55"), 55.0)
        self.assertEqual(HELPERS.to_float("71.5"), 71.5)
        self.assertEqual(HELPERS.to_float(3), 3.0)

    def test_returns_none_for_missing_or_non_numeric(self):
        """Return None instead of raising."""
        self.assertIsNone(HELPERS.to_float(None))
        self.assertIsNone(HELPERS.to_float(""))
        self.assertIsNone(HELPERS.to_float("n/a"))
        self.assertIsNone(HELPERS.to_float({}))


class MaxShowersTest(TestCase):
    """Test the maximum showers fallback."""

    def test_uses_reported_maximum(self):
        """Use tmpMX when the device reports it."""
        self.assertEqual(HELPERS.max_showers({"tmpMX": "3"}, 4), 3)
        self.assertEqual(HELPERS.max_showers({"tmpMX": 5}, 4), 5)

    def test_falls_back_when_missing(self):
        """Fall back to the default when tmpMX is missing (old API)."""
        self.assertEqual(HELPERS.max_showers({}, 4), 4)

    def test_falls_back_when_invalid(self):
        """Fall back to the default when tmpMX is not a whole number."""
        self.assertEqual(HELPERS.max_showers({"tmpMX": ""}, 4), 4)
        self.assertEqual(HELPERS.max_showers({"tmpMX": "x"}, 4), 4)
        self.assertEqual(HELPERS.max_showers({"tmpMX": None}, 4), 4)
        self.assertEqual(HELPERS.max_showers({"tmpMX": "-1"}, 4), 4)


# Values sent before the mode map was introduced
EXPECTED_MODES = {
    "performance": "0",
    "p1": "1",
    "p2": "2",
    "p3": "3",
    "eco": "4",
    "ec2": "5",
    "ec3": "6",
}


class ModeMapTest(TestCase):
    """Test the operation mode map."""

    def test_operation_to_tesy_mode(self):
        """Map every known operation mode to the same value as before."""
        self.assertEqual(HELPERS.OPERATION_TO_TESY_MODE, EXPECTED_MODES)
        for operation, mode in EXPECTED_MODES.items():
            self.assertEqual(HELPERS.tesy_mode(operation), mode)

    def test_tesy_mode_to_operation(self):
        """Map every Tesy mode back to its operation mode."""
        for operation, mode in EXPECTED_MODES.items():
            self.assertEqual(HELPERS.TESY_MODE_TO_OPERATION[mode], operation)
        self.assertEqual(len(HELPERS.TESY_MODE_TO_OPERATION), len(EXPECTED_MODES))

    def test_rejects_unknown_operation_mode(self):
        """Raise ValueError for modes that are not in the map."""
        for operation in ("off", "heat_pump", "", None):
            with self.assertRaises(ValueError):
                HELPERS.tesy_mode(operation)

    def test_unknown_tesy_mode_is_not_mapped(self):
        """Leave unknown Tesy modes unmapped so the caller can fall back."""
        self.assertIsNone(HELPERS.TESY_MODE_TO_OPERATION.get("7"))

    def test_state_values_match_home_assistant(self):
        """Keep the local state values in line with Home Assistant."""
        try:
            from homeassistant.components import water_heater
        except ImportError:
            self.skipTest("Home Assistant is not installed")
        self.assertEqual(HELPERS.STATE_PERFORMANCE, water_heater.STATE_PERFORMANCE)
        self.assertEqual(HELPERS.STATE_ECO, water_heater.STATE_ECO)
