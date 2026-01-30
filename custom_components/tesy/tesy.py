"""Tesy integration."""

from __future__ import annotations

import logging
from typing import Any

from urllib.parse import urlparse, urlencode
import requests

from .const import (
    ATTR_POWER,
    ATTR_TARGET_TEMP,
    ATTR_BOOST,
    ATTR_MODE,
    HTTP_TIMEOUT,
    IP_ADDRESS,
    HEATER_POWER,
)

_LOGGER = logging.getLogger(__name__)


class Tesy:
    """Tesy instance."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Init Tesy."""
        self._ip_address = data[IP_ADDRESS]

        self._heater_power = 2400
        if HEATER_POWER in data:
            self._heater_power = data[HEATER_POWER]

    def get_data(self) -> dict[str, Any]:
        """Get data for Tesy component."""
        return self._get_request(name="_all").json()

    def set_target_temperature(self, val: int) -> bool:
        """Set target temperature for Tesy component."""
        return self._get_request(name=ATTR_TARGET_TEMP, set=val).json()

    def set_power(self, val: str) -> bool:
        """Set power for Tesy component."""
        return self._get_request(name=ATTR_POWER, set=val).json()

    def set_boost(self, val: str) -> bool:
        """Set boost for Tesy component."""
        return self._get_request(name=ATTR_BOOST, set=val).json()

    def set_operation_mode(self, val: str) -> bool:
        """Set boost for Tesy component."""
        return self._get_request(name=ATTR_MODE, set=val).json()

    def _get_request(self, **kwargs) -> requests.Response:
        """Make GET request to the Tesy API."""
        url = urlparse(f"http://{self._ip_address}/api")
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
