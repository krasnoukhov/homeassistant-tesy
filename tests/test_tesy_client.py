"""Tests for the Tesy local API client (no Home Assistant needed)."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType
from unittest import TestCase
from unittest.mock import patch

import requests


def load_client_module():
    """Load tesy.py with a stub const module instead of Home Assistant."""
    names = (
        "custom_components",
        "custom_components.tesy",
        "custom_components.tesy.const",
    )
    previous = {name: sys.modules.get(name) for name in names}
    package = ModuleType("custom_components")
    package.__path__ = []
    integration = ModuleType("custom_components.tesy")
    integration.__path__ = []
    const = ModuleType("custom_components.tesy.const")
    for name, value in {
        "ATTR_POWER": "pwr",
        "ATTR_TARGET_TEMP": "tmpT",
        "ATTR_BOOST": "bst",
        "ATTR_MODE": "mode",
        "ATTR_CHILD_LOCK": "lck",
        "ATTR_API": "api",
        "ATTR_ENERGY_RESETTABLE": "pwc_u",
        "HTTP_TIMEOUT": 15,
        "IP_ADDRESS": "ip_address",
        "HEATER_POWER": "heater_power",
    }.items():
        setattr(const, name, value)
    try:
        sys.modules.update(
            {
                "custom_components": package,
                "custom_components.tesy": integration,
                "custom_components.tesy.const": const,
            }
        )
        path = Path(__file__).parents[1] / "custom_components" / "tesy" / "tesy.py"
        spec = spec_from_file_location("custom_components.tesy.tesy", path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for name, module in previous.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


TESY = load_client_module()


class RequestErrorsTest(TestCase):
    """Every requests failure reaches callers as ConnectionError."""

    def test_request_failures_become_connection_error(self):
        client = TESY.Tesy({"ip_address": "192.0.2.1"})
        for error in (
            requests.exceptions.ReadTimeout("slow"),
            requests.exceptions.ConnectTimeout("no route"),
            requests.exceptions.ConnectionError("refused"),
            requests.exceptions.TooManyRedirects("loop"),
            TimeoutError("timeout"),
        ):
            with self.subTest(error=type(error).__name__):
                with patch.object(TESY.requests, "get", side_effect=error):
                    with self.assertRaises(ConnectionError):
                        client.set_timezone("EET-2EEST,M3.5.0/3,M10.5.0/4")
