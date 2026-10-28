"""Tests for the fields left out of the diagnostics download (no Home Assistant needed)."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType
from unittest import TestCase


def load_const_module():
    """Load const.py with a stub homeassistant.const."""
    names = ("homeassistant", "homeassistant.const")
    previous = {name: sys.modules.get(name) for name in names}
    homeassistant = ModuleType("homeassistant")
    homeassistant.__path__ = []
    ha_const = ModuleType("homeassistant.const")
    ha_const.CONF_IP_ADDRESS = "ip_address"
    try:
        sys.modules.update(
            {"homeassistant": homeassistant, "homeassistant.const": ha_const}
        )
        path = Path(__file__).parents[1] / "custom_components" / "tesy" / "const.py"
        spec = spec_from_file_location("tesy_const", path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for name, module in previous.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


CONST = load_const_module()

# Fields of real _all replies (BelliSlimo 2002 and ModEco 2 2004) that identify
# the user, their network or the device.
PERSONAL = {"MAC", "wIP", "prfl", "wSSID", "extr"}
# Fields needed to debug a heater; they must stay in the download.
TECHNICAL = {
    "id",
    "wsw",
    "hsw",
    "tz",
    "date",
    "wtstp",
    "mode",
    "pwr",
    "bst",
    "ht",
    "tmpC",
    "tmpT",
    "tmpR",
    "tmpMX",
    "err",
    "lck",
    "cdt",
    "vac",
    "prgVac",
    "parNF",
    "pwcalc",
    "pwc_t",
    "pwc_u",
    "wup",
    "wdBm",
    "prgP1MO",
}


class RedactionTest(TestCase):
    def test_personal_fields_are_redacted(self):
        self.assertLessEqual(PERSONAL, CONST.TO_REDACT)

    def test_configured_ip_address_is_redacted(self):
        self.assertIn("ip_address", CONST.TO_REDACT)

    def test_technical_fields_are_kept(self):
        self.assertFalse(TECHNICAL & CONST.TO_REDACT)
