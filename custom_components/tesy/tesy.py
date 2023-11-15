"""Tesy integration."""
from __future__ import annotations

import logging
from typing import Any

from urllib.parse import urlparse, urlencode
import requests

from .const import (
    ATTR_POWER,
    ATTR_TARGET_TEMP,
    HTTP_TIMEOUT,
    IP_ADDRESS,
)


_LOGGER = logging.getLogger(__name__)


class Tesy:
    """Tesy instance."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Init Tesy."""
        self._ip_address = data[IP_ADDRESS]

    def get_data(self) -> dict[str, Any]:
        """Get data for Tesy component."""
        return self._get_request(name="_all").json()

    def set_target_temperature(self, val: int) -> bool:
        """Set target temperature for Tesy component."""
        self._get_request(name=ATTR_TARGET_TEMP, set=val).json()
        return True

    def set_power(self, val: str) -> bool:
        """Set power for Tesy component."""
        self._get_request(name=ATTR_POWER, set=val).json()
        return True

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
