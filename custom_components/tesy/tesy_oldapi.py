"""Tesy integration."""

from __future__ import annotations

import logging
import time
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

        # ponytail: cache calcRes separately — energy counter changes slowly, and
        # the Atheros chip chokes when polled for all 3 endpoints every 30 s.
        self._calc_res_cache = None
        self._calc_res_fetched_at = 0.0

    def get_data(self) -> dict[str, Any]:
        """Get data for Tesy component."""

        data = {
            "status": self._get_request(cmd="status").json(),
            "devstat": self._get_request(cmd="devstat").json(),
        }

        # Cache calcRes — energy counter changes slowly (~10 min granularity is
        # fine).  The Atheros web-server drops requests when hammered with 3
        # rapid-fire HTTP calls every 30 s; skipping this one cuts normal poll
        # traffic by a third and setter bursts by two-thirds.
        now = time.time()
        if self._calc_res_cache is not None and (now - self._calc_res_fetched_at) < 600:
            data["calcRes"] = self._calc_res_cache
        else:
            try:
                calc_res = self._get_request(cmd="calcRes").json()
                data["calcRes"] = calc_res
                self._calc_res_cache = calc_res
                self._calc_res_fetched_at = now
            except (ConnectionError, ValueError):
                _LOGGER.debug("Energy counter is not available from the old API")

        return self._convert_api(data)

    def _convert_api(self, data: dict[str, Any]) -> dict[str, Any]:
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
                ATTR_ERROR: status.get("err_flag", "0"),
                ATTR_CURRENT_TEMP: status.get("gradus", "0"),
                ATTR_TARGET_TEMP: status.get("ref_gradus", "0"),
                ATTR_CURRENT_TARGET_TEMP: status.get("ref_gradus", "0"),
                ATTR_BOOST: str(status.get("boost", "0")),
                ATTR_POWER: onoff.get(status["power_sw"], "0"),
                ATTR_CHILD_LOCK: onoff.get(status["lockB"], "0"),
                ATTR_IS_HEATING: (
                    "1"
                    if str(status.get("heater_state", "")).upper() == "HEATING"
                    else "0"
                ),
            }
        )

        calc_result = data.get("calcRes", {})
        energy_counter = calc_result.get("sum")
        try:
            if int(energy_counter) >= 0:
                o[ATTR_ENERGY_RESETTABLE] = dict(utc=str(energy_counter))
        except (TypeError, ValueError):
            _LOGGER.debug("Invalid old API energy counter: %r", energy_counter)

        reported_power = calc_result.get("watt", status.get("watts"))
        try:
            reported_power = int(reported_power)
            if reported_power > 0:
                self._heater_power = reported_power
        except (TypeError, ValueError):
            _LOGGER.debug("Invalid old API heater power: %r", reported_power)

        _LOGGER.debug(f"converted API: {str(o)}")
        return o

    def _convert_setter_api(self, ack: dict[str, Any]) -> dict[str, Any]:
        """Old API setters only ack the request; no refetch needed."""
        if ack.get("stat") != "ok":
            return {ATTR_API: "ERROR"}
        return {ATTR_API: "OK"}

    def set_target_temperature(self, val: int) -> dict[str, Any]:
        """Set target temperature for Tesy component."""
        return self._convert_setter_api(self._get_request("setTemp", val=val).json())

    def set_power(self, val: str) -> dict[str, Any]:
        """Set power for Tesy component."""
        if val == "0":
            _val = "off"
        elif val == "1":
            _val = "on"
        else:
            raise ValueError
        return self._convert_setter_api(self._get_request("power", val=_val).json())

    def set_boost(self, val: str) -> dict[str, Any]:
        """Set boost for Tesy component."""
        return self._convert_setter_api(self._get_request("boostSW", mode=val).json())

    def set_operation_mode(self, val: str) -> dict[str, Any]:
        """Set mode for Tesy component."""
        return self._convert_setter_api(
            self._get_request("modeSW", mode=int(val) + 1).json()
        )

    def set_child_lock(self, val: str) -> dict[str, Any]:
        """Set child lock for Tesy component. Not supported on old API."""
        _LOGGER.warning("set_child_lock is not supported on the old API")
        return {ATTR_API: "OK"}

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
