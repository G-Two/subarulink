#  SPDX-License-Identifier: Apache-2.0
"""
subarulink.hass - A subpackage intended for Home Assistant integrations.

controller.py - controller for Home Assistant

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
import logging
import time

from subarulink.controller import Controller
from subarulink.hass.battery_sensor import Battery, EVRange
from subarulink.hass.binary_sensor import ChargerConnectionSensor
from subarulink.hass.charger import ChargerSwitch, ChargingSensor
from subarulink.hass.climate import Climate, TempSensor
from subarulink.hass.gps import GPS, LocateSwitch, Odometer
from subarulink.hass.lock import Lock

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
                self._components.append(Battery(car, self))
                self._components.append(ChargerConnectionSensor(car, self))
                self._components.append(ChargingSensor(car, self))
                self._components.append(ChargerSwitch(car, self))
                self._components.append(EVRange(car, self))
            if self._hasRES[vin] or self._hasEV[vin]:
                self._components.append(Climate(car, self))
            if self._hasRemote[vin]:
                self._components.append(TempSensor(car, self))
                self._components.append(Lock(car, self))
                self._components.append(GPS(car, self))
                self._components.append(LocateSwitch(car, self))
                self._components.append(Odometer(car, self))
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
                self._last_update_time[vin] = cur_time
                self._last_fetch_time[vin] = cur_time
            elif cur_time - last_fetch > self._fetch_interval:
                await self._fetch_status(vin)
                self._last_fetch_time[vin] = cur_time
