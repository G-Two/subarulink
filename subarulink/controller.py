#  SPDX-License-Identifier: Apache-2.0
"""
Provides managed controller interface to Subaru Starlink mobile app API via `subarulink.connection`.

For more details, please refer to the documentation at https://github.com/G-Two/subarulink
"""
import asyncio
from datetime import datetime
import json
import logging
import pprint
import time

from subarulink.connection import Connection
import subarulink.const as sc
from subarulink.const import FEATURE_G2_TELEMATICS
from subarulink.exceptions import InvalidPIN, PINLockoutProtect, SubaruException

_LOGGER = logging.getLogger(__name__)


class Controller:
    """Controller to interact with Subaru Starlink mobile app API."""

    def __init__(
        self,
        websession,
        username,
        password,
        device_id,
        pin,
        device_name,
        update_interval=sc.DEFAULT_UPDATE_INTERVAL,
        fetch_interval=sc.DEFAULT_FETCH_INTERVAL,
    ):
        """Initialize controller.

        Args:
            websession (aiohttp.ClientSession): An instance of aiohttp.ClientSession.
            username (str): Username used for the MySubaru mobile app.
            password (str): Password used for the MySubaru mobile app.
            device_id (str): Alphanumeric designator that Subaru API uses to track individual device authorization.
            pin (str): 4 digit pin number required to send remote vehicle commands.
            device_name (str): Human friendly name that is associated with `device_id` (shows on mysubaru.com profile "devices").
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

    async def connect(self, test_login=False):
        """
        Connect to Subaru Remote Services API.

        Args:
            test_login (bool, optional): If `True` then username/password is verified only.

        Returns:
            bool: `True` if success, `False` if failure

        Raises:
            InvalidCredentials: If login credentials are incorrect.
            IncompleteCredentials: If login credentials were not provided.
            SubaruException: If authorization and registration sequence fails for any other reason.
        """
        _LOGGER.debug("Connecting controller to Subaru Remote Services")
        vehicle_list = await self._connection.connect(test_login=test_login)
        if vehicle_list is None:
            raise SubaruException("Connection to Subaru API failed")

        if not test_login:
            for vehicle in vehicle_list:
                self._parse_vehicle(vehicle)
                _LOGGER.debug("Subaru Remote Services Ready!")

        return True

    async def test_pin(self):
        """
        Tests if stored PIN is valid for Remote Services.

        Returns:
            bool: `True` if PIN is correct. `False` if no vehicle with remote capability exists in account.

        Raises:
            InvalidPIN: If PIN is incorrect.
            SubaruException: If other failure occurs.
        """
        _LOGGER.info("Testing PIN for validity with Subaru remote services")
        for vin in self._vehicles:
            if self.get_remote_status(vin):
                await self._connection.validate_session(vin)
                api_gen = self.get_api_gen(vin)
                form_data = {"pin": self._pin}
                test_path = sc.API_G1_LOCATE_UPDATE if api_gen == sc.FEATURE_G1_TELEMATICS else sc.API_G2_LOCATE_UPDATE
                async with self._vehicles[vin][sc.VEHICLE_LOCK]:
                    js_resp = await self._post(test_path, json_data=form_data)
                    _LOGGER.debug(pprint.pformat(js_resp))
                    if js_resp["success"]:
                        _LOGGER.info("PIN is valid for Subaru remote services")
                        return True
        _LOGGER.info("No active vehicles with remote services subscription - PIN not required")
        return False

    def get_vehicles(self):
        """
        Return list of VINs available to user on Subaru Remote Services API.

        Returns:
            List: A list containing the VINs of all vehicles registered to the Subaru account.
        """
        return list(self._vehicles.keys())

    def get_ev_status(self, vin):
        """
        Get whether the specified VIN is an Electric Vehicle.

        Args:
            vin (str): The VIN to check.

        Returns:
            bool: `True` if `vin` is an Electric Vehicle, `False` if not.
            None: If `vin` is invalid.
        """
        vehicle = self._vehicles.get(vin.upper())
        status = None
        if vehicle:
            status = sc.FEATURE_PHEV in vehicle[sc.VEHICLE_FEATURES]
            _LOGGER.debug("Getting EV Status %s:%s", vin, status)
        return status

    def get_remote_status(self, vin):
        """
        Get whether the specified VIN has remote locks/horn/light service available.

        Args:
            vin (str): The VIN to check.

        Returns:
            bool: `True` if `vin` has remote capability and an active service plan, `False` if not.
            None: If `vin` is invalid.
        """
        vehicle = self._vehicles.get(vin.upper())
        status = None
        if vehicle:
            status = sc.FEATURE_REMOTE in vehicle[sc.VEHICLE_SUBSCRIPTION_FEATURES] and self.get_subscription_status(
                vin
            )
            _LOGGER.debug("Getting remote Status %s:%s", vin, status)
        return status

    def get_res_status(self, vin):
        """
        Get whether the specified VIN has remote engine start service available.

        Args:
            vin (str): The VIN to check.

        Returns:
            bool: `True` if `vin` has remote engine (or EV) start capability and an active service plan, `False` if not.
            None: If `vin` is invalid.
        """
        vehicle = self._vehicles.get(vin.upper())
        status = None
        if vehicle:
            status = sc.FEATURE_REMOTE_START in vehicle[sc.VEHICLE_FEATURES] and self.get_remote_status(vin)
            _LOGGER.debug("Getting RES Status %s:%s", vin, status)
        return status

    def get_safety_status(self, vin):
        """
        Get whether the specified VIN is has an active Starlink Safety Plus service plan.

        Args:
            vin (str): The VIN to check.

        Returns:
            bool: `True` if `vin` has an active Safety Plus service plan, `False` if not.
            None: If `vin` is invalid.
        """
        vehicle = self._vehicles.get(vin.upper())
        status = None
        if vehicle:
            status = sc.FEATURE_SAFETY in vehicle[sc.VEHICLE_SUBSCRIPTION_FEATURES] and self.get_subscription_status(
                vin
            )
            _LOGGER.debug("Getting Safety Plus Status %s:%s", vin, status)
        return status

    def get_subscription_status(self, vin):
        """
        Get whether the specified VIN has an active service plan.

        Args:
            vin (str): The VIN to check.

        Returns:
            bool: `True` if `vin` has an active service plan, `False` if not.
            None: If `vin` is invalid.
        """
        vehicle = self._vehicles.get(vin.upper())
        status = None
        if vehicle:
            status = vehicle[sc.VEHICLE_SUBSCRIPTION_STATUS] == sc.FEATURE_ACTIVE
            _LOGGER.debug("Getting subscription Status %s:%s", vin, status)
        return status

    def get_api_gen(self, vin):
        """
        Get the Subaru telematics API generation of a specified VIN.

        Args:
            vin (str): The VIN to check.

        Returns:
            str: `subarulink.const.FEATURE_G1_TELEMATICS` or `subarulink.const.FEATURE_G2_TELEMATICS`
            None: If `vin` is invalid.
        """
        vehicle = self._vehicles.get(vin.upper())
        result = None
        if vehicle:
            if sc.FEATURE_G1_TELEMATICS in vehicle[sc.VEHICLE_FEATURES]:
                result = sc.FEATURE_G1_TELEMATICS
            if sc.FEATURE_G2_TELEMATICS in vehicle[sc.VEHICLE_FEATURES]:
                result = sc.FEATURE_G2_TELEMATICS
            _LOGGER.debug("Getting vehicle API gen %s:%s", vin, result)
        return result

    def vin_to_name(self, vin):
        """
        Get the nickname of a specified VIN.

        Args:
            vin (str): The VIN to check.

        Returns:
            str: Display name associated with `vin`
            None: If `vin` is invalid.
        """
        vehicle = self._vehicles.get(vin.upper())
        result = None
        if vehicle:
            result = vehicle[sc.VEHICLE_NAME]
        return result

    async def get_data(self, vin):
        """
        Get locally cached vehicle data.  Fetch from Subaru API if not present.

        Args:
            vin (str): The VIN to get.

        Returns:
            dict: Vehicle information.
            None: If `vin` is invalid.

        Raises:
            SubaruException: If fetch operation fails.
        """
        vehicle = self._vehicles.get(vin.upper())
        result = None
        if vehicle:
            if len(vehicle.get(sc.VEHICLE_STATUS)) == 0:
                await self.fetch(vin)
            result = self._vehicles[vin.upper()]
        return result

    async def get_climate_settings(self, vin):
        """
        Fetch saved climate control settings from Subaru API.

        Args:
            vin (str): The VIN to get.

        Returns:
            bool: `True` upon success. Settings are not returned by this function. Use `get_data()` to retrieve.
            None: If `vin` is invalid.

        Raises:
            SubaruException: If failure prevents a valid response from being received.
        """
        vin = vin.upper()
        if self.get_res_status(vin) or self.get_ev_status(vin):
            await self._connection.validate_session(vin)
            js_resp = await self._get(sc.API_G2_FETCH_CLIMATE_SETTINGS)
            _LOGGER.debug(js_resp)
            self._vehicles[vin]["climate"] = json.loads(js_resp["data"])
            return True

    async def save_climate_settings(self, vin, form_data):
        """
        Save climate control settings to Subaru.

        Args:
            vin (str): The VIN to save climate settings to.
            form_data (dict): Climate settings to save.

        Returns:
            bool: `True` upon success. Settings are not returned by this function. Use `get_data()` to retrieve.
            None: If `vin` is invalid, unsupported, or climate settings invalid.

        Raises:
            SubaruException: If failure prevents a valid response from being received.
        """
        vin = vin.upper()
        if self.get_res_status(vin) or self.get_ev_status(vin):
            if self._validate_remote_start_params(vin, form_data):
                await self._connection.validate_session(vin)
                js_resp = await self._post(sc.API_G2_SAVE_CLIMATE_SETTINGS, json_data=form_data)
                _LOGGER.debug(js_resp)
                self._vehicles[vin]["climate"] = js_resp["data"]
                _LOGGER.info("Climate control settings saved.")
                return True

    async def fetch(self, vin, force=False):
        """
        Fetch latest vehicle status data cached on Subaru servers.

        Args:
            vin (str): The VIN to fetch.
            force (bool, optional): Override `fetch_interval` value and force a query.

        Returns:
            bool: `True` upon success. Status is not returned by this function. Use `get_data()` to retrieve.
            None: If `vin` is invalid, unsupported, or `fetch_interval` not met.

        Raises:
            SubaruException: If failure prevents a valid response from being received.
        """
        vin = vin.upper()
        if self.get_safety_status(vin):
            async with self._controller_lock:
                last_fetch = self.get_last_fetch_time(vin)
                cur_time = time.time()
                if force or cur_time - last_fetch > self._fetch_interval:
                    result = await self._fetch_status(vin)
                    self._vehicles[vin][sc.VEHICLE_LAST_FETCH] = cur_time
                    return result

    async def update(self, vin, force=False):
        """
        Initiate remote service command to update vehicle status.

        Args:
            vin (str): The VIN to update.
            force (bool, optional): Override `update_interval` value and force a query.

        Returns:
            bool: `True` upon success. Status is not returned by this function. Use `fetch()` then `get_data()` to retrieve.
            None: If `vin` is invalid, unsupported, or `update_interval` not met.

        Raises:
            SubaruException: If failure prevents a valid response from being received.
        """
        vin = vin.upper()
        if self.get_remote_status(vin):
            async with self._controller_lock:
                last_update = self.get_last_update_time(vin)
                cur_time = time.time()
                if force or cur_time - last_update > self._update_interval:
                    result = await self._locate(vin, hard_poll=True)
                    self._vehicles[vin][sc.VEHICLE_LAST_UPDATE] = cur_time
                    return result

    def get_update_interval(self):
        """Get current update interval."""
        return self._update_interval

    def set_update_interval(self, value):
        """
        Set new update interval.

        Args:
            value (int): New update interval in seconds.

        Returns:
            bool: `True` if update succeeded, `False` if update failed.
        """
        old_interval = self._update_interval
        if value >= 300:
            self._update_interval = value
            _LOGGER.debug("Update interval changed from %s to %s", old_interval, value)
            return True

        _LOGGER.error("Invalid update interval %s. Keeping old value: %s", value, old_interval)
        return False

    def get_fetch_interval(self):
        """Get current fetch interval."""
        return self._fetch_interval

    def set_fetch_interval(self, value):
        """
        Set new fetch interval.

        Args:
            value (int): New fetch interval in seconds.

        Returns:
            bool: `True` if update succeeded, `False` if update failed.
        """
        old_interval = self._fetch_interval
        if value >= 60:
            self._fetch_interval = value
            _LOGGER.debug("Fetch interval changed from %s to %s", old_interval, value)
            return True

        _LOGGER.error("Invalid fetch interval %s. Keeping old value: %s", value, old_interval)
        return False

    def get_last_fetch_time(self, vin):
        """
        Get last time data was fetched for a specific VIN.

        Args:
            vin (str): VIN to check.

        Returns:
            float:  timestamp of last update()
            None: if `vin` is invalid.
        """
        result = None
        vehicle = self._vehicles.get(vin.upper())
        if vehicle:
            result = vehicle[sc.VEHICLE_LAST_FETCH]
        return result

    def get_last_update_time(self, vin):
        """
        Get last time update remote command was used on a specific VIN.

        Args:
            vin (str): VIN to check.

        Returns:
            float:  timestamp of last update()
            None: if `vin` is invalid.
        """
        result = None
        vehicle = self._vehicles.get(vin.upper())
        if vehicle:
            result = vehicle[sc.VEHICLE_LAST_UPDATE]
        return result

    async def charge_start(self, vin):
        """
        Send command to start EV charging.

        Args:
            vin (str): Destination VIN for command.

        Returns:
            bool: `True` upon success.  `False` upon failure.

        Raises:
            InvalidPIN: if PIN is incorrect.
            SubaruException: for all other failures.
        """
        success, _ = await self._remote_command(vin.upper(), sc.API_EV_CHARGE_NOW)
        return success

    async def lock(self, vin):
        """
        Send command to lock doors.

        Args:
            vin (str): Destination VIN for command.

        Returns:
            bool: `True` upon success.  `False` upon failure.

        Raises:
            InvalidPIN: if PIN is incorrect.
            SubaruException: for all other failures.
        """
        form_data = {"forceKeyInCar": False}
        success, _ = await self._actuate(vin.upper(), sc.API_LOCK, data=form_data)
        return success

    async def unlock(self, vin, only_driver=True):
        """
        Send command to unlock doors.

        Args:
            vin (str): Destination VIN for command.
            only_driver (bool, optional): Only unlock driver's door if `True`.

        Returns:
            bool: `True` upon success.  `False` upon failure.

        Raises:
            InvalidPIN: if PIN is incorrect.
            SubaruException: for all other failures.
        """
        door = sc.ALL_DOORS
        if only_driver:
            door = sc.DRIVERS_DOOR
        form_data = {sc.WHICH_DOOR: door}
        success, _ = await self._actuate(vin.upper(), sc.API_UNLOCK, data=form_data)
        return success

    async def lights(self, vin):
        """
        Send command to flash lights.

        Args:
            vin (str): Destination VIN for command.

        Returns:
            bool: `True` upon success.  `False` upon failure.

        Raises:
            InvalidPIN: if PIN is incorrect.
            SubaruException: for all other failures.
        """
        success, _ = await self._actuate(vin.upper(), sc.API_LIGHTS)
        return success

    async def horn(self, vin):
        """
        Send command to sound horn.

        Args:
            vin (str): Destination VIN for command.

        Returns:
            bool: `True` upon success.  `False` upon failure.

        Raises:
            InvalidPIN: if PIN is incorrect.
            SubaruException: for all other failures.
        """
        success, _ = await self._actuate(vin.upper(), sc.API_HORN_LIGHTS)
        return success

    async def remote_stop(self, vin):
        """
        Send command to stop engine.

        Args:
            vin (str): Destination VIN for command.

        Returns:
            bool: `True` upon success.  `False` upon failure.

        Raises:
            InvalidPIN: if PIN is incorrect.
            SubaruException: for all other failures.
        """
        success, _ = await self._actuate(vin.upper(), sc.API_G2_REMOTE_ENGINE_STOP)
        return success

    async def remote_start(self, vin, form_data=None):
        """
        Send command to start engine.

        Args:
            vin (str): Destination VIN for command.
            form_data (dict, optional): Climate control settings

        Returns:
            bool: `True` upon success.  `False` upon failure.

        Raises:
            InvalidPIN: if PIN is incorrect.
            SubaruException: for all other failures.
        """
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
        raise SubaruException("Remote Start not supported for this vehicle")

    def invalid_pin_entered(self):
        """Return if invalid PIN error was received, thus locking out further remote commands."""
        return self._pin_lockout

    def update_saved_pin(self, new_pin):
        """
        Update the saved PIN used by the controller.

        Args:
            new_pin (str): New 4 digit PIN.

        Returns:
            bool: `True` if PIN was updated, otherwise `False`
        """
        if new_pin != self._pin:
            self._pin = new_pin
            self._pin_lockout = False
            return True
        return False

    async def _get(self, url, params=None):
        js_resp = await self._connection.get(url, params)
        self._check_error_code(js_resp)
        return js_resp

    async def _post(self, url, params=None, json_data=None):
        js_resp = await self._connection.post(url, params, json_data)
        self._check_error_code(js_resp)
        return js_resp

    def _check_error_code(self, js_resp):
        error = js_resp.get("errorCode")
        if error == sc.ERROR_SOA_403:
            _LOGGER.debug("SOA 403 error - clearing session cookie")
            self._connection.reset_session()
        elif error == sc.ERROR_INVALID_CREDENTIALS:
            _LOGGER.error("PIN is not valid for Subaru remote services")
            self._pin_lockout = True
            raise InvalidPIN("Invalid PIN! %s" % js_resp["data"]["errorDescription"])
        elif error == sc.ERROR_SERVICE_ALREADY_STARTED:
            pass
        elif error:
            _LOGGER.error("Unhandled API error code %s", error)
            raise SubaruException("Unhandled API error: {} - {}".format(error, js_resp["data"]["errorDescription"]))

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

    async def _remote_query(self, vin, cmd):
        tries_left = 2
        js_resp = None
        while tries_left > 0:
            await self._connection.validate_session(vin)
            api_gen = self.get_api_gen(vin)
            async with self._vehicles[vin][sc.VEHICLE_LOCK]:
                js_resp = await self._get(cmd.replace("api_gen", api_gen))
                _LOGGER.debug(pprint.pformat(js_resp))
                if js_resp["success"]:
                    return js_resp
                if js_resp["errorCode"] == sc.ERROR_SOA_403:
                    tries_left -= 1
                else:
                    tries_left = 0
        raise SubaruException("Remote query failed. Response: %s " % js_resp)

    async def _remote_command(self, vin, cmd, data=None, poll_url=sc.API_REMOTE_SVC_STATUS):
        try_again = True
        while try_again:
            if not self._pin_lockout:
                await self._connection.validate_session(vin)
                async with self._vehicles[vin][sc.VEHICLE_LOCK]:
                    try_again, success, js_resp = await self._execute_remote_command(vin, cmd, data, poll_url)
                    if success:
                        return success, js_resp
            else:
                raise PINLockoutProtect("Remote command with invalid PIN cancelled to prevent account lockout")
        return False, None

    async def _execute_remote_command(self, vin, cmd, data, poll_url):
        try_again = False
        success = None
        api_gen = self.get_api_gen(vin)
        form_data = {"pin": self._pin}
        if data:
            form_data.update(data)
        js_resp = await self._post(cmd.replace("api_gen", api_gen), json_data=form_data)
        _LOGGER.debug(pprint.pformat(js_resp))
        if api_gen == FEATURE_G2_TELEMATICS:
            if js_resp["errorCode"] == sc.ERROR_SOA_403:
                try_again = True
            if js_resp["success"]:
                req_id = js_resp["data"][sc.SERVICE_REQ_ID]
                success, js_resp = await self._wait_request_status_g2(req_id, poll_url)
        else:
            if js_resp.get(sc.SERVICE_REQ_ID):
                req_id = js_resp[sc.SERVICE_REQ_ID]
                success, js_resp = await self._wait_request_status_g1(req_id, poll_url)
        return try_again, success, js_resp

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
        _LOGGER.debug("Fetching vehicle status from Subaru")
        js_resp = await self._get_vehicle_status(vin)
        if js_resp.get("success") and js_resp.get("data"):
            data = js_resp["data"]
            old_status = self._vehicles[vin][sc.VEHICLE_STATUS]
            status = {}

            # These values seem to always be valid
            status[sc.ODOMETER] = data.get(sc.VS_ODOMETER)
            status[sc.TIMESTAMP] = data.get(sc.VS_TIMESTAMP) / 1000
            status[sc.AVG_FUEL_CONSUMPTION] = data.get(sc.VS_AVG_FUEL_CONSUMPTION)
            status[sc.DIST_TO_EMPTY] = data.get(sc.VS_DIST_TO_EMPTY)
            status[sc.VEHICLE_STATE] = data.get(sc.VS_VEHICLE_STATE)

            # Tire pressure is either valid or None.  If None and we have a previous value, keep previous, otherwise 0.
            status[sc.TIRE_PRESSURE_FL] = int(
                data.get(sc.VS_TIRE_PRESSURE_FL) or (old_status.get(sc.TIRE_PRESSURE_FL) or 0)
            )
            status[sc.TIRE_PRESSURE_FR] = int(
                data.get(sc.VS_TIRE_PRESSURE_FR) or (old_status.get(sc.TIRE_PRESSURE_FL) or 0)
            )
            status[sc.TIRE_PRESSURE_RL] = int(
                data.get(sc.VS_TIRE_PRESSURE_RL) or (old_status.get(sc.TIRE_PRESSURE_FL) or 0)
            )
            status[sc.TIRE_PRESSURE_RR] = int(
                data.get(sc.VS_TIRE_PRESSURE_RR) or (old_status.get(sc.TIRE_PRESSURE_FL) or 0)
            )

            # Not sure if these fields are ever valid (or even appear) for non security plus subscribers.  They are always garbage on Crosstrek PHEV.
            if not self.get_remote_status(vin):
                status[sc.LONGITUDE] = data.get(sc.VS_LONGITUDE)
                status[sc.LATITUDE] = data.get(sc.VS_LATITUDE)
                status[sc.HEADING] = data.get(sc.VS_HEADING)
                status[sc.LOCATION_VALID] = True
                if status[sc.LONGITUDE] in [sc.BAD_LONGITUDE, None] and status[sc.LATITUDE] in [
                    sc.BAD_LATITUDE,
                    None,
                ]:
                    status[sc.LOCATION_VALID] = False

            self._vehicles[vin][sc.VEHICLE_STATUS].update(status)

        # Additional Data (Security Plus Required)
        if self.get_remote_status(vin):
            js_resp = await self._remote_query(vin, sc.API_CONDITION)
            if js_resp.get("success") and js_resp.get("data"):
                status = await self._cleanup_condition(js_resp, vin)
                self._vehicles[vin][sc.VEHICLE_STATUS].update(status)

        return True

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
        except KeyError:  # Once in a while a 'value' key or some other field is missing
            pass

        if self.get_ev_status(vin):
            if int(data.get(sc.EV_DISTANCE_TO_EMPTY) or 0) > 20:
                # This value is incorrectly high immediately after car shutdown
                data.pop(sc.EV_DISTANCE_TO_EMPTY)
            if int(data.get(sc.EV_TIME_TO_FULLY_CHARGED) or sc.BAD_EV_TIME_TO_FULLY_CHARGED) == int(
                sc.BAD_EV_TIME_TO_FULLY_CHARGED
            ):
                # Value is None or known erroneous number
                data[sc.EV_TIME_TO_FULLY_CHARGED] = 0
            # Value is correct unless it is None
            data[sc.EV_DISTANCE_TO_EMPTY] = int(data.get(sc.EV_DISTANCE_TO_EMPTY) or 0)

        # Obtain lat/long from a more reliable source for Security Plus subscribers
        await self._locate(vin)
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
            success = js_resp.get("success")

        if success and js_resp.get("success"):
            self._parse_location(vin, js_resp["data"]["result"])
            return True
        if success and js_resp.get("status"):
            self._parse_location(vin, js_resp["result"])
            return True

    def _parse_location(self, vin, result):
        if result[sc.LONGITUDE] == sc.BAD_LONGITUDE and result[sc.LATITUDE] == sc.BAD_LATITUDE:
            # After car shutdown, some vehicles will push an update to Subaru with an invalid location. In this case keep previous and set flag so app knows to request update.
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.LONGITUDE] = self._vehicles[vin][sc.VEHICLE_STATUS].get(
                sc.LONGITUDE
            )
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.LATITUDE] = self._vehicles[vin][sc.VEHICLE_STATUS].get(
                sc.LATITUDE
            )
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.HEADING] = self._vehicles[vin][sc.VEHICLE_STATUS].get(sc.HEADING)
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.LOCATION_VALID] = False
        else:
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.LONGITUDE] = result.get(sc.LONGITUDE)
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.LATITUDE] = result.get(sc.LATITUDE)
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.HEADING] = result.get(sc.HEADING)
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.LOCATION_VALID] = True

    async def _wait_request_status_g2(self, req_id, poll_url, attempts=20):
        params = {sc.SERVICE_REQ_ID: req_id}
        attempts_left = attempts
        _LOGGER.debug("Polling for remote service request completion: serviceRequestId=%s", req_id)
        while attempts_left > 0:
            js_resp = await self._get(poll_url.replace("api_gen", sc.FEATURE_G2_TELEMATICS), params=params)
            _LOGGER.debug(pprint.pformat(js_resp))
            if js_resp["data"]["remoteServiceState"] == "finished":
                if js_resp["data"]["success"]:
                    _LOGGER.info("Remote service request completed successfully: %s", req_id)
                    return True, js_resp
                _LOGGER.error(
                    "Remote service request completed but failed: %s Error: %s", req_id, js_resp["data"]["errorCode"],
                )
                return False, js_resp
            if js_resp["data"].get("remoteServiceState") == "started":
                _LOGGER.info(
                    "Subaru API reports remote service request is in progress: %s", req_id,
                )
                attempts_left -= 1
                await asyncio.sleep(2)
                continue
        _LOGGER.error("Remote service request completion message not received")
        return False, None

    async def _wait_request_status_g1(self, req_id, poll_url, attempts=20):
        params = {sc.SERVICE_REQ_ID: req_id}
        attempts_left = attempts
        _LOGGER.debug("Polling for remote service request completion: serviceRequestId=%s", req_id)
        while attempts_left > 0:
            js_resp = await self._get(poll_url.replace("api_gen", sc.FEATURE_G1_TELEMATICS), params=params)
            _LOGGER.debug(pprint.pformat(js_resp))
            if js_resp["status"] == "SUCCESS":
                _LOGGER.info("Remote service request completed successfully: %s", req_id)
                return True, js_resp
            if js_resp["status"] == "PENDING":
                _LOGGER.info(
                    "Subaru API reports remote service request is in progress: %s", req_id,
                )
                attempts_left -= 1
                await asyncio.sleep(2)
                continue
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

            return is_valid

        except KeyError:
            return None
