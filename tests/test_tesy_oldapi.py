"""Tests for the Tesy old API client."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
import time
from types import ModuleType
from unittest import TestCase
from unittest.mock import Mock


def load_old_api_module():
    """Load the old API module without requiring a Home Assistant installation."""
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
        "IP_ADDRESS": "ip_address",
        "HEATER_POWER": "heater_power",
        "HTTP_TIMEOUT": 15,
        "ATTR_API": "api",
        "ATTR_SOFTWARE": "wsw",
        "ATTR_MAC": "MAC",
        "ATTR_DEVICE_ID": "id",
        "ATTR_MODE": "mode",
        "ATTR_CURRENT_TEMP": "tmpC",
        "ATTR_TARGET_TEMP": "tmpT",
        "ATTR_CURRENT_TARGET_TEMP": "tmpT",
        "ATTR_BOOST": "bst",
        "ATTR_POWER": "pwr",
        "ATTR_CHILD_LOCK": "lck",
        "ATTR_IS_HEATING": "ht",
        "ATTR_ERROR": "err",
        "ATTR_ENERGY_RESETTABLE": "pwc_u",
    }
    for name, value in values.items():
        setattr(constants, name, value)

    try:
        sys.modules["custom_components"] = package
        sys.modules["custom_components.tesy"] = integration_package
        sys.modules["custom_components.tesy.const"] = constants

        module_path = (
            Path(__file__).parents[1] / "custom_components" / "tesy" / "tesy_oldapi.py"
        )
        spec = spec_from_file_location(
            "custom_components.tesy.tesy_oldapi",
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


OLD_API = load_old_api_module()


def response(payload):
    """Create a mocked requests response."""
    result = Mock()
    result.json.return_value = payload
    return result


class TesyOldApiTest(TestCase):
    """Test old API data conversion."""

    def setUp(self):
        """Create a client and common device responses."""
        self.client = OLD_API.TesyOldApi({"ip_address": "192.0.2.1", "heater_power": 0})
        self.status = {
            "heater_state": "HEATING",
            "mode": "1",
            "boost": "0",
            "power_sw": "on",
            "lockB": "off",
            "gradus": "71.0",
            "ref_gradus": "55",
            "watts": "2400",
        }
        self.devstat = {
            "devid": "2000-34008a311bf0 FW22.4M",
            "macaddr": "00:11:22:33:44:55",
        }

    def test_maps_energy_counter_power_and_heating_state(self):
        """Map calcRes and status fields to the common API representation."""
        self.client._get_request = Mock(
            side_effect=[
                response(self.status),
                response(self.devstat),
                response(
                    {
                        "sum": "8211003",
                        "resetDate": "2024-09-15 04:04:19",
                        "volume": "150",
                        "watt": "2400",
                    }
                ),
            ]
        )

        data = self.client.get_data()

        self.assertEqual(data["pwc_u"], {"utc": "8211003"})
        self.assertEqual(data["ht"], "1")
        self.assertEqual(self.client._heater_power, 2400)

    def test_keeps_device_available_without_energy_endpoint(self):
        """Keep core device data available when calcRes is unsupported."""
        self.status["heater_state"] = "READY"
        self.client._get_request = Mock(
            side_effect=[
                response(self.status),
                response(self.devstat),
                ConnectionError(),
            ]
        )

        data = self.client.get_data()

        self.assertNotIn("pwc_u", data)
        self.assertEqual(data["ht"], "0")
        self.assertEqual(data["tmpC"], "71.0")
        self.assertEqual(self.client._heater_power, 2400)

    def test_ignores_invalid_energy_response(self):
        """Keep core device data available when calcRes returns invalid JSON."""
        invalid_response = Mock()
        invalid_response.json.side_effect = ValueError()
        self.client._get_request = Mock(
            side_effect=[
                response(self.status),
                response(self.devstat),
                invalid_response,
            ]
        )

        data = self.client.get_data()

        self.assertNotIn("pwc_u", data)
        self.assertEqual(data["ht"], "1")

    def test_calcres_cached_within_10_minutes(self):
        """Second get_data() within 10 min should skip the calcRes HTTP call."""
        self.client._get_request = Mock(
            side_effect=[
                response(self.status),
                response(self.devstat),
                response({"sum": "12345", "watt": "2400"}),
                response(self.status),
                response(self.devstat),
            ]
        )

        data1 = self.client.get_data()
        self.assertEqual(self.client._get_request.call_count, 3)
        self.assertEqual(data1["pwc_u"], {"utc": "12345"})

        data2 = self.client.get_data()
        self.assertEqual(self.client._get_request.call_count, 5)
        self.assertEqual(data2["pwc_u"], {"utc": "12345"})

    def test_calcres_refetched_after_10_minutes(self):
        """Cache expires after 10 minutes, triggering a fresh calcRes fetch."""
        self.client._get_request = Mock(
            side_effect=[
                response(self.status),
                response(self.devstat),
                response({"sum": "12345", "watt": "2400"}),
                response(self.status),
                response(self.devstat),
                response({"sum": "12400", "watt": "2400"}),
            ]
        )

        self.client.get_data()
        self.assertEqual(self.client._get_request.call_count, 3)

        self.client._calc_res_fetched_at = time.time() - 601

        data2 = self.client.get_data()
        self.assertEqual(self.client._get_request.call_count, 6)
        self.assertEqual(data2["pwc_u"], {"utc": "12400"})

    def test_setter_returns_ok_without_refetch(self):
        """Setter should return OK with a single HTTP call, not four."""
        self.client._get_request = Mock(return_value=response({"stat": "ok"}))

        result = self.client.set_target_temperature(55)

        self.assertEqual(result, {"api": "OK"})
        self.client._get_request.assert_called_once()

    def test_reset_energy_counter_ok(self):
        """Reset the energy counter when the device confirms it."""
        self.client._get_request = Mock(return_value=response({"err": "0"}))

        result = self.client.reset_energy_counter()

        self.client._get_request.assert_called_with(cmd="resetPow")
        self.assertEqual(result["api"], "OK")

    def test_reset_energy_counter_error(self):
        """Report failure when the device rejects the reset."""
        self.client._get_request = Mock(return_value=response({"err": "1"}))

        result = self.client.reset_energy_counter()

        self.assertEqual(result["api"], "ERROR")
