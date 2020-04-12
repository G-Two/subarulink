#  SPDX-License-Identifier: Apache-2.0
"""
subarulink.hass - A subpackage intended for Home Assistant integrations.

controller.py - controller for Home Assistant

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
import asyncio
import logging

from subarulink.controller import Controller
from subarulink.exceptions import SubaruException
from subarulink.hass.battery_sensor import Battery, Range
from subarulink.hass.binary_sensor import ChargerConnectionSensor
from subarulink.hass.charger import ChargerSwitch, ChargingSensor
from subarulink.hass.climate import Climate, TempSensor
from subarulink.hass.gps import GPS, Odometer
from subarulink.hass.lock import Lock

_LOGGER = logging.getLogger(__name__)


class HassController(Controller):
    """Controller for connections to Subaru Starlink Gen2 API."""

    def __init__(
        self,
        websession,
        username,
        password,
        device_id,
        pin,
        device_name,
        update_interval=7200,
    ):
        """Initialize controller.

        Args:
            websession (aiohttp.ClientSession): Session
            username (Text): Username
            password (Text): Password
            device_id (Text): Alphanumeric designator that Subaru API uses to determine if a device is authorized to send remote requests
            pin (Text): 4 digit pin number string required to submit Subaru Remote requests
            device_name (Text): Human friendly name that is associated with device_id (shows on mysubaru.com profile "devices")
            update_interval (int, optional): Seconds between vehicle queries

        """
        super().__init__(
            websession, username, password, device_id, pin, device_name, update_interval
        )
        self._components = []

    async def connect(self, test_login=False):
        """
        Connect to Subaru Remote Services API.

        Args:
            test_login (Bool, optional): Only check for authorization

        """
        if test_login:
            response = await self._connection.connect()
            if response:
                return True
            return False

        _LOGGER.debug("Connecting controller to Subaru Remote Services")
        cars = await self._connection.connect()
        if cars is None:
            raise SubaruException("Connection to Subaru API failed")

        for car in cars:
            vin = car["vin"]
            self._cars.append(vin)
            self._vin_name_map[vin] = car["display_name"]
            self._id_vin_map[car["id"]] = vin
            self._vin_id_map[vin] = car["id"]
            _LOGGER.debug("Determining API generation with selectVehicle.json")
            self._api_gen[vin] = await self._select_vehicle(vin)
            self._lock[vin] = asyncio.Lock()
            self._last_update_time[vin] = 0
            self._car_data[vin] = {}
            self._update[vin] = True
            if self._api_gen[vin] == "g2":
                self._components.append(Climate(car, self))
                self._components.append(Battery(car, self))
                self._components.append(Range(car, self))
                self._components.append(TempSensor(car, self))
                self._components.append(Lock(car, self))
                self._components.append(ChargerConnectionSensor(car, self))
                self._components.append(ChargingSensor(car, self))
                self._components.append(ChargerSwitch(car, self))
                self._components.append(GPS(car, self))
                self._components.append(Odometer(car, self))
        _LOGGER.debug("Subaru Remote Services Ready!")
        return True

    def get_homeassistant_components(self):
        """Return list of Subaru components for Home Assistant setup.

        Use get_vehicles() for general API use.
        """
        return self._components
