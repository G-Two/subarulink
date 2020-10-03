#  SPDX-License-Identifier: Apache-2.0
"""
subarulink - A Python Package for interacting with Subaru Starlink Remote Services API.

controller.py - provides managed connection to Subaru API

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
import asyncio
from datetime import datetime
import json
import logging
import pprint
import time

from subarulink.connection import Connection
import subarulink.const as sc
from subarulink.exceptions import InvalidPIN, PINLockoutProtect, SubaruException

_LOGGER = logging.getLogger(__name__)


class Controller:
    """Controller for connections to Subaru Starlink API."""

    def __init__(
        self, websession, username, password, device_id, pin, device_name, update_interval=7200, fetch_interval=300,
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
        self._connection = Connection(websession, username, password, device_id, device_name)
        self._update_interval = update_interval
        self._fetch_interval = fetch_interval
        self._car_data = {}
        self._update = {}
        self._pin = pin
        self._vin_id_map = {}
        self._vin_name_map = {}
        self._api_gen = {}
        self._lock = {}
        self._hasEV = {}
        self._hasRemote = {}
        self._hasRES = {}
        self._hasSafety = {}
        self._controller_lock = asyncio.Lock()
        self._last_update_time = {}
        self._last_fetch_time = {}
        self._cars = []
        self._pin_lockout = False

    async def connect(self, test_login=False) -> bool:
        """
        Connect to Subaru Remote Services API.

        Args:
            test_login (Bool, optional): Only check for authorization

        """
        if test_login:
            response = await self._connection.connect(test_login=True)
            if response:
                return True
            return False

        _LOGGER.debug("Connecting controller to Subaru Remote Services")
        cars = await self._connection.connect()
        if cars is None:
            raise SubaruException("Connection to Subaru API failed")

        for car in cars:
            vin = car["vin"].upper()
            self._cars.append(vin)
            self._vin_name_map[vin] = car["display_name"]
            self._vin_id_map[vin] = car["id"]
            self._api_gen[vin] = car["api_gen"]
            self._hasEV[vin] = car["hasEV"]
            self._hasRES[vin] = car["hasRES"]
            self._hasRemote[vin] = car["hasRemote"]
            self._hasSafety[vin] = car["hasSafety"]
            self._lock[vin] = asyncio.Lock()
            self._last_update_time[vin] = 0
            self._last_fetch_time[vin] = 0
            self._car_data[vin] = {"status": {}}
            self._update[vin] = True

        _LOGGER.debug("Subaru Remote Services Ready!")
        return True

    async def test_pin(self):
        """Tests if stored PIN is valid for Remote Services."""
        _LOGGER.info("Testing PIN for validity with Subaru remote services")
        for vin in self._cars:
            if self._hasRemote[vin]:
                await self._connection.validate_session(vin)
                api_gen = self._api_gen[vin]
                form_data = {"pin": self._pin}
                async with self._lock[vin]:
                    js_resp = await self._post("service/%s/vehicleStatus/execute.json" % (api_gen), json=form_data)
                    _LOGGER.debug(pprint.pformat(js_resp))
                    if js_resp["success"]:
                        _LOGGER.info("PIN is valid for Subaru remote services")
                        return True
                    if js_resp["errorCode"] == "InvalidCredentials":
                        _LOGGER.error("PIN is not valid for Subaru remote services")
                        self._pin_lockout = True
                        raise InvalidPIN("Invalid PIN! %s" % js_resp["data"]["errorDescription"])
        return False
        _LOGGER.info("No active vehicles with remote services subscription - PIN not required")

    def get_vehicles(self):
        """Return list of VINs available to user on Subaru Remote Services API."""
        return self._cars

    def get_ev_status(self, vin):
        """Get if EV."""
        _LOGGER.debug("Getting EV Status %s:%s", vin, str(self._hasEV.get(vin)))
        return self._hasEV.get(vin.upper())

    def get_remote_status(self, vin):
        """Get if remote services available."""
        _LOGGER.debug("Getting remote Status %s:%s", vin, str(self._hasRemote.get(vin)))
        return self._hasRemote.get(vin.upper())

    def get_res_status(self, vin):
        """Get if remote engine start is available."""
        _LOGGER.debug("Getting RES Status %s:%s", vin, str(self._hasRES.get(vin)))
        return self._hasRES.get(vin.upper())

    def get_safety_status(self, vin):
        """Get if safety plus subscription is active."""
        _LOGGER.debug("Getting Safety Plus Status %s:%s", vin, str(self._hasSafety.get(vin)))
        return self._hasSafety.get(vin.upper())

    def get_api_gen(self, vin):
        """Get API version (g1 or g2) for vehicle."""
        return self._api_gen.get(vin.upper())

    def vin_to_name(self, vin):
        """Return display name for a given VIN."""
        return self._vin_name_map.get(vin.upper())

    async def get_data(self, vin):
        """Get locally cached vehicle data.  Fetch if not present."""
        vin = vin.upper()
        if len(self._car_data[vin]["status"]) == 0:
            await self.fetch(vin)
        return self._car_data[vin]

    async def get_climate_settings(self, vin):
        """Fetch saved climate control settings."""
        vin = vin.upper()
        if self._hasRES[vin] or self._hasEV[vin]:
            await self._connection.validate_session(vin)
            js_resp = await self._get("service/g2/remoteEngineStart/fetch.json")
            _LOGGER.debug(js_resp)
            if js_resp["success"]:
                self._car_data[vin]["climate"] = json.loads(js_resp["data"])
                return True
            else:
                _LOGGER.error("Failed to fetch saved climate settings: %s", js_resp["errorCode"])

    async def save_climate_settings(self, vin, form_data):
        """Fetch saved climate control settings."""
        vin = vin.upper()
        if self._hasRES[vin] or self._hasEV[vin]:
            if self._validate_remote_start_params(vin, form_data):
                js_resp = await self._post("/service/g2/remoteEngineStart/save.json", json=form_data)
                _LOGGER.debug(js_resp)
                if js_resp["success"]:
                    self._car_data[vin]["climate"] = js_resp["data"]
                    _LOGGER.info("Climate control settings saved.")
                    return True
            else:
                _LOGGER.error("Failed to fetch saved climate settings: %s", js_resp["errorCode"])

    async def fetch(self, vin, force=False):
        """Fetch latest data from Subaru.  Does not invoke a remote request."""
        vin = vin.upper()
        cur_time = time.time()
        async with self._controller_lock:
            last_fetch = self._last_fetch_time[vin]
            if force or cur_time - last_fetch > self._fetch_interval:
                await self._fetch_status(vin)
                self._last_fetch_time[vin] = cur_time

    async def update(self, vin, force=False):
        """Request Subaru send remote command to update vehicle data."""
        vin = vin.upper()
        cur_time = time.time()
        async with self._controller_lock:
            last_update = self._last_update_time[vin]
            if force or cur_time - last_update > self._update_interval:
                result = await self._locate(vin, hard_poll=True)
                await self._fetch_status(vin)
                self._last_update_time[vin] = cur_time
                return result

    def get_update_interval(self):
        """Get current update interval."""
        return self._update_interval

    def set_update_interval(self, value):
        """Set new update interval."""
        old_interval = self._update_interval
        if value >= 300:
            self._update_interval = value
            _LOGGER.debug("Update interval changed from %s to %s", old_interval, value)
        else:
            _LOGGER.error("Invalid update interval %s. Keeping old value: %s", value, old_interval)

    def get_fetch_interval(self):
        """Get current fetch interval."""
        return self._fetch_interval

    def set_fetch_interval(self, value):
        """Set new fetch interval."""
        old_interval = self._fetch_interval
        if value >= 60:
            self._fetch_interval = value
            _LOGGER.debug("Fetch interval changed from %s to %s", old_interval, value)
        else:
            _LOGGER.error("Invalid fetch interval %s. Keeping old value: %s", value, old_interval)

    def get_last_update_time(self, vin):
        """Get last time update() remote command was used."""
        return self._last_update_time[vin.upper()]

    async def charge_start(self, vin):
        """Start EV charging."""
        success, _ = await self._remote_command(vin.upper(), "phevChargeNow")
        return success

    async def lock(self, vin):
        """Send lock command."""
        form_data = {"forceKeyInCar": False}
        success, _ = await self._actuate(vin.upper(), "lock", data=form_data)
        return success

    async def unlock(self, vin, only_driver=True):
        """Send unlock command."""
        door = sc.ALL_DOORS
        if only_driver:
            door = sc.DRIVERS_DOOR
        form_data = {sc.WHICH_DOOR: door}
        success, _ = await self._actuate(vin.upper(), "unlock", data=form_data)
        return success

    async def lights(self, vin):
        """Send lights command."""
        success, _ = await self._actuate(vin.upper(), "lightsOnly")
        return success

    async def horn(self, vin):
        """Send horn command."""
        success, _ = await self._actuate(vin.upper(), "hornLights")
        return success

    async def remote_stop(self, vin):
        """Send remote stop command."""
        success, _ = await self._actuate(vin.upper(), "engineStop")
        return success

    async def remote_start(self, vin, form_data=None):
        """Send remote start command."""
        vin = vin.upper()
        if self._hasRES[vin] or self._hasEV[vin]:
            if form_data:
                if self._validate_remote_start_params(vin, form_data):
                    climate_settings = form_data
                else:
                    raise SubaruException("Error with climate settings")
            else:
                await self.get_climate_settings(vin)
                climate_settings = self._car_data[vin]["climate"]
            if climate_settings:
                success, _ = await self._actuate(vin, "engineStart", data=climate_settings)
                return success
            else:
                raise SubaruException("Error with climate settings")
        else:
            raise SubaruException("Remote Start not supported for this vehicle")

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
        vin = vin.upper()
        if vin in self._update:
            return self._update[vin]
        return None

    def set_updates(self, vin, setting):
        """Change update setting for vehicle."""
        self._update[vin.upper()] = setting

    def invalid_pin_entered(self):
        """Return if invalid PIN error was received, thus locking out further remote commands."""
        return self._pin_lockout

    def updated_saved_pin(self, new_pin):
        """Update the saved PIN used by the controller."""
        if new_pin != self._pin:
            self._pin = new_pin
            self._pin_lockout = False
            return True
        return False

    async def _get(self, cmd, params=None, data=None, json=None):
        return await self._connection.get("/%s" % cmd, params, data, json)

    async def _post(self, cmd, params=None, data=None, json=None):
        return await self._connection.post("/%s" % cmd, params, data, json)

    async def _remote_query(self, vin, cmd, data=None):
        await self._connection.validate_session(vin)
        api_gen = self._api_gen[vin]
        async with self._lock[vin]:
            js_resp = await self._get("service/%s/%s/execute.json" % (api_gen, cmd), json=data)
            _LOGGER.debug(pprint.pformat(js_resp))
            if js_resp["success"]:
                return js_resp
            raise SubaruException("Remote query failed. Response: %s " % js_resp)

    async def _remote_command(self, vin, cmd, data=None, poll_url="/service/api_gen/remoteService/status.json"):
        if not self._pin_lockout:
            await self._connection.validate_session(vin)
            api_gen = self._api_gen[vin]
            form_data = {"pin": self._pin}
            if data:
                form_data.update(data)
            req_id = ""
            async with self._lock[vin]:
                js_resp = await self._post("service/%s/%s/execute.json" % (api_gen, cmd), json=form_data)
                _LOGGER.debug(pprint.pformat(js_resp))
                if js_resp["success"]:
                    req_id = js_resp["data"][sc.SERVICE_REQ_ID]
                    return await self._wait_request_status(req_id, api_gen, poll_url)
                if js_resp["errorCode"] == "InvalidCredentials":
                    self._pin_lockout = True
                    raise InvalidPIN("Invalid PIN! %s" % js_resp["data"]["errorDescription"])
                if js_resp["errorCode"] == "ServiceAlreadyStarted":
                    return False, None
                raise SubaruException("Remote command failed.  Response: %s " % js_resp)
        raise PINLockoutProtect("Remote command with invalid PIN cancelled to prevent account lockout")

    async def _actuate(self, vin, cmd, data=None):
        form_data = {"delay": 0, "vin": vin}
        if data:
            form_data.update(data)
        if self.get_remote_status(vin):
            return await self._remote_command(vin, cmd, data=form_data)
        else:
            raise SubaruException("Command requires REMOTE subscription.")

    async def _get_vehicle_status(self, vin):
        await self._connection.validate_session(vin)
        js_resp = await self._get("vehicleStatus.json")
        _LOGGER.debug(pprint.pformat(js_resp))
        return js_resp

    async def _fetch_status(self, vin):
        if self.get_safety_status(vin):
            _LOGGER.debug("Fetching vehicle status from Subaru")
            js_resp = await self._get_vehicle_status(vin)
            if js_resp.get("success") and js_resp.get("data"):
                data = js_resp["data"]
                status = {}
                status[sc.ODOMETER] = data.get(sc.VS_ODOMETER)
                status[sc.TIMESTAMP] = data.get(sc.VS_TIMESTAMP) / 1000
                status[sc.HEADING] = data.get(sc.VS_HEADING)
                status[sc.AVG_FUEL_CONSUMPTION] = data.get(sc.VS_AVG_FUEL_CONSUMPTION)
                status[sc.DIST_TO_EMPTY] = data.get(sc.VS_DIST_TO_EMPTY)
                status[sc.VEHICLE_STATE] = data.get(sc.VS_VEHICLE_STATE)
                status[sc.TIRE_PRESSURE_FL] = int(data.get(sc.VS_TIRE_PRESSURE_FL) or 0)
                status[sc.TIRE_PRESSURE_FR] = int(data.get(sc.VS_TIRE_PRESSURE_FR) or 0)
                status[sc.TIRE_PRESSURE_RL] = int(data.get(sc.VS_TIRE_PRESSURE_RL) or 0)
                status[sc.TIRE_PRESSURE_RR] = int(data.get(sc.VS_TIRE_PRESSURE_RR) or 0)
                if data.get(sc.VS_LONGITUDE) != sc.BAD_LONGITUDE:
                    status[sc.LONGITUDE] = data.get(sc.VS_LONGITUDE)
                if data.get(sc.VS_LATITUDE) != sc.BAD_LATITUDE:
                    status[sc.LATITUDE] = data.get(sc.VS_LATITUDE)
                if data.get(sc.VS_HEADING):
                    status[sc.HEADING] = data.get(sc.VS_HEADING)

                self._car_data[vin]["status"].update(status)
            else:
                raise SubaruException("Error fetching vehicle status %s" % pprint.pformat(js_resp))
        else:
            raise SubaruException("Safety Plus subscription required for this vehicle")

        # Additional Data (Security Plus Required)
        if self.get_remote_status(vin):
            js_resp = await self._remote_query(vin, "condition")
            if js_resp.get("success") and js_resp.get("data"):
                status = await self._cleanup_condition(js_resp, vin)
                self._car_data[vin]["status"].update(status)

    async def _cleanup_condition(self, js_resp, vin):
        data = {}
        try:
            # Annoying key/value pair format [{"key": key, "value": value}, ...]
            data = {i["key"]: i["value"] for i in js_resp["data"]["result"]["vehicleStatus"]}
            data[sc.TIMESTAMP] = datetime.strptime(
                js_resp["data"]["result"]["lastUpdatedTime"], sc.TIMESTAMP_FMT
            ).timestamp()
            data[sc.POSITION_TIMESTAMP] = datetime.strptime(
                data[sc.POSITION_TIMESTAMP], sc.POSITION_TIMESTAMP_FMT
            ).timestamp()

            # Discard these values since vehicleStatus.json is always more reliable
            data.pop(sc.ODOMETER)
            data.pop(sc.AVG_FUEL_CONSUMPTION)
            data.pop(sc.DIST_TO_EMPTY)
            data.pop(sc.TIRE_PRESSURE_FL)
            data.pop(sc.TIRE_PRESSURE_FR)
            data.pop(sc.TIRE_PRESSURE_RL)
            data.pop(sc.TIRE_PRESSURE_RR)

            if self.get_ev_status(vin):
                if int(data.get(sc.EV_DISTANCE_TO_EMPTY) or 0) > 20:
                    # This value is incorrectly high immediately after car shutdown
                    data.pop(sc.EV_DISTANCE_TO_EMPTY)
                if (
                    int(data.get(sc.EV_TIME_TO_FULLY_CHARGED) or sc.BAD_EV_TIME_TO_FULLY_CHARGED)
                    == sc.BAD_EV_TIME_TO_FULLY_CHARGED
                ):
                    # Value is None or known erroneous number
                    data[sc.EV_TIME_TO_FULLY_CHARGED] = 0
                # Value is correct unless it is None
                data[sc.EV_DISTANCE_TO_EMPTY] = int(data.get(sc.EV_DISTANCE_TO_EMPTY) or 0)

            # Replace lat/long from a more reliable source for Security Plus subscribers
            await self._locate(vin)
        except KeyError:  # Once in a while a 'value' key or some other field is missing
            pass

        return data

    async def _locate(self, vin, hard_poll=False):
        if hard_poll:
            # Sends a locate command to the vehicle to get real time position
            success, js_resp = await self._remote_command(
                vin, "vehicleStatus", poll_url="/service/api_gen/vehicleStatus/locationStatus.json",
            )
        else:
            # Reports the last location the vehicle has reported to Subaru
            js_resp = await self._remote_query(vin, "locate")
            success = js_resp["success"]

        if success and js_resp.get("success"):
            self._car_data[vin]["status"][sc.LONGITUDE] = js_resp["data"]["result"][sc.LONGITUDE]
            self._car_data[vin]["status"][sc.LATITUDE] = js_resp["data"]["result"][sc.LATITUDE]
            self._car_data[vin]["status"][sc.HEADING] = js_resp["data"]["result"][sc.HEADING]
            return True

    async def _wait_request_status(self, req_id, api_gen, poll_url, attempts=20):
        params = {sc.SERVICE_REQ_ID: req_id}
        attempt = 0
        _LOGGER.debug("Polling for remote service request completion: serviceRequestId=%s", req_id)
        while attempt < attempts:
            try:
                js_resp = await self._connection.get(poll_url.replace("api_gen", api_gen), params=params)
            except SubaruException as ex:
                attempt += 1
                _LOGGER.error("Remote service status poll request returned error %s", ex.message)
                continue
            _LOGGER.debug(pprint.pformat(js_resp))
            if not js_resp["success"]:
                _LOGGER.error("Remote service command returned error: %s", js_resp["errorCode"])
            elif js_resp["data"]["remoteServiceState"] == "finished":
                if js_resp["data"]["success"]:
                    _LOGGER.info("Remote service request completed successfully: %s", req_id)
                    return True, js_resp
                else:
                    _LOGGER.error(
                        "Remote service request completed but failed: %s Error: %s",
                        req_id,
                        js_resp["data"]["errorCode"],
                    )
                    return False, js_resp
            elif js_resp["data"].get("remoteServiceState") == "started":
                _LOGGER.info("Subaru API reports remote service request is in progress: %s", req_id)
            attempt += 1
            await asyncio.sleep(2)
        _LOGGER.error("Remote service request completion message not received")
        return False, None

    def _validate_remote_start_params(self, vin, form_data):
        try:
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
            if form_data[sc.HEAT_SEAT_LEFT] not in [
                sc.HEAT_SEAT_OFF,
                sc.HEAT_SEAT_HI,
                sc.HEAT_SEAT_MED,
                sc.HEAT_SEAT_LOW,
            ]:
                is_valid = False
            if form_data[sc.HEAT_SEAT_RIGHT] not in [
                sc.HEAT_SEAT_OFF,
                sc.HEAT_SEAT_HI,
                sc.HEAT_SEAT_MED,
                sc.HEAT_SEAT_LOW,
            ]:
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

            form_data[sc.RUNTIME] = sc.RUNTIME_DEFAULT
            form_data[sc.CLIMATE] = sc.CLIMATE_DEFAULT
            if self._hasEV[vin]:
                form_data[sc.START_CONFIG] = sc.START_CONFIG_DEFAULT_EV
            elif self._hasRES[vin]:
                form_data[sc.START_CONFIG] = sc.START_CONFIG_DEFAULT_RES
            else:
                raise SubaruException("Vehicle Remote Start not supported.")

            return is_valid

        except KeyError:
            return None
