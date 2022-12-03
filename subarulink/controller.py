#  SPDX-License-Identifier: Apache-2.0
"""
Provides managed controller interface to Subaru Starlink mobile app API via `subarulink.connection`.

For more details, please refer to the documentation at https://github.com/G-Two/subarulink
"""
import asyncio
from datetime import datetime, timedelta
import json
import logging
import pprint
import time

import subarulink
from subarulink.connection import Connection
import subarulink.const as sc
from subarulink.exceptions import (
    InvalidPIN,
    PINLockoutProtect,
    RemoteServiceFailure,
    SubaruException,
    VehicleNotSupported,
)

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
        country=sc.COUNTRY_USA,
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
            country (str): Country for MySubaru Account [CAN, USA].
            update_interval (int, optional): Seconds between requests for vehicle send update
            fetch_interval (int, optional): Seconds between fetches of Subaru's cached vehicle information

        """
        self._connection = Connection(websession, username, password, device_id, device_name, country)
        self._country = country
        self._update_interval = update_interval
        self._fetch_interval = fetch_interval
        self._vehicles = {}
        self._vehicle_asyncio_lock = {}
        self._pin = pin
        self._controller_lock = asyncio.Lock()
        self._pin_lockout = False
        self.version = subarulink.__version__

    async def connect(self):
        """
        Connect to Subaru Remote Services API.

        Returns:
            bool: `True` if success, `False` if failure

        Raises:
            InvalidCredentials: If login credentials are incorrect.
            IncompleteCredentials: If login credentials were not provided.
            SubaruException: If authorization and registration sequence fails for any other reason.
        """
        _LOGGER.debug("subarulink %s", self.version)
        _LOGGER.debug("Connecting controller to Subaru Remote Services")
        vehicle_list = await self._connection.connect()

        if len(vehicle_list) > 0:
            for vehicle in vehicle_list:
                self._parse_vehicle(vehicle)
            _LOGGER.debug("Subaru Remote Services Ready")
            return True

        _LOGGER.debug("No vehicles found, nothing to do")
        return False

    @property
    def device_registered(self):
        """Device is registered."""
        return self._connection.device_registered

    @property
    def contact_methods(self):
        """Email address for 2FA."""
        return self._connection.auth_contact_methods

    async def request_auth_code(self, contact_method):
        """Request 2FA code be sent via email."""
        return await self._connection.request_auth_code(contact_method)

    async def submit_auth_code(self, code):
        """Submit received 2FA code for validation."""
        return await self._connection.submit_auth_code(code)

    def is_pin_required(self):
        """
        Return if a vehicle with an active remote service subscription exists.

        Returns:
            bool: `True` if PIN is required. `False` if PIN not required.
        """
        for vin in self._vehicles:
            if self.get_remote_status(vin):
                return True
        return False

    async def test_pin(self):
        """
        Test if stored PIN is valid for Remote Services.

        Returns:
            bool: `True` if PIN is correct. `False` if no vehicle with remote capability exists in account.

        Raises:
            InvalidPIN: If PIN is incorrect.
            SubaruException: If other failure occurs.
        """
        _LOGGER.info("Testing PIN for validity with Subaru remote services")
        for vin, _ in self._vehicles.items():
            if self.get_remote_status(vin):
                await self._connection.validate_session(vin)
                api_gen = self.get_api_gen(vin)
                form_data = {"pin": self._pin, "vin": vin, "delay": 0}
                test_path = sc.API_G1_LOCATE_UPDATE if api_gen == sc.FEATURE_G1_TELEMATICS else sc.API_G2_LOCATE_UPDATE
                async with self._vehicle_asyncio_lock[vin]:
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

    def get_model_year(self, vin):
        """
        Get model year for the specified VIN.

        Args:
            vin (str): The VIN to check.

        Returns:
            str: model year.
            None: If `vin` is invalid.
        """
        if isinstance(vehicle := self._vehicles.get(vin.upper()), dict):
            return vehicle.get(sc.VEHICLE_MODEL_YEAR)

    def get_model_name(self, vin):
        """
        Get model name for the specified VIN.

        Args:
            vin (str): The VIN to check.

        Returns:
            str: model name.
            None: If `vin` is invalid.
        """
        if isinstance(vehicle := self._vehicles.get(vin.upper()), dict):
            return vehicle.get(sc.VEHICLE_MODEL_NAME)

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

    async def list_climate_preset_names(self, vin):
        """
        Get list of climate control presets.

        Args:
            vin (str): The VIN of the vehicle.

        Returns:
            list: containing climate preset names.
            None: If `preset_name` not found.

        Raises:
            VehicleNotSupported: if vehicle/subscription not supported
        """
        self._validate_remote_capability(vin)
        if not self._vehicles[vin].get("climate"):
            await self._fetch_climate_presets(vin)
        return [i[sc.PRESET_NAME] for i in self._vehicles[vin]["climate"]]

    async def get_climate_preset_by_name(self, vin, preset_name):
        """
        Get climate control preset by name.

        Args:
            vin (str): The VIN of the vehicle.
            preset_name (str): Name of climate settings preset.

        Returns:
            dict: containing climate preset parameters.
            None: If `preset_name` not found.

        Raises:
            VehicleNotSupported: if vehicle/subscription not supported
        """
        self._validate_remote_capability(vin)
        if not self._vehicles[vin].get("climate"):
            await self._fetch_climate_presets(vin)
        for preset in self._vehicles[vin]["climate"]:
            if preset["name"] == preset_name:
                return preset

    async def get_user_climate_preset_data(self, vin):
        """
        Get user climate control preset data.

        Args:
            vin (str): The VIN of the vehicle.

        Returns:
            list: containing up to 4 climate preset data dicts.
            None: If `preset_name` not found.

        Raises:
            VehicleNotSupported: if vehicle/subscription not supported
        """
        self._validate_remote_capability(vin)
        if not self._vehicles[vin].get("climate"):
            await self._fetch_climate_presets(vin)
        return [i for i in self._vehicles[vin]["climate"] if i[sc.PRESET_TYPE] == sc.PRESET_TYPE_USER]

    async def delete_climate_preset_by_name(self, vin, preset_name):
        """
        Delete climate control user preset by name.

        Args:
            vin (str): The VIN of the vehicle.
            preset_name (str): Name of climate settings preset.

        Returns:
            bool: `True` if successful.

        Raises:
            SubaruException: if `preset_name` not found
            VehicleNotSupported: if vehicle/subscription not supported
        """
        self._validate_remote_capability(vin)
        preset = await self.get_climate_preset_by_name(vin, preset_name)
        if preset and preset["presetType"] == "userPreset":
            user_presets = [i for i in self._vehicles[vin]["climate"] if i["presetType"] == "userPreset"]
            user_presets.remove(preset)
            return await self.update_user_climate_presets(vin, user_presets)
        raise SubaruException(f"User preset name '{preset_name}' not found")

    async def update_user_climate_presets(self, vin, preset_data):
        """
        Save user defined climate control settings to Subaru.

        Args:
            vin (str): The VIN to save climate settings to.
            preset_data (list): List of Climate settings dicts to save.

        Returns:
            bool: `True` upon success.
            None: If `vin` is invalid or unsupported.

        Raises:
            SubaruException: If preset_data is invalid or fails to save.
            VehicleNotSupported: if vehicle/subscription not supported
        """
        self._validate_remote_capability(vin)
        if not self._vehicles[vin].get("climate"):
            await self._fetch_climate_presets(vin)
        if not isinstance(preset_data, list) and not isinstance(preset_data[0], dict):
            raise SubaruException("Preset data must be a list of climate settings dicts")
        if len(preset_data) > 4:
            raise SubaruException("Preset list may have a maximum of 4 entries")
        for preset in preset_data:
            self._validate_remote_start_params(vin, preset)
        await self._connection.validate_session(vin)
        js_resp = await self._post(sc.API_G2_SAVE_RES_SETTINGS, json_data=preset_data)
        _LOGGER.debug(js_resp)
        success = js_resp["success"]
        await self._fetch_climate_presets(vin)
        return success

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
        async with self._controller_lock:
            last_fetch = self.get_last_fetch_time(vin)
            cur_time = time.time()
            if force or cur_time - last_fetch > self._fetch_interval:
                result = await self._fetch_status(vin)
                self._vehicles[vin][sc.VEHICLE_LAST_FETCH] = datetime.utcfromtimestamp(cur_time)
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
            VehicleNotSupported: if vehicle/subscription not supported
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
        else:
            raise VehicleNotSupported("Active STARLINK Security Plus subscription required.")

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
            bool: `True` upon success.

        Raises:
            InvalidPIN: if PIN is incorrect
            PINLockoutProtect: if PIN was previously incorrect and was not updated
            RemoteServiceFailure: for failure after request submitted
            VehicleNotSupported: if vehicle/subscription not supported
            SubaruException: for other failures
        """
        if self.get_ev_status(vin):
            success, _ = await self._remote_command(vin.upper(), sc.API_EV_CHARGE_NOW, sc.API_REMOTE_SVC_STATUS)
            return success
        raise VehicleNotSupported("PHEV charging not supported for this vehicle")

    async def lock(self, vin):
        """
        Send command to lock doors.

        Args:
            vin (str): Destination VIN for command.

        Returns:
            bool: `True` upon success.

        Raises:
            InvalidPIN: if PIN is incorrect
            PINLockoutProtect: if PIN was previously incorrect and was not updated
            RemoteServiceFailure: for failure after request submitted
            VehicleNotSupported: if vehicle/subscription not supported
            SubaruException: for other failures
        """
        form_data = {"forceKeyInCar": False}
        success, _ = await self._actuate(vin, sc.API_LOCK, data=form_data)
        return success

    async def unlock(self, vin, door=sc.ALL_DOORS):
        """
        Send command to unlock doors.

        Args:
            vin (str): Destination VIN for command.
            door (str, optional): Specify door to unlock.

        Returns:
            bool: `True` upon success.

        Raises:
            InvalidPIN: if PIN is incorrect
            PINLockoutProtect: if PIN was previously incorrect and was not updated
            RemoteServiceFailure: for failure after request submitted
            VehicleNotSupported: if vehicle/subscription not supported
            SubaruException: for other failures
        """
        if door in sc.VALID_DOORS:
            form_data = {sc.WHICH_DOOR: door}
            success, _ = await self._actuate(vin.upper(), sc.API_UNLOCK, data=form_data)
            return success
        raise SubaruException(f"Invalid door '{door}' specified for unlock command")

    async def lights(self, vin):
        """
        Send command to flash lights.

        Args:
            vin (str): Destination VIN for command.

        Returns:
            bool: `True` upon success.

        Raises:
            InvalidPIN: if PIN is incorrect
            PINLockoutProtect: if PIN was previously incorrect and was not updated
            RemoteServiceFailure: for failure after request submitted
            VehicleNotSupported: if vehicle/subscription not supported
            SubaruException: for other failures
        """
        poll_url = sc.API_REMOTE_SVC_STATUS
        if self.get_api_gen(vin) == sc.FEATURE_G1_TELEMATICS:
            poll_url = sc.API_G1_HORN_LIGHTS_STATUS
        success, _ = await self._actuate(vin.upper(), sc.API_LIGHTS, poll_url=poll_url)
        return success

    async def lights_stop(self, vin):
        """
        Send command to stop flash lights.

        Args:
            vin (str): Destination VIN for command.

        Returns:
            bool: `True` upon success.

        Raises:
            InvalidPIN: if PIN is incorrect
            PINLockoutProtect: if PIN was previously incorrect and was not updated
            RemoteServiceFailure: for failure after request submitted
            VehicleNotSupported: if vehicle/subscription not supported
            SubaruException: for other failures
        """
        poll_url = sc.API_REMOTE_SVC_STATUS
        if self.get_api_gen(vin) == sc.FEATURE_G1_TELEMATICS:
            poll_url = sc.API_G1_HORN_LIGHTS_STATUS
        success, _ = await self._actuate(vin.upper(), sc.API_LIGHTS_STOP, poll_url=poll_url)
        return success

    async def horn(self, vin):
        """
        Send command to sound horn.

        Args:
            vin (str): Destination VIN for command.

        Returns:
            bool: `True` upon success.

        Raises:
            InvalidPIN: if PIN is incorrect
            PINLockoutProtect: if PIN was previously incorrect and was not updated
            RemoteServiceFailure: for failure after request submitted
            VehicleNotSupported: if vehicle/subscription not supported
            SubaruException: for other failures
        """
        poll_url = sc.API_REMOTE_SVC_STATUS
        if self.get_api_gen(vin) == sc.FEATURE_G1_TELEMATICS:
            poll_url = sc.API_G1_HORN_LIGHTS_STATUS
        success, _ = await self._actuate(vin.upper(), sc.API_HORN_LIGHTS, poll_url=poll_url)
        return success

    async def horn_stop(self, vin):
        """
        Send command to sound horn.

        Args:
            vin (str): Destination VIN for command.

        Returns:
            bool: `True` upon success.

        Raises:
            InvalidPIN: if PIN is incorrect
            PINLockoutProtect: if PIN was previously incorrect and was not updated
            RemoteServiceFailure: for failure after request submitted
            VehicleNotSupported: if vehicle/subscription not supported
            SubaruException: for other failures
        """
        poll_url = sc.API_REMOTE_SVC_STATUS
        if self.get_api_gen(vin) == sc.FEATURE_G1_TELEMATICS:
            poll_url = sc.API_G1_HORN_LIGHTS_STATUS
        success, _ = await self._actuate(vin.upper(), sc.API_HORN_LIGHTS_STOP, poll_url=poll_url)
        return success

    async def remote_stop(self, vin):
        """
        Send command to stop engine.

        Args:
            vin (str): Destination VIN for command.

        Returns:
            bool: `True` upon success.

        Raises:
            InvalidPIN: if PIN is incorrect
            PINLockoutProtect: if PIN was previously incorrect and was not updated
            RemoteServiceFailure: for failure after request submitted
            VehicleNotSupported: if vehicle/subscription not supported
            SubaruException: for other failures
        """
        if self.get_res_status(vin) or self.get_ev_status(vin):
            success, _ = await self._actuate(vin.upper(), sc.API_G2_REMOTE_ENGINE_STOP)
            return success
        raise VehicleNotSupported("Remote Start not supported for this vehicle")

    async def remote_start(self, vin, preset_name):
        """
        Send command to start engine and set climate control.

        Args:
            vin (str): Destination VIN for command.
            preset_name (str): Climate control preset name

        Returns:
            bool: `True` upon success.

        Raises:
            InvalidPIN: if PIN is incorrect
            PINLockoutProtect: if PIN was previously incorrect and was not updated
            RemoteServiceFailure: for failure after request submitted
            VehicleNotSupported: if vehicle/subscription not supported
            SubaruException: for other failures
        """
        self._validate_remote_capability(vin)
        preset_data = await self.get_climate_preset_by_name(vin, preset_name)
        if preset_data:
            js_resp = await self._post(sc.API_G2_SAVE_RES_QUICK_START_SETTINGS, json_data=preset_data)
            _LOGGER.debug(pprint.pprint(js_resp))
            if js_resp.get("success"):
                success, _ = await self._actuate(vin, sc.API_G2_REMOTE_ENGINE_START, data=preset_data)
                return success
            raise SubaruException(f"Climate preset '{preset_name}' failed: {js_resp}")
        raise SubaruException(f"Climate preset '{preset_name}' does not exist")

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
        if error in [sc.ERROR_SOA_403, sc.ERROR_INVALID_TOKEN]:
            _LOGGER.debug("SOA 403 error - clearing session cookie")
            self._connection.reset_session()
        elif error in [sc.ERROR_INVALID_CREDENTIALS, "SXM40006"]:
            _LOGGER.error("PIN is not valid for Subaru remote services")
            self._pin_lockout = True
            raise InvalidPIN("Invalid PIN! %s" % js_resp)
        elif error in [
            sc.ERROR_SERVICE_ALREADY_STARTED,
            sc.ERROR_G1_SERVICE_ALREADY_STARTED,
        ]:
            pass
        elif error:
            _LOGGER.error("Unhandled API error code %s", error)
            raise SubaruException(f"Unhandled API error: {error} - {js_resp}")

    def _parse_vehicle(self, vehicle):
        vin = vehicle["vin"].upper()
        _LOGGER.debug("Parsing vehicle: %s", vin)
        self._vehicle_asyncio_lock[vin] = asyncio.Lock()
        self._vehicles[vin] = {
            sc.VEHICLE_MODEL_YEAR: vehicle[sc.VEHICLE_MODEL_YEAR],
            sc.VEHICLE_MODEL_NAME: vehicle[sc.VEHICLE_MODEL_NAME],
            sc.VEHICLE_NAME: vehicle[sc.VEHICLE_NAME],
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
            async with self._vehicle_asyncio_lock[vin]:
                js_resp = await self._get(cmd.replace("api_gen", api_gen))
                _LOGGER.debug(pprint.pformat(js_resp))
                if js_resp["success"]:
                    return js_resp
                if js_resp["errorCode"] == sc.ERROR_SOA_403:
                    tries_left -= 1
                else:
                    tries_left = 0
        raise SubaruException("Remote query failed. Response: %s " % js_resp)

    async def _remote_command(self, vin, cmd, poll_url, data=None):
        try_again = True
        vin = vin.upper()
        while try_again:
            if not self._pin_lockout:
                # There is some sort of token expiration with the telematics provider that is checked after
                # a successful remote command is sent causing the status polling to fail and making it seem the
                # command failed. Workaround is to force a reauth before the command is issued.
                if self._connection.get_session_age() > sc.MAX_SESSION_AGE_MINS:
                    self._connection.reset_session()
                await self._connection.validate_session(vin)
                async with self._vehicle_asyncio_lock[vin]:
                    try_again, success, js_resp = await self._execute_remote_command(vin, cmd, data, poll_url)
                    if success:
                        return success, js_resp
            else:
                raise PINLockoutProtect("Remote command with invalid PIN cancelled to prevent account lockout")

    async def _execute_remote_command(self, vin, cmd, data, poll_url):
        try_again = False
        success = None
        api_gen = self.get_api_gen(vin)
        form_data = {"pin": self._pin, "delay": 0, "vin": vin}
        if data:
            form_data.update(data)
        js_resp = await self._post(cmd.replace("api_gen", api_gen), json_data=form_data)
        _LOGGER.debug(pprint.pformat(js_resp))
        if js_resp["errorCode"] == sc.ERROR_SOA_403:
            try_again = True
        if js_resp["errorCode"] in [
            sc.ERROR_G1_SERVICE_ALREADY_STARTED,
            sc.ERROR_SERVICE_ALREADY_STARTED,
        ]:
            await asyncio.sleep(10)
            try_again = True
        if js_resp["success"]:
            req_id = js_resp["data"][sc.SERVICE_REQ_ID]
            success, js_resp = await self._wait_request_status(vin, req_id, poll_url)
        return try_again, success, js_resp

    async def _actuate(self, vin, cmd, data=None, poll_url=sc.API_REMOTE_SVC_STATUS):
        form_data = {"delay": 0, "vin": vin}
        if data:
            form_data.update(data)
        if self.get_remote_status(vin):
            return await self._remote_command(vin, cmd, poll_url, data=form_data)
        raise VehicleNotSupported("Active STARLINK Security Plus subscription required.")

    async def _get_vehicle_status(self, vin):
        await self._connection.validate_session(vin)
        js_resp = await self._get(sc.API_VEHICLE_STATUS)
        _LOGGER.debug(pprint.pformat(js_resp))
        return js_resp

    async def _fetch_status(self, vin):
        _LOGGER.debug("Fetching vehicle status from Subaru")
        js_resp = await self._get_vehicle_status(vin)
        if js_resp.get("success") and js_resp.get("data"):
            status = self._parse_vehicle_status(js_resp, vin)
            self._vehicles[vin][sc.VEHICLE_STATUS].update(status)

        # Additional Data (Security Plus and Generation2 Required)
        if self.get_remote_status(vin) and self.get_api_gen(vin) == sc.FEATURE_G2_TELEMATICS:
            try:
                js_resp = await self._remote_query(vin, sc.API_CONDITION)
                if js_resp.get("success") and js_resp.get("data"):
                    status = self._parse_condition(js_resp, vin)
                    self._vehicles[vin][sc.VEHICLE_STATUS].update(status)

                # Obtain lat/long from a more reliable source for Security Plus g2
                await self._locate(vin)

            except SubaruException as err:
                if "HTTP 500" in err.message:
                    # This is a condition that intermittently occurs and appears to be caused by some sort of timeout on the Subaru backend
                    _LOGGER.warning("HTTP 500 received when fetching vehicle information from Subaru")
                    return False
                raise err

        # Fetch climate presets for supported vehicles
        if self.get_res_status(vin) or self.get_ev_status(vin):
            await self._fetch_climate_presets(vin)

        return True

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

    def _parse_location(self, vin, result):
        if result[sc.API_LONGITUDE] == sc.BAD_LONGITUDE and result[sc.API_LATITUDE] == sc.BAD_LATITUDE:
            # After car shutdown, some vehicles will push an update to Subaru with an invalid location. In this case keep previous and set flag so app knows to request update.
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.API_LONGITUDE] = self._vehicles[vin][sc.VEHICLE_STATUS].get(
                sc.API_LONGITUDE
            )
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.API_LATITUDE] = self._vehicles[vin][sc.VEHICLE_STATUS].get(
                sc.API_LATITUDE
            )
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.API_HEADING] = self._vehicles[vin][sc.VEHICLE_STATUS].get(
                sc.API_HEADING
            )
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.LOCATION_VALID] = False
        else:
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.API_LONGITUDE] = result.get(sc.API_LONGITUDE)
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.API_LATITUDE] = result.get(sc.API_LATITUDE)
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.API_HEADING] = result.get(sc.API_HEADING)
            self._vehicles[vin][sc.VEHICLE_STATUS][sc.LOCATION_VALID] = True

    async def _wait_request_status(self, vin, req_id, poll_url, attempts=20):
        params = {sc.SERVICE_REQ_ID: req_id}
        attempts_left = attempts
        _LOGGER.debug("Polling for remote service request completion: serviceRequestId=%s", req_id)
        while attempts_left > 0:
            js_resp = await self._get(poll_url.replace("api_gen", self.get_api_gen(vin)), params=params)
            _LOGGER.debug(pprint.pformat(js_resp))
            if js_resp["errorCode"] in [sc.ERROR_SOA_403, sc.ERROR_INVALID_TOKEN]:
                await self._connection.validate_session(vin)
                continue
            if js_resp["data"]["remoteServiceState"] == "finished":
                if js_resp["data"]["success"]:
                    _LOGGER.info("Remote service request completed successfully: %s", req_id)
                    return True, js_resp
                _LOGGER.error(
                    "Remote service request completed but failed: %s Error: %s",
                    req_id,
                    js_resp["data"]["errorCode"],
                )
                raise RemoteServiceFailure(
                    "Remote service request completed but failed: %s" % js_resp["data"]["errorCode"]
                )
            if js_resp["data"].get("remoteServiceState") == "started":
                _LOGGER.info(
                    "Subaru API reports remote service request is in progress: %s",
                    req_id,
                )
                attempts_left -= 1
                await asyncio.sleep(2)
                continue
        _LOGGER.error("Remote service request completion message never received")
        raise RemoteServiceFailure("Remote service request completion message never received")

    async def _fetch_climate_presets(self, vin):
        vin = vin.upper()
        if self.get_res_status(vin) or self.get_ev_status(vin):
            presets = []

            # Fetch STARLINK Presets
            js_resp = await self._get(sc.API_G2_FETCH_RES_SUBARU_PRESETS)
            _LOGGER.debug(pprint.pformat(js_resp))
            built_in_presets = [json.loads(i) for i in js_resp["data"]]
            for i in built_in_presets:
                if self.get_ev_status(vin) and i["vehicleType"] == "phev":
                    presets.append(i)
                elif not self.get_ev_status(vin) and i["vehicleType"] == "gas":
                    presets.append(i)

            # Fetch User Defined Presets
            js_resp = await self._get(sc.API_G2_FETCH_RES_USER_PRESETS)
            _LOGGER.debug(pprint.pformat(js_resp))
            data = js_resp["data"]  # data is None is user has not configured any presets
            if isinstance(data, str):
                for i in json.loads(data):
                    presets.append(i)

            self._vehicles[vin]["climate"] = presets
            return True
        raise VehicleNotSupported("Active STARLINK Security Plus subscription required.")

    def _validate_remote_start_params(self, vin, preset_data):
        is_valid = True
        err_msg = None
        try:
            for item in preset_data:
                if preset_data[item] not in sc.VALID_CLIMATE_OPTIONS[item]:
                    if item == "name" and isinstance(preset_data[item], str):
                        continue
                    is_valid = False
                    err_msg = f"Invalid value for {item}: {preset_data[item]}"
                    break
        except KeyError as err:
            is_valid = False
            err_msg = f"Invalid option: {err}"
        if not is_valid:
            raise SubaruException(err_msg)

        if self.get_ev_status(vin):
            preset_data.update(sc.START_CONFIG_CONSTS_EV)
        else:
            preset_data.update(sc.START_CONFIG_CONSTS_RES)
        return is_valid

    def _validate_remote_capability(self, vin):
        if not self.get_res_status(vin) and not self.get_ev_status(vin):
            raise VehicleNotSupported(
                "Active STARLINK Security Plus subscription and remote start capable vehicle required."
            )
        return True

    def _parse_vehicle_status(self, js_resp, vin):
        """Parse fields from vehicleStatus.json."""
        data = js_resp["data"]
        old_status = self._vehicles[vin][sc.VEHICLE_STATUS]
        status = {}

        # These values seem to always be valid
        status[sc.API_ODOMETER] = int(data.get(sc.API_ODOMETER))
        status[sc.API_TIMESTAMP] = datetime.strptime(data.get(sc.API_TIMESTAMP), sc.VS_TIMESTAMP_FMT)

        # These values are either valid or None. If None and we have a previous value, keep previous, otherwise 0.
        status[sc.API_AVG_FUEL_CONSUMPTION] = data.get(sc.API_AVG_FUEL_CONSUMPTION) or (
            old_status.get(sc.API_AVG_FUEL_CONSUMPTION) or 0
        )
        status[sc.API_DIST_TO_EMPTY] = data.get(sc.API_DIST_TO_EMPTY) or (old_status.get(sc.API_DIST_TO_EMPTY) or 0)
        status[sc.API_VEHICLE_STATE] = data.get(sc.API_VEHICLE_STATE) or old_status.get(sc.API_VEHICLE_STATE)

        # Tire pressure is either valid or None.  If None and we have a previous value, keep previous, otherwise 0.
        status[sc.API_TIRE_PRESSURE_FL] = int(
            data.get(sc.API_TIRE_PRESSURE_FL) or (old_status.get(sc.API_TIRE_PRESSURE_FL) or 0)
        )
        status[sc.API_TIRE_PRESSURE_FR] = int(
            data.get(sc.API_TIRE_PRESSURE_FR) or (old_status.get(sc.API_TIRE_PRESSURE_FR) or 0)
        )
        status[sc.API_TIRE_PRESSURE_RL] = int(
            data.get(sc.API_TIRE_PRESSURE_RL) or (old_status.get(sc.API_TIRE_PRESSURE_RL) or 0)
        )
        status[sc.API_TIRE_PRESSURE_RR] = int(
            data.get(sc.API_TIRE_PRESSURE_RR) or (old_status.get(sc.API_TIRE_PRESSURE_RR) or 0)
        )

        # Not sure if these fields are ever valid (or even appear) for non security plus subscribers.
        status[sc.LOCATION_VALID] = False
        if data.get(sc.API_LONGITUDE) not in [sc.BAD_LONGITUDE, None] and data.get(sc.API_LATITUDE) not in [
            sc.BAD_LATITUDE,
            None,
        ]:
            status[sc.API_LONGITUDE] = data.get(sc.API_LONGITUDE)
            status[sc.API_LATITUDE] = data.get(sc.API_LATITUDE)
            status[sc.API_HEADING] = int(data.get(sc.API_HEADING))
            status[sc.LOCATION_VALID] = True

        return status

    def _parse_condition(self, js_resp, vin):
        """Parse fields from condition/execute.json."""
        data = js_resp["data"]["result"]
        keep_data = {
            sc.API_DOOR_BOOT_POSITION: data[sc.API_DOOR_BOOT_POSITION],
            sc.API_DOOR_ENGINE_HOOD_POSITION: data[sc.API_DOOR_ENGINE_HOOD_POSITION],
            sc.API_DOOR_FRONT_LEFT_POSITION: data[sc.API_DOOR_FRONT_LEFT_POSITION],
            sc.API_DOOR_FRONT_RIGHT_POSITION: data[sc.API_DOOR_FRONT_RIGHT_POSITION],
            sc.API_DOOR_REAR_LEFT_POSITION: data[sc.API_DOOR_REAR_LEFT_POSITION],
            sc.API_DOOR_REAR_RIGHT_POSITION: data[sc.API_DOOR_REAR_RIGHT_POSITION],
            sc.API_REMAINING_FUEL_PERCENT: data[sc.API_REMAINING_FUEL_PERCENT],
            sc.API_LAST_UPDATED_DATE: data[sc.API_LAST_UPDATED_DATE],
            sc.API_WINDOW_FRONT_LEFT_STATUS: data[sc.API_WINDOW_FRONT_LEFT_STATUS],
            sc.API_WINDOW_FRONT_RIGHT_STATUS: data[sc.API_WINDOW_FRONT_RIGHT_STATUS],
            sc.API_WINDOW_REAR_LEFT_STATUS: data[sc.API_WINDOW_REAR_LEFT_STATUS],
            sc.API_WINDOW_REAR_RIGHT_STATUS: data[sc.API_WINDOW_REAR_RIGHT_STATUS],
            sc.API_WINDOW_SUNROOF_STATUS: data[sc.API_WINDOW_SUNROOF_STATUS],
        }
        keep_data[sc.API_TIMESTAMP] = datetime.strptime(data[sc.API_LAST_UPDATED_DATE], sc.TIMESTAMP_FMT)

        # Parse EV specific values
        if self.get_ev_status(vin):
            # Value is correct unless it is None
            keep_data[sc.API_EV_DISTANCE_TO_EMPTY] = int(data.get(sc.API_EV_DISTANCE_TO_EMPTY) or 0)
            keep_data[sc.API_EV_STATE_OF_CHARGE_PERCENT] = float(data.get(sc.API_EV_STATE_OF_CHARGE_PERCENT) or 0)
            keep_data[sc.API_EV_IS_PLUGGED_IN] = data.get(sc.API_EV_IS_PLUGGED_IN)
            keep_data[sc.API_EV_CHARGER_STATE_TYPE] = data.get(sc.API_EV_CHARGER_STATE_TYPE)
            keep_data[sc.API_EV_TIME_TO_FULLY_CHARGED] = data.get(sc.API_EV_TIME_TO_FULLY_CHARGED)

            if int(data.get(sc.API_EV_DISTANCE_TO_EMPTY) or 0) < 20:
                # This value is sometimes incorrectly high immediately after car shutdown
                keep_data[sc.API_EV_DISTANCE_TO_EMPTY] = data[sc.API_EV_DISTANCE_TO_EMPTY]

            # If car is charging, calculate absolute time of estimated completion
            if data.get(sc.API_EV_CHARGER_STATE_TYPE) == sc.CHARGING:
                keep_data[sc.API_EV_TIME_TO_FULLY_CHARGED_UTC] = data[sc.API_TIMESTAMP] + timedelta(
                    minutes=int(data.get(sc.API_EV_TIME_TO_FULLY_CHARGED))
                )
            else:
                keep_data[sc.API_EV_TIME_TO_FULLY_CHARGED_UTC] = None
            keep_data[sc.API_EV_TIME_TO_FULLY_CHARGED] = keep_data[sc.API_EV_TIME_TO_FULLY_CHARGED_UTC]

        return keep_data
