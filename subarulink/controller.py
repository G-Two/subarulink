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
        self._vehicles = {}
        self._pin = pin
        self._controller_lock = asyncio.Lock()
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
        vehicle_list = await self._connection.connect()
        if vehicle_list is None:
            raise SubaruException("Connection to Subaru API failed")

        for vehicle in vehicle_list:
            self._parse_vehicle(vehicle)

        _LOGGER.debug("Subaru Remote Services Ready!")
        return True

    async def test_pin(self):
        """Tests if stored PIN is valid for Remote Services."""
        _LOGGER.info("Testing PIN for validity with Subaru remote services")
        for vin in self._vehicles:
            if self.get_remote_status(vin):
                await self._connection.validate_session(vin)
                api_gen = self.get_api_gen(vin)
                form_data = {"pin": self._pin}
                async with self._vehicles[vin][sc.VEHICLE_LOCK]:
                    js_resp = await self._post(sc.API_VEHICLE_STATUS.replace("api_gen", api_gen), json_data=form_data,)
                    _LOGGER.debug(pprint.pformat(js_resp))
                    if js_resp["success"]:
                        _LOGGER.info("PIN is valid for Subaru remote services")
                        return True
                    if js_resp["errorCode"] == "InvalidCredentials":
                        _LOGGER.error("PIN is not valid for Subaru remote services")
                        self._pin_lockout = True
                        raise InvalidPIN("Invalid PIN! %s" % js_resp["data"]["errorDescription"])
        _LOGGER.info("No active vehicles with remote services subscription - PIN not required")
        return False

    def get_vehicles(self):
        """Return list of VINs available to user on Subaru Remote Services API."""
        return list(self._vehicles.keys())

    def get_ev_status(self, vin):
        """Get if EV."""
        vehicle = self._vehicles.get(vin.upper())
        if vehicle:
            status = sc.FEATURE_PHEV in vehicle[sc.VEHICLE_FEATURES]
            _LOGGER.debug("Getting EV Status %s:%s", vin, status)
            return status
        return None

    def get_remote_status(self, vin):
        """Get if remote services available."""
        vehicle = self._vehicles.get(vin.upper())
        if vehicle:
            status = sc.FEATURE_REMOTE in vehicle[sc.VEHICLE_SUBSCRIPTION_FEATURES] and self.get_subscription_status(
                vin
            )
            _LOGGER.debug("Getting remote Status %s:%s", vin, status)
            return status
        return None

    def get_res_status(self, vin):
        """Get if remote engine start is available."""
        vehicle = self._vehicles.get(vin.upper())
        if vehicle:
            status = sc.FEATURE_REMOTE_START in vehicle[sc.VEHICLE_FEATURES] and self.get_subscription_status(vin)
            _LOGGER.debug("Getting RES Status %s:%s", vin, status)
            return status
        return None

    def get_safety_status(self, vin):
        """Get if safety plus subscription is active."""
        vehicle = self._vehicles.get(vin.upper())
        if vehicle:
            status = sc.FEATURE_SAFETY in vehicle[sc.VEHICLE_SUBSCRIPTION_FEATURES] and self.get_subscription_status(
                vin
            )
            _LOGGER.debug("Getting Safety Plus Status %s:%s", vin, status)
            return status
        return None

    def get_subscription_status(self, vin):
        """Get if subscription is active."""
        vehicle = self._vehicles.get(vin.upper())
        if vehicle:
            status = vehicle[sc.VEHICLE_SUBSCRIPTION_STATUS] == sc.FEATURE_ACTIVE
            _LOGGER.debug("Getting subscription Status %s:%s", vin, status)
            return status
        return None

    def get_api_gen(self, vin):
        """Get API version (g1 or g2) for vehicle."""
        vehicle = self._vehicles.get(vin.upper())
        if vehicle:
            if sc.FEATURE_G1_TELEMATICS in vehicle[sc.VEHICLE_FEATURES]:
                return sc.FEATURE_G1_TELEMATICS
            if sc.FEATURE_G2_TELEMATICS in vehicle[sc.VEHICLE_FEATURES]:
                return sc.FEATURE_G2_TELEMATICS
        return None

    def vin_to_name(self, vin):
        """Return display name for a given VIN."""
        vehicle = self._vehicles.get(vin.upper())
        if vehicle:
            return vehicle[sc.VEHICLE_NAME]
        return None

    async def get_data(self, vin):
        """Get locally cached vehicle data.  Fetch if not present."""
        vin = vin.upper()
        if len(self._vehicles[vin][sc.VEHICLE_STATUS]) == 0:
            await self.fetch(vin)
        return self._vehicles[vin]

    async def get_climate_settings(self, vin):
        """Fetch saved climate control settings."""
        vin = vin.upper()
        if self.get_res_status(vin) or self.get_ev_status(vin):
            await self._connection.validate_session(vin)
            js_resp = await self._get(sc.API_G2_FETCH_CLIMATE_SETTINGS)
            _LOGGER.debug(js_resp)
            if js_resp["success"]:
                self._vehicles[vin]["climate"] = json.loads(js_resp["data"])
                return True
            _LOGGER.error("Failed to fetch saved climate settings: %s", js_resp["errorCode"])

    async def save_climate_settings(self, vin, form_data):
        """Fetch saved climate control settings."""
        vin = vin.upper()
        if self.get_res_status(vin) or self.get_ev_status(vin):
            if self._validate_remote_start_params(vin, form_data):
                js_resp = await self._post(sc.API_G2_SAVE_CLIMATE_SETTINGS, json_data=form_data)
                _LOGGER.debug(js_resp)
                if js_resp["success"]:
                    self._vehicles[vin]["climate"] = js_resp["data"]
                    _LOGGER.info("Climate control settings saved.")
                    return True
            else:
                _LOGGER.error("Failed to fetch saved climate settings: %s", js_resp["errorCode"])

    async def fetch(self, vin, force=False):
        """Fetch latest data from Subaru.  Does not invoke a remote request."""
        vin = vin.upper()
        cur_time = time.time()
        async with self._controller_lock:
            last_fetch = self._vehicles[vin][sc.VEHICLE_LAST_FETCH]
            if force or cur_time - last_fetch > self._fetch_interval:
                await self._fetch_status(vin)
                self._vehicles[vin][sc.VEHICLE_LAST_FETCH] = cur_time

    async def update(self, vin, force=False):
        """Request Subaru send remote command to update vehicle data."""
        vin = vin.upper()
        cur_time = time.time()
        async with self._controller_lock:
            last_update = self._vehicles[vin][sc.VEHICLE_LAST_UPDATE]
            if force or cur_time - last_update > self._update_interval:
                result = await self._locate(vin, hard_poll=True)
                await self._fetch_status(vin)
                self._vehicles[vin][sc.VEHICLE_LAST_UPDATE] = cur_time
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
        return self._vehicles[vin][sc.VEHICLE_LAST_UPDATE]

    async def charge_start(self, vin):
        """Start EV charging."""
        success, _ = await self._remote_command(vin.upper(), "phevChargeNow")
        return success

    async def lock(self, vin):
        """Send lock command."""
        form_data = {"forceKeyInCar": False}
        success, _ = await self._actuate(vin.upper(), sc.API_LOCK, data=form_data)
        return success

    async def unlock(self, vin, only_driver=True):
        """Send unlock command."""
        door = sc.ALL_DOORS
        if only_driver:
            door = sc.DRIVERS_DOOR
        form_data = {sc.WHICH_DOOR: door}
        success, _ = await self._actuate(vin.upper(), sc.API_UNLOCK, data=form_data)
        return success

    async def lights(self, vin):
        """Send lights command."""
        success, _ = await self._actuate(vin.upper(), sc.API_LIGHTS)
        return success

    async def horn(self, vin):
        """Send horn command."""
        success, _ = await self._actuate(vin.upper(), sc.API_HORN_LIGHTS)
        return success

    async def remote_stop(self, vin):
        """Send remote stop command."""
        success, _ = await self._actuate(vin.upper(), sc.API_G2_REMOTE_ENGINE_STOP)
        return success

    async def remote_start(self, vin, form_data=None):
        """Send remote start command."""
        vin = vin.upper()
        if self.get_res_status(vin) or self.get_ev_status(vin):
            if form_data:
                if self._validate_remote_start_params(vin, form_data):
                    climate_settings = form_data
                else:
                    raise SubaruException("Error with climate settings")
            else:
                await self.get_climate_settings(vin)
                climate_settings = self._vehicles[vin]["climate"]
            if climate_settings:
                success, _ = await self._actuate(vin, sc.API_G2_REMOTE_ENGINE_START, data=climate_settings)
                return success
            raise SubaruException("Error with climate settings")
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
        vehicle = self._vehicles.get(vin.upper())
        if vehicle:
            return vehicle[sc.VEHICLE_UPDATE]
        return None

    def set_updates(self, vin, setting):
        """Change update setting for vehicle."""
        vehicle = self._vehicles.get(vin.upper())
        if vehicle:
            vehicle[sc.VEHICLE_UPDATE] = setting
            return True
        return None

    def invalid_pin_entered(self):
        """Return if invalid PIN error was received, thus locking out further remote commands."""
        return self._pin_lockout

    def update_saved_pin(self, new_pin):
        """Update the saved PIN used by the controller."""
        if new_pin != self._pin:
            self._pin = new_pin
            self._pin_lockout = False
            return True
        return False

    async def _get(self, url, params=None, data=None, json_data=None):
        return await self._connection.get(url, params, data, json_data)

    async def _post(self, url, params=None, data=None, json_data=None):
        return await self._connection.post(url, params, data, json_data)

    def _parse_vehicle(self, vehicle):
        vin = vehicle["vin"].upper()
        _LOGGER.debug("Parsing vehicle: %s", vin)
        self._vehicles[vin] = {
            sc.VEHICLE_NAME: vehicle[sc.VEHICLE_NAME],
            sc.VEHICLE_LOCK: asyncio.Lock(),
            sc.VEHICLE_LAST_FETCH: 0,
            sc.VEHICLE_LAST_UPDATE: 0,
            sc.VEHICLE_STATUS: {},
            sc.VEHICLE_FEATURES: vehicle[sc.VEHICLE_FEATURES],
            sc.VEHICLE_SUBSCRIPTION_FEATURES: vehicle[sc.VEHICLE_SUBSCRIPTION_FEATURES],
            sc.VEHICLE_SUBSCRIPTION_STATUS: vehicle[sc.VEHICLE_SUBSCRIPTION_STATUS],
        }

    async def _remote_query(self, vin, cmd, data=None):
        await self._connection.validate_session(vin)
        api_gen = self.get_api_gen(vin)
        async with self._vehicles[vin][sc.VEHICLE_LOCK]:
            js_resp = await self._get(cmd.replace("api_gen", api_gen), json_data=data)
            _LOGGER.debug(pprint.pformat(js_resp))
            if js_resp["success"]:
                return js_resp
            if js_resp.get("errorCode") == sc.SOA_UNABLE_TO_PARSE:
                _LOGGER.warning("SOA 403 error - clearing session cookie")
                self._connection.reset_session()
            else:
                raise SubaruException("Remote query failed. Response: %s " % js_resp)

    async def _remote_command(self, vin, cmd, data=None, poll_url=sc.API_REMOTE_SVC_STATUS):
        if not self._pin_lockout:
            await self._connection.validate_session(vin)
            api_gen = self.get_api_gen(vin)
            form_data = {"pin": self._pin}
            if data:
                form_data.update(data)
            req_id = ""
            async with self._vehicles[vin][sc.VEHICLE_LOCK]:
                js_resp = await self._post(cmd.replace("api_gen", api_gen), json_data=form_data)
                _LOGGER.debug(pprint.pformat(js_resp))
                if js_resp["success"]:
                    req_id = js_resp["data"][sc.SERVICE_REQ_ID]
                    return await self._wait_request_status(req_id, api_gen, poll_url)
                if js_resp["errorCode"] == sc.INVALID_CREDENTIALS:
                    self._pin_lockout = True
                    raise InvalidPIN("Invalid PIN! %s" % js_resp["data"]["errorDescription"])
                if js_resp["errorCode"] == sc.SERVICE_ALREADY_STARTED:
                    return False, None
                if js_resp["errorCode"] == sc.SOA_UNABLE_TO_PARSE:
                    self._connection.reset_session()
                    return False, None
                raise SubaruException("Remote command failed.  Response: %s " % js_resp)
        raise PINLockoutProtect("Remote command with invalid PIN cancelled to prevent account lockout")

    async def _actuate(self, vin, cmd, data=None):
        form_data = {"delay": 0, "vin": vin}
        if data:
            form_data.update(data)
        if self.get_remote_status(vin):
            return await self._remote_command(vin, cmd, data=form_data)
        raise SubaruException("Command requires REMOTE subscription.")

    async def _get_vehicle_status(self, vin):
        await self._connection.validate_session(vin)
        js_resp = await self._get(sc.API_VEHICLE_STATUS)
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
                self._vehicles[vin][sc.VEHICLE_STATUS].update(status)

            elif js_resp.get("errorCode") == sc.SOA_UNABLE_TO_PARSE:
                _LOGGER.warning("SOA 403 error - clearing session cookie")
                self._connection.reset_session()
            else:
                raise SubaruException("Error fetching vehicle status %s" % pprint.pformat(js_resp))
        else:
            raise SubaruException("Safety Plus subscription required for this vehicle")

        # Additional Data (Security Plus Required)
        if self.get_remote_status(vin):
            js_resp = await self._remote_query(vin, sc.API_CONDITION)
            if js_resp.get("success") and js_resp.get("data"):
                status = await self._cleanup_condition(js_resp, vin)
                self._vehicles[vin][sc.VEHICLE_STATUS].update(status)

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
            if self.get_api_gen(vin) == sc.FEATURE_G2_TELEMATICS:
                url = sc.API_G2_LOCATE_UPDATE
                poll_url = sc.API_G2_LOCATE_STATUS
            else:
                url = sc.API_G1_LOCATE_UPDATE
                poll_url = sc.API_G1_LOCATE_STATUS
            success, js_resp = await self._remote_command(vin, url, poll_url=poll_url)
        else:
            # Reports the last location the vehicle has reported to Subaru
            js_resp = await self._remote_query(vin, sc.API_LOCATE)
            success = js_resp["success"]

        if success and js_resp.get("success"):
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.LONGITUDE] = js_resp["data"]["result"][sc.LONGITUDE]
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.LATITUDE] = js_resp["data"]["result"][sc.LATITUDE]
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.HEADING] = js_resp["data"]["result"][sc.HEADING]
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
                _LOGGER.error(
                    "Remote service request completed but failed: %s Error: %s", req_id, js_resp["data"]["errorCode"],
                )
                return False, js_resp
            elif js_resp["data"].get("remoteServiceState") == "started":
                _LOGGER.info(
                    "Subaru API reports remote service request is in progress: %s", req_id,
                )
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
            if form_data[sc.REAR_DEFROST] not in [
                sc.REAR_DEFROST_OFF,
                sc.REAR_DEFROST_ON,
            ]:
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
            if self.get_ev_status(vin):
                form_data[sc.START_CONFIG] = sc.START_CONFIG_DEFAULT_EV
            elif self.get_res_status(vin):
                form_data[sc.START_CONFIG] = sc.START_CONFIG_DEFAULT_RES
            else:
                raise SubaruException("Vehicle Remote Start not supported.")

            return is_valid

        except KeyError:
            return None
