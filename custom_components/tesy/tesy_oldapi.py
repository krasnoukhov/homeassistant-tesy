"""Tesy integration."""

from __future__ import annotations

import logging
from typing import Any

from urllib.parse import urlparse, urlencode
import requests

from .const import *

_LOGGER = logging.getLogger(__name__)


class TesyOldApi:
    """Tesy Old API instance."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Init Tesy."""
        self._ip_address = data[IP_ADDRESS]

        self._heater_power = 2400
        if HEATER_POWER in data:
            self._heater_power = data[HEATER_POWER]

    def get_data(self) -> dict[str, Any]:
        """Get data for Tesy component."""

        return self.convertApi(
            {
                "status": self._get_request(cmd="status").json(),
                "devstat": self._get_request(cmd="devstat").json(),
            }
        )

    def convertApi(self, data: dict[str, Any]) -> dict[str, Any]:
        onoff = {"on": "1", "off": "0"}
        status = data["status"]
        mode = self._coerce_mode(status.get("mode"))

        o = dict()
        o.update(
            {
                ATTR_API: "OK",
                ATTR_SOFTWARE: data["devstat"]["devid"],
                ATTR_MAC: data["devstat"]["macaddr"],
                ATTR_DEVICE_ID: data["devstat"]["devid"].split("-")[0],
                ATTR_MODE: mode,
                ATTR_CURRENT_TEMP: status["gradus"],
                ATTR_TARGET_TEMP: status["ref_gradus"],
                ATTR_BOOST: str(status.get("boost", "0")),
                ATTR_POWER: onoff[status["power_sw"]],
            }
        )


        _LOGGER.debug(f"converted API: {str(o)}")
        return o

    def set_target_temperature(self, val: int) -> bool:
        """Set target temperature for Tesy component."""
        return self._get_request("setTemp", val=val).json()

    def set_power(self, val: str) -> bool:
        """Set power for Tesy component."""
        if val == "0":
            _val = "off"
        elif val == "1":
            _val = "on"
        else:
            raise ValueError
        return self._get_request("power", val=_val).json()

    def set_boost(self, val: str) -> bool:
        """Set boost for Tesy component."""
        return self._get_request("boostSW", mode=val).json()

    def set_operation_mode(self, val: str) -> bool:
        """Set mode for Tesy component."""
        return self._get_request("modeSW", mode=int(val) + 1).json()
    def _coerce_mode(self, mode: Any) -> str:
        """Convert mode reported by the old API into the numeric string the integration expects."""
        if mode is None:
            return "0"

        try:
            return str(int(mode) - 1)
        except (TypeError, ValueError):
            pass

        if isinstance(mode, str):
            key = mode.strip().lower().replace("_", "").replace(" ", "")
            mapping = {
                "manual": "0",
                "p1": "1",
                "auto": "1",
                "p2": "2",
                "p3": "3",
                "eco": "4",
                "ec2": "5",
                "ec3": "6",
                "ecoconfort": "5",
                "ecocomfort": "5",
                "econight": "6",
            }
            if key in mapping:
                return mapping[key]

        _LOGGER.warning("Unknown mode value from old API: %r", mode)
        return "0"

    def _get_request(self, cmd, **kwargs) -> requests.Response:
        """Make GET request to the Tesy API."""
        url = urlparse(f"http://{self._ip_address}/{cmd}")
        url = url._replace(query=urlencode(kwargs))

        _LOGGER.debug(f"Tesy request: GET {url.geturl()}")
        try:
            r = requests.get(url.geturl(), timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            _LOGGER.debug(f"Tesy status: {r.status_code}")
            _LOGGER.debug(f"Tesy response: {r.text}")

            return r
        except TimeoutError as timeout_error:
            raise ConnectionError from timeout_error
        except requests.exceptions.ConnectionError as connection_error:
            raise ConnectionError from connection_error
        except requests.exceptions.HTTPError as http_error:
            raise ConnectionError from http_error
