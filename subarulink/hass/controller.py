#  SPDX-License-Identifier: Apache-2.0
"""
subarulink.hass - A subpackage intended for Home Assistant integrations.

controller.py - controller for Home Assistant

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
import logging
import time

import subarulink.const as sc
from subarulink.controller import Controller
from subarulink.hass.binary_sensor import EVChargerConnection
from subarulink.hass.climate import Climate
from subarulink.hass.device_tracker import GPS
from subarulink.hass.lock import Lock
from subarulink.hass.sensor import SubaruSensor
from subarulink.hass.switch import EVChargeSwitch, UpdateSwitch

_LOGGER = logging.getLogger(__name__)


class HassController(Controller):
    """Controller for connections to Subaru Starlink API."""

    def __init__(
        self,
        websession,
        username,
        password,
        device_id,
        pin,
        device_name,
        update_interval=7200,
        fetch_interval=300,
    ):
        """Initialize controller.

        Args:
            websession (aiohttp.ClientSession): Session
            username (Text): Username
            password (Text): Password
            device_id (Text): Alphanumeric designator that Subaru API uses to determine if a device is authorized to send remote requests
            pin (Text): 4 digit pin number string required to submit Subaru Remote requests
            device_name (Text): Human friendly name that is associated with device_id (shows on mysubaru.com profile "devices")
            update_interval (int, optional): Seconds between requests for vehicle send update
            fetch_interval (int, optional): Seconds between fetches of Subaru's cached vehicle information

        """
        super().__init__(
            websession,
            username,
            password,
            device_id,
            pin,
            device_name,
            update_interval,
            fetch_interval,
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

        await super().connect(test_login)
        for vin in self._cars:
            car = {}
            car["display_name"] = self._vin_name_map[vin]
            car["vin"] = vin
            car["id"] = self._vin_id_map[vin]
            if self._hasEV[vin]:
                self._components.append(
                    SubaruSensor(
                        car, "EV Battery Level", sc.EV_STATE_OF_CHARGE_PERCENT, self,
                    )
                )
                self._components.append(EVChargerConnection(car, self))
                self._components.append(
                    SubaruSensor(
                        car, "EV Charge Rate", sc.EV_TIME_TO_FULLY_CHARGED, self,
                    )
                )
                self._components.append(EVChargeSwitch(car, self))
                self._components.append(
                    SubaruSensor(car, "EV Range", sc.EV_DISTANCE_TO_EMPTY, self)
                )
            if self._hasRES[vin] or self._hasEV[vin]:
                self._components.append(Climate(car, self))
            if self._hasRemote[vin]:
                self._components.append(
                    SubaruSensor(
                        car, "Avg Fuel Consumption", sc.AVG_FUEL_CONSUMPTION, self,
                    )
                )
                self._components.append(
                    SubaruSensor(car, "12V Battery Voltage", sc.BATTERY_VOLTAGE, self)
                )
                self._components.append(GPS(car, self))
                self._components.append(UpdateSwitch(car, self))
                self._components.append(Lock(car, self))
                self._components.append(
                    SubaruSensor(car, "Odometer", sc.ODOMETER, self)
                )
                self._components.append(
                    SubaruSensor(car, "Range", sc.DIST_TO_EMPTY, self)
                )
                self._components.append(
                    SubaruSensor(car, "External Temp", sc.EXTERNAL_TEMP, self)
                )
        return True

    def get_homeassistant_components(self):
        """Return list of Subaru components for Home Assistant setup.

        Use get_vehicles() for general API use.
        """
        return self._components

    async def hass_update(self, vin):
        """Fetch or Update data, depending on how long it has been."""
        cur_time = time.time()
        async with self._controller_lock:
            last_update = self._last_update_time[vin]
            last_fetch = self._last_fetch_time[vin]
            if cur_time - last_update > self._update_interval:
                if last_update == 0:
                    # Don't do full update on first run so hass setup completes faster
                    await self._fetch_status(vin)
                else:
                    await self._locate(vin)
                    await self._fetch_status(vin)
                self._last_update_time[vin] = cur_time
                self._last_fetch_time[vin] = cur_time
            elif cur_time - last_fetch > self._fetch_interval:
                await self._fetch_status(vin)
                self._last_fetch_time[vin] = cur_time
