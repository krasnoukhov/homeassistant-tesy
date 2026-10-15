"""Tests for request error handling in the Tesy API clients."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType
from unittest import TestCase
from unittest.mock import Mock, patch

import requests

INTEGRATION_PATH = Path(__file__).parents[1] / "custom_components" / "tesy"


def load_client_modules():
    """Load both API clients without requiring a Home Assistant installation."""
    module_names = (
        "homeassistant",
        "homeassistant.const",
        "custom_components",
        "custom_components.tesy",
        "custom_components.tesy.const",
        "custom_components.tesy.tesy",
        "custom_components.tesy.tesy_oldapi",
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

    def load(name):
        spec = spec_from_file_location(
            f"custom_components.tesy.{name}", INTEGRATION_PATH / f"{name}.py"
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
        load("const")
        return load("tesy"), load("tesy_oldapi")
    finally:
        for name, previous_module in previous_modules.items():
            if previous_module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous_module


TESY, OLD_API = load_client_modules()


def response(payload):
    """Create a mocked requests response."""
    result = Mock()
    result.json.return_value = payload
    return result


class RequestErrorTest(TestCase):
    """Test that request failures surface as ConnectionError."""

    def setUp(self):
        """Create both clients."""
        self.client = TESY.Tesy({"ip_address": "192.0.2.1"})
        self.old_client = OLD_API.TesyOldApi({"ip_address": "192.0.2.1"})

    def test_read_timeout_raises_connection_error(self):
        """Map ReadTimeout to ConnectionError for polling and setters."""
        with patch("requests.get", side_effect=requests.exceptions.ReadTimeout()):
            with self.assertRaises(ConnectionError):
                self.client.get_data()
            with self.assertRaises(ConnectionError):
                self.client.set_power("1")

    def test_old_api_read_timeout_raises_connection_error(self):
        """Map ReadTimeout to ConnectionError for polling and setters."""
        with patch("requests.get", side_effect=requests.exceptions.ReadTimeout()):
            with self.assertRaises(ConnectionError):
                self.old_client.get_data()
            with self.assertRaises(ConnectionError):
                self.old_client.set_power("1")

    def test_http_error_raises_connection_error(self):
        """Map HTTP error statuses to ConnectionError."""
        error = requests.Response()
        error.status_code = 500
        for client in (self.client, self.old_client):
            with patch("requests.get", return_value=error):
                with self.assertRaises(ConnectionError):
                    client.get_data()

    def test_old_api_keeps_data_when_energy_counter_times_out(self):
        """Keep core device data when only calcRes times out."""
        status = {"mode": "1", "power_sw": "on", "lockB": "off"}
        devstat = {"devid": "2000-34008a311bf0 FW22.4M", "macaddr": "00:11:22"}
        with patch(
            "requests.get",
            side_effect=[
                response(status),
                response(devstat),
                requests.exceptions.ReadTimeout(),
            ],
        ):
            result = self.old_client.get_data()

        self.assertEqual(result["api"], "OK")
        self.assertEqual(result["pwr"], "1")
        self.assertNotIn("pwc_u", result)
