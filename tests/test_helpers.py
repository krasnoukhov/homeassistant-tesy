"""Tests for the Tesy helpers."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType
from unittest import TestCase


def load_helpers_module():
    """Load the helpers module without requiring a Home Assistant installation."""
    module_names = (
        "homeassistant",
        "homeassistant.const",
        "custom_components",
        "custom_components.tesy",
        "custom_components.tesy.const",
        "custom_components.tesy.helpers",
    )
    previous_modules = {name: sys.modules.get(name) for name in module_names}

    homeassistant = ModuleType("homeassistant")
    homeassistant.__path__ = []
    homeassistant_const = ModuleType("homeassistant.const")
    homeassistant_const.CONF_IP_ADDRESS = "ip_address"
    package = ModuleType("custom_components")
    package.__path__ = []
    integration_package = ModuleType("custom_components.tesy")
    integration_package.__path__ = []
    integration_path = Path(__file__).parents[1] / "custom_components" / "tesy"

    def load(name):
        spec = spec_from_file_location(
            f"custom_components.tesy.{name}", integration_path / f"{name}.py"
        )
        module = module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    try:
        sys.modules["homeassistant"] = homeassistant
        sys.modules["homeassistant.const"] = homeassistant_const
        sys.modules["custom_components"] = package
        sys.modules["custom_components.tesy"] = integration_package
        # The real constants, so the shower flags of each model are tested
        load("const")
        return load("helpers")
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

    def test_falls_back_when_zero(self):
        """Fall back to the default when tmpMX is zero (Eco would target 0)."""
        self.assertEqual(HELPERS.max_showers({"tmpMX": "0"}, 4), 4)
        self.assertEqual(HELPERS.max_showers({"tmpMX": 0}, 4), 4)


class UsesShowersTest(TestCase):
    """Test which devices report hot water in showers."""

    def test_shower_models_on_new_api(self):
        """BelliSlimo and BelliSlimo Lite report showers."""
        self.assertTrue(HELPERS.uses_showers("2002", old_api=False))
        self.assertTrue(HELPERS.uses_showers("2005", old_api=False))

    def test_shower_models_on_old_api(self):
        """Old API shower devices keep the temperature entities for now."""
        self.assertFalse(HELPERS.uses_showers("2002", old_api=True))
        self.assertFalse(HELPERS.uses_showers("2005", old_api=True))

    def test_other_models(self):
        """Temperature models and unknown ids do not use showers."""
        for device_id in ("2000", "2003", "2004", "9999", "", None):
            self.assertFalse(HELPERS.uses_showers(device_id, old_api=False))


class IsHeatingTest(TestCase):
    """Test the heating state."""

    def test_heating_and_idle(self):
        """ht 1 is heating, 0 is not."""
        self.assertTrue(HELPERS.is_heating({"ht": "1", "pwr": "1"}))
        self.assertFalse(HELPERS.is_heating({"ht": "0", "pwr": "1"}))

    def test_switched_off_is_not_heating(self):
        """A heater that is off is not heating, whatever ht says."""
        self.assertFalse(HELPERS.is_heating({"ht": "1", "pwr": "0"}))

    def test_without_power_field(self):
        """ht alone decides when pwr is missing."""
        self.assertTrue(HELPERS.is_heating({"ht": "1"}))
        self.assertFalse(HELPERS.is_heating({"ht": "0"}))

    def test_unknown(self):
        """A missing or unexpected ht value is unknown."""
        for data in ({}, {"ht": ""}, {"ht": "2"}, {"ht": None}, {"ht": "yes"}):
            self.assertIsNone(HELPERS.is_heating(data), data)


class HasErrorTest(TestCase):
    """Test the error state, which follows the MyTESY app."""

    def test_no_error(self):
        """00 (new API) and 0 (old API) mean no error."""
        for value in ("00", "0", 0, " 00 "):
            self.assertFalse(HELPERS.has_error({"err": value}), value)

    def test_error(self):
        """Any other code is an error, without decoding it."""
        for value in ("01", "05", "6", "10", "0A", "11", "000", 3):
            self.assertTrue(HELPERS.has_error({"err": value}), value)

    def test_unknown(self):
        """A missing or empty code is unknown, not an error."""
        for data in ({}, {"err": ""}, {"err": None}, {"err": "  "}):
            self.assertIsNone(HELPERS.has_error(data), data)


class ReadyInTest(TestCase):
    """Test the Ready In countdown."""

    def test_counts_down_while_heating(self):
        """While heating, cdt is shown as reported."""
        self.assertEqual(HELPERS.ready_in({"cdt": "81", "ht": "1", "pwr": "1"}), 81)

    def test_idle_is_ready_now(self):
        """The idle leftover in cdt is not shown: the water is ready."""
        for cdt in ("0", "1", "2"):
            self.assertEqual(HELPERS.ready_in({"cdt": cdt, "ht": "0", "pwr": "1"}), 0)

    def test_without_ht(self):
        """ht isn't required: without it cdt is shown as reported."""
        self.assertEqual(HELPERS.ready_in({"cdt": "2"}), 2)
        self.assertEqual(HELPERS.ready_in({"cdt": "2", "ht": ""}), 2)

    def test_switched_off_is_unknown(self):
        """A heater that is off isn't heating towards anything."""
        self.assertIsNone(HELPERS.ready_in({"cdt": "5", "ht": "0", "pwr": "0"}))

    def test_invalid_is_unknown(self):
        """A missing or non-numeric cdt is unknown."""
        for data in ({}, {"cdt": ""}, {"cdt": None}, {"cdt": "-1"}, {"cdt": "x"}):
            self.assertIsNone(HELPERS.ready_in(data), data)


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
