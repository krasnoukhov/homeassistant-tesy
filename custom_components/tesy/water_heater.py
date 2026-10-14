"""Tesy water heater component."""

from typing import Any
from custom_components.tesy.coordinator import TesyCoordinator

import voluptuous as vol

from homeassistant.components.water_heater import (
    STATE_ECO,
    STATE_PERFORMANCE,
    WaterHeaterEntity,
    WaterHeaterEntityDescription,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
    STATE_OFF,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    TESY_DEVICE_TYPES,
    ATTR_CURRENT_TEMP,
    ATTR_CURRENT_TARGET_TEMP,
    ATTR_DEVICE_ID,
    ATTR_IS_HEATING,
    ATTR_MODE,
    ATTR_POWER,
    ATTR_TARGET_TEMP,
    DOMAIN,
    TESY_MODE_P1,
    TESY_MODE_P2,
    TESY_MODE_P3,
    TESY_MODE_EC2,
    TESY_MODE_EC3,
)

from .entity import TesyEntity
from .helpers import TESY_MODE_TO_OPERATION, max_showers, tesy_mode, to_float
from .schedule import (
    DAYS,
    HOURS_PER_DAY,
    MAX_SLOT_TEMP,
    MIN_SLOT_TEMP,
    PROGRAMS,
    active_program,
    ALL_DAYS,
    active_target,
    days_or_all,
    encode_day,
    get_program,
    schedule_key,
    whole_number,
    write_failure_message,
)

SERVICE_SET_SCHEDULE = "set_schedule"
ATTR_PROGRAM = "program"
ATTR_DAYS = "days"
ATTR_TEMPERATURES = "temperatures"


def _whole_number(value: Any) -> int:
    """Voluptuous validator: a whole number, fractions rejected."""
    try:
        return whole_number(value)
    except (TypeError, ValueError) as err:
        raise vol.Invalid(str(err)) from err


SET_SCHEDULE_SCHEMA = {
    vol.Required(ATTR_PROGRAM): vol.All(_whole_number, vol.In(PROGRAMS)),
    vol.Optional(ATTR_DAYS, default=list(ALL_DAYS)): vol.All(
        cv.ensure_list,
        vol.Length(max=len(DAYS)),
        [vol.All(cv.string, vol.Lower, vol.In(ALL_DAYS))],
        days_or_all,
    ),
    vol.Required(ATTR_TEMPERATURES): vol.All(
        cv.ensure_list,
        vol.Length(min=HOURS_PER_DAY, max=HOURS_PER_DAY),
        [
            vol.Any(
                None,
                vol.All(
                    _whole_number,
                    vol.Range(min=MIN_SLOT_TEMP, max=MAX_SLOT_TEMP),
                ),
            )
        ],
    ),
}

OPERATION_LIST = [
    STATE_OFF,
    STATE_PERFORMANCE,
    TESY_MODE_P1,
    TESY_MODE_P2,
    TESY_MODE_P3,
    STATE_ECO,
    TESY_MODE_EC2,
    TESY_MODE_EC3,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create Tesy water heater in HASS."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Registered for every heater, so the action exists even if the first poll
    # lacked the program fields; async_set_schedule rejects unsupported ones.
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_SCHEDULE,
        SET_SCHEDULE_SCHEMA,
        "async_set_schedule",
    )

    async_add_entities(
        [
            TesyWaterHeater(
                hass,
                coordinator,
                entry,
                WaterHeaterEntityDescription(
                    key="water_heater",
                    translation_key="heater",
                ),
            )
        ]
    )


class TesyWaterHeater(TesyEntity, WaterHeaterEntity):
    """Representation of an Tesy water heater."""

    _attr_operation_list = OPERATION_LIST
    # Weekly programs are a few KB and change rarely; keep them out of history.
    _unrecorded_attributes = frozenset(
        {f"schedule_p{program}" for program in PROGRAMS} | {"tesy_features"}
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
        | WaterHeaterEntityFeature.ON_OFF
    )

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: TesyCoordinator,
        entry: ConfigEntry,
        description: Any,
    ) -> None:
        super().__init__(hass, coordinator, entry, description)

        # Default values
        self._attr_min_temp = 15
        self._attr_max_temp = 75

        if self.coordinator.data[ATTR_DEVICE_ID] in TESY_DEVICE_TYPES:
            self._attr_min_temp = TESY_DEVICE_TYPES[
                self.coordinator.data[ATTR_DEVICE_ID]
            ]["min_setpoint"]
            self._attr_max_temp = TESY_DEVICE_TYPES[
                self.coordinator.data[ATTR_DEVICE_ID]
            ]["max_setpoint"]

            # if heater only supports showers, get its maximum depending on model, position
            if (
                "use_showers"
                in TESY_DEVICE_TYPES[self.coordinator.data[ATTR_DEVICE_ID]]
                and TESY_DEVICE_TYPES[self.coordinator.data[ATTR_DEVICE_ID]][
                    "use_showers"
                ]
                == True
            ):
                self._attr_max_temp = max_showers(
                    self.coordinator.data, self._attr_max_temp
                )

    @property
    def precision(self) -> float:
        """Water temperature in tenths as the heater reports it (tmpC "54.2").

        Shower models report a whole number of showers instead.
        """
        device = TESY_DEVICE_TYPES.get(self.coordinator.data.get(ATTR_DEVICE_ID), {})
        return PRECISION_WHOLE if device.get("use_showers") else PRECISION_TENTHS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return to_float(self.coordinator.data.get(ATTR_CURRENT_TEMP))

    @property
    def current_operation(self):
        """Return current operation."""

        if (
            ATTR_POWER not in self.coordinator.data
            or ATTR_MODE not in self.coordinator.data
        ):
            return STATE_OFF

        # if powered off
        if self.coordinator.data[ATTR_POWER] != "1":
            return STATE_OFF

        # Unknown modes are reported as off
        return TESY_MODE_TO_OPERATION.get(self.coordinator.data[ATTR_MODE], STATE_OFF)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        # Just in case if power is missing from json, prevent crashes
        if ATTR_POWER not in self.coordinator.data:
            return

        if self.coordinator.data[ATTR_POWER] == "1":
            if self.coordinator.data[ATTR_MODE] != "0":
                response = await self.coordinator.async_set_operation_mode("0")
                await self.partially_update_data_from_api(response, ATTR_MODE)

        response = await self.coordinator.async_set_target_temperature(
            kwargs.get(ATTR_TEMPERATURE)
        )
        await self.partially_update_data_from_api(
            response, ATTR_TARGET_TEMP, ATTR_CURRENT_TARGET_TEMP
        )
        # Optimistic: in manual mode, tmpR always equals tmpT
        new_temp = kwargs.get(ATTR_TEMPERATURE)
        if new_temp is not None:
            self.coordinator.data[ATTR_CURRENT_TARGET_TEMP] = new_temp
            self.coordinator.async_set_updated_data(self.coordinator.data)

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new target operation mode."""

        # Just in case if power is missing from json, prevent crashes
        if ATTR_POWER not in self.coordinator.data:
            return

        if operation_mode == STATE_OFF:
            response = await self.coordinator.async_set_power("0")
            await self.partially_update_data_from_api(response, ATTR_POWER)
        else:
            # Raises ValueError for an unknown mode, before anything is sent
            new_mode = tesy_mode(operation_mode)

            if self.coordinator.data[ATTR_POWER] == "0":
                response = await self.coordinator.async_set_power("1")
                await self.partially_update_data_from_api(response, ATTR_POWER)

            response = await self.coordinator.async_set_operation_mode(new_mode)
            await self.partially_update_data_from_api(
                response,
                ATTR_MODE,
                ATTR_TARGET_TEMP,
                ATTR_CURRENT_TARGET_TEMP,
                ATTR_POWER,
            )

            if (
                operation_mode in (STATE_ECO, TESY_MODE_EC2, TESY_MODE_EC3)
                and not self.coordinator.is_old_api
            ):
                response = await self.coordinator.async_set_target_temperature(
                    self._attr_max_temp
                )
                await self.partially_update_data_from_api(
                    response, ATTR_CURRENT_TARGET_TEMP
                )

    async def async_turn_on(self, **_kwargs: Any) -> None:
        """Turn on water heater."""
        response = await self.coordinator.async_set_power("1")
        await self.partially_update_data_from_api(response, ATTR_POWER)

    async def async_turn_off(self, **_kwargs: Any) -> None:
        """Turn off water heater."""
        response = await self.coordinator.async_set_power("0")
        await self.partially_update_data_from_api(response, ATTR_POWER)

    @property
    def target_temperature(self):
        """Return the target the heater is currently working towards."""
        return active_target(
            self.coordinator.data, use_schedule=self.coordinator.supports_schedule
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        data = self.coordinator.data
        attributes: dict[str, Any] = {
            "is_heating": ATTR_IS_HEATING in data and data[ATTR_IS_HEATING] == "1",
            "target_temp_step": 1,
        }

        features = self.coordinator.features
        if features:
            # Lets dashboards tell a heater with extended features from one
            # with basic control.
            attributes["tesy_features"] = sorted(features)

        if self.coordinator.supports_schedule:
            # Setpoint used in manual mode, kept while another mode is active.
            manual = to_float(data.get(ATTR_TARGET_TEMP))
            if manual is not None:
                attributes["manual_temperature"] = manual
            attributes["active_program"] = active_program(data)
            for program in PROGRAMS:
                attributes[f"schedule_p{program}"] = get_program(data, program)

        return attributes

    async def async_set_schedule(
        self, program: int, temperatures: list[int | None], days: list[str]
    ) -> None:
        """Write 24 hourly temperatures (None = empty hour) to program days."""
        if not self.coordinator.supports_schedule:
            # The service is per platform; another Tesy heater may support it.
            raise ServiceValidationError(
                f"Weekly programs are not supported on {self.entity_id}"
            )
        try:
            value = encode_day(temperatures)
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err

        written: list[str] = []
        for day in days:
            key = schedule_key(program, day)
            try:
                response = await self.coordinator.async_set_schedule(key, value)
            except ValueError as err:  # not JSON: keep the partial-write context
                raise HomeAssistantError(
                    write_failure_message(
                        program, written, day, "invalid response from heater"
                    )
                ) from err
            except (ConnectionError, NotImplementedError) as err:
                # The client wraps transport errors in a bare ConnectionError:
                # name the cause then (e.g. ReadTimeout), like the poll does.
                reason = str(err) or (
                    f"cannot reach heater: {type(err.__cause__ or err).__name__}"
                )
                raise HomeAssistantError(
                    write_failure_message(program, written, day, reason)
                ) from err

            # Report only the api value: a reply may include the MAC address
            ok = isinstance(response, dict)
            if not ok or response.get("api") != "OK" or response.get(key) != value:
                api = response.get("api") if ok else type(response).__name__
                raise HomeAssistantError(
                    write_failure_message(
                        program, written, day, f"rejected by the heater (api={api!r})"
                    )
                )
            await self.partially_update_data_from_api(response, key)
            written.append(day.upper())
