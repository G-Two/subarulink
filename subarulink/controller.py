#  SPDX-License-Identifier: Apache-2.0
"""
subarulink - A Python Package for interacting with Subaru Starlink Remote Services API.

controller.py - provides managed connection to Subaru API

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
import asyncio
import logging
import pprint
import time

from subarulink.connection import Connection
import subarulink.const as sc
from subarulink.exceptions import SubaruException

_LOGGER = logging.getLogger(__name__)


class Controller:
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
        self._connection = Connection(
            websession, username, password, device_id, device_name
        )
        self._update_interval: int = update_interval
        self._car_data = {}
        self._update = {}
        self._pin = pin
        self._id_vin_map = {}
        self._vin_id_map = {}
        self._vin_name_map = {}
        self._api_gen = {}
        self._lock = {}
        self._current_id = None
        self._current_vin = None
        self._controller_lock = asyncio.Lock()
        self._last_update_time = {}
        self._cars = []

    async def connect(self, test_login=False) -> bool:
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
        _LOGGER.debug("Subaru Remote Services Ready!")
        return True

    def get_vehicles(self):
        """Return list of VINs available to user on Subaru Remote Services API."""
        return self._cars

    def get_api_gen(self, vin):
        """Get API version (g1 or g2) for vehicle."""
        return self._api_gen.get(vin)

    def vin_to_name(self, vin):
        """Return display name for a given VIN."""
        return self._vin_name_map.get(vin)

    async def get_data(self, vin):
        """Get locally cached vehicle data.  Fetch if not present."""
        if len(self._car_data[vin]) == 0:
            await self._fetch_status(vin)
        return self._car_data[vin]

    async def fetch(self, vin):
        """Fetch latest data from Subaru.  Does not invoke a remote request."""
        await self._fetch_status(vin)
        return self._car_data[vin]

    async def update(self, vin, force=False):
        """Request Subaru send remote command to update vehicle data."""
        cur_time = time.time()
        async with self._controller_lock:
            last_update = self._last_update_time[vin]
            if force or cur_time - last_update > self._update_interval:
                await self._locate(vin)
                await self._fetch_status(vin)
                self._last_update_time[vin] = cur_time

    def get_last_update_time(self, vin):
        """Get last time update() remote command was used."""
        return self._last_update_time[vin]

    async def charge_start(self, vin):
        """Start EV charging."""
        return await self._remote_command(vin, "phevChargeNow")

    async def lock(self, vin):
        """Send lock command."""
        form_data = {"forceKeyInCar": False}
        return await self._actuate(vin, "lock", data=form_data)

    async def unlock(self, vin, only_driver=True):
        """Send unlock command."""
        door = sc.ALL_DOORS
        if only_driver:
            door = sc.DRIVERS_DOOR
        form_data = {sc.WHICH_DOOR: door}
        return await self._actuate(vin, "unlock", data=form_data)

    async def lights(self, vin):
        """Send lights command."""
        await self._actuate(vin, "lightsOnly")

    async def horn(self, vin):
        """Send horn command."""
        await self._actuate(vin, "hornLights")

    async def remote_stop(self, vin):
        """Send remote stop command."""
        await self._actuate(vin, "engineStop")

    async def remote_start(
        self,
        vin,
        temp,
        mode,
        heat_left_seat,
        heat_right_seat,
        rear_defrost,
        fan_speed,
        recirculate,
        rear_ac,
    ):
        """Send remote start command."""
        form_data = {
            sc.TEMP: temp,
            sc.CLIMATE: sc.CLIMATE_DEFAULT,
            sc.RUNTIME: sc.RUNTIME_DEFAULT,
            sc.MODE: mode,
            sc.HEAT_SEAT_LEFT: heat_left_seat,
            sc.HEAT_SEAT_RIGHT: heat_right_seat,
            sc.REAR_DEFROST: rear_defrost,
            sc.FAN_SPEED: fan_speed,
            sc.RECIRCULATE: recirculate,
            sc.REAR_AC: rear_ac,
            sc.START_CONFIG: sc.START_CONFIG_DEFAULT,
        }
        if _validate_remote_start_params(form_data):
            await self._actuate(vin, "engineStart", data=form_data)
        else:
            return None

    def get_updates(self, vin):
        """Get updates dictionary.

        Parameters
        ----------
        vin : string
            VIN for the vehicle.

        Returns
        -------
        bool or None
            If vin exists, a bool indicating whether updates should be
            processed. Othewise, returns None.

        """
        if vin in self._update:
            return self._update[vin]
        return None

    def set_updates(self, vin, setting):
        """Change update setting for vehicle."""
        self._update[vin] = setting

    async def _get(self, cmd, params=None, data=None, json=None):
        return await self._connection.get("/%s" % cmd, params, data, json)

    async def _post(self, cmd, params=None, data=None, json=None):
        return await self._connection.post("/%s" % cmd, params, data, json)

    async def _remote_query(self, vin, cmd, data=None):
        await self._connection.validate_session()
        api_gen = await self._select_vehicle(vin)
        async with self._lock[vin]:
            js_resp = await self._get(
                "service/%s/%s/execute.json" % (api_gen, cmd), json=data
            )
            _LOGGER.debug(pprint.pformat(js_resp))
            if js_resp["success"]:
                return js_resp
            raise SubaruException("Remote query failed. Response: %s " % js_resp)

    async def _remote_command(
        self, vin, cmd, data=None, poll_url="/service/api_gen/remoteService/status.json"
    ):
        await self._connection.validate_session()
        api_gen = await self._select_vehicle(vin)
        form_data = {"pin": self._pin}
        if data:
            form_data.update(data)
        req_id = ""
        async with self._lock[vin]:
            js_resp = await self._post(
                "service/%s/%s/execute.json" % (api_gen, cmd), json=form_data
            )
            _LOGGER.debug(pprint.pformat(js_resp))
            if js_resp["success"]:
                req_id = js_resp["data"][sc.SERVICE_REQ_ID]
                js_resp = await self._wait_request_status(req_id, api_gen, poll_url)
                return js_resp
            raise SubaruException("Remote command failed.  Response: %s " % js_resp)

    async def _actuate(self, vin, cmd, data=None):
        form_data = {"delay": 0, "vin": vin}
        if data:
            form_data.update(data)
        return await self._remote_command(vin, cmd, data=form_data)

    async def _fetch_status(self, vin):
        _LOGGER.debug("Fetching vehicle status from Subaru")
        js_resp = await self._remote_query(vin, "condition")
        if js_resp:
            status = {}
            try:
                # Annoying key/value pair format [{"key": key, "value": value}, ...]
                status = {
                    i["key"]: i["value"]
                    for i in js_resp["data"]["result"]["vehicleStatus"]
                }
            except KeyError:
                # Once in a while a 'value' key is missing
                pass
            status[sc.ODOMETER] = js_resp["data"]["result"]["odometer"]
            status[sc.TIMESTAMP] = js_resp["data"]["result"]["lastUpdatedTime"]
            self._car_data[vin]["status"] = status

    async def _locate(self, vin):
        js_resp = await self._remote_command(
            vin,
            "vehicleStatus",
            poll_url="/service/api_gen/vehicleStatus/locationStatus.json",
        )
        if js_resp:
            self._car_data[vin]["location"] = js_resp["data"]["result"]

    async def _wait_request_status(self, req_id, api_gen, poll_url, attempts=20):
        success = False
        params = {sc.SERVICE_REQ_ID: req_id}
        attempt = 0
        _LOGGER.debug(
            "Polling for remote service request completion: serviceRequestId=%s", req_id
        )
        while not success and attempt < attempts:
            js_resp = await self._connection.get(
                poll_url.replace("api_gen", api_gen), params=params
            )
            _LOGGER.debug(pprint.pformat(js_resp))
            if js_resp["data"]["success"]:
                success = True
                _LOGGER.debug(
                    "Remote service request completed: serviceRequestId=%s", req_id
                )
                return js_resp
            attempt += 1
            await asyncio.sleep(2)
        _LOGGER.error("Remote service request completion message not received")
        return False

    async def _select_vehicle(self, vin=None):
        params = {}
        if self._vin_id_map.get(vin):
            params["vin"] = vin
            params["_"] = int(time.time())
            js_resp = await self._get("selectVehicle.json", params=params)
            _LOGGER.debug(pprint.pformat(js_resp))
            if js_resp["success"]:
                self._current_vin = vin
                self._current_id = self._vin_id_map.get(vin)
                api_gen = "g1" if "g1" in js_resp["data"]["features"] else "g2"
                _LOGGER.debug(
                    "Current vehicle: vin=%s, api_gen=%s", self._current_vin, api_gen
                )
                return api_gen
        else:
            _LOGGER.error("No such vehicle: %s", vin)
            return None


def _validate_remote_start_params(form_data):
    temp = int(form_data[sc.TEMP])
    is_valid = True
    if temp > sc.TEMP_MAX or temp < sc.TEMP_MIN:
        is_valid = False
    if form_data[sc.MODE] not in [
        sc.MODE_AUTO,
        sc.MODE_DEFROST,
        sc.MODE_FACE,
        sc.MODE_FEET,
        sc.MODE_FEET_DEFROST,
        sc.MODE_SPLIT,
    ]:
        is_valid = False
    if form_data[sc.HEAT_SEAT_LEFT] not in [sc.HEAT_SEAT_OFF, sc.HEAT_SEAT_ON]:
        is_valid = False
    if form_data[sc.HEAT_SEAT_RIGHT] not in [sc.HEAT_SEAT_OFF, sc.HEAT_SEAT_ON]:
        is_valid = False
    if form_data[sc.REAR_DEFROST] not in [sc.REAR_DEFROST_OFF, sc.REAR_DEFROST_ON]:
        is_valid = False
    if form_data[sc.FAN_SPEED] not in [
        sc.FAN_SPEED_AUTO,
        sc.FAN_SPEED_HI,
        sc.FAN_SPEED_LOW,
        sc.FAN_SPEED_MED,
    ]:
        is_valid = False
    if form_data[sc.RECIRCULATE] not in [sc.RECIRCULATE_OFF, sc.RECIRCULATE_ON]:
        is_valid = False
    if form_data[sc.REAR_AC] not in [sc.REAR_AC_OFF, sc.REAR_AC_ON]:
        is_valid = False
    return is_valid
