#  SPDX-License-Identifier: Apache-2.0
"""
Provides managed HTTP session to Subaru Starlink mobile app API.

For more details, please refer to the documentation at https://github.com/G-Two/subarulink
"""
import asyncio
import logging
import pprint
import time

import aiohttp
from yarl import URL

from subarulink.const import (
    API_LOGIN,
    API_REFRESH_VEHICLES,
    API_SELECT_VEHICLE,
    API_VALIDATE_SESSION,
    ERROR_INVALID_CREDENTIALS,
    ERROR_PASSWORD_WARNING,
    MOBILE_API_BASE_URL,
    WEB_API_AUTHORIZE_DEVICE,
    WEB_API_BASE_URL,
    WEB_API_LOGIN,
    WEB_API_NAME_DEVICE,
)
from subarulink.exceptions import (
    IncompleteCredentials,
    InvalidCredentials,
    SubaruException,
)

_LOGGER = logging.getLogger(__name__)

GET = "get"
POST = "post"


class Connection:
    """A managed HTTP session to Subaru Starlink mobile app API."""

    def __init__(self, websession: aiohttp.ClientSession, username, password, device_id, device_name,) -> None:
        """
        Initialize connection object.

        Args:
            websession (aiohttp.ClientSession): An instance of aiohttp.ClientSession.
            username (str): Username used for the MySubaru mobile app.
            password (str): Password used for the MySubaru mobile app.
            device_id (str): Alphanumeric designator that Subaru API uses to track individual device authorization.
            device_name (str): Human friendly name that is associated with `device_id` (shows on mysubaru.com profile "devices").
        """
        self._username = username
        self._password = password
        self._device_id = device_id
        self._lock = asyncio.Lock()
        self._device_name = device_name
        self._vehicles = []
        self._head = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; Android SDK built for x86 Build/QSR1.191030.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.185 Mobile Safari/537.36",
            "Origin": "file://",
            "X-Requested-With": "com.subaru.telematics.app.remote",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Accept": "*/*",
        }
        self._websession = websession
        self._authenticated = False
        self._registered = False
        self._current_vin = None

    async def connect(self, test_login=False):
        """
        Connect to and establish session with Subaru Starlink mobile app API.

        Args:
            test_login (bool): If `True` then username/password is verified but device registration is not performed.

        Returns:
            List: A list of strs containing the VIN of each vehicle registered in the Subaru account.

        Raises:
            InvalidCredentials: If login credentials are incorrect.
            IncompleteCredentials: If login credentials were not provided.
            SubaruException: If login fails for any other reason.

        """
        await self._authenticate()
        await self._refresh_vehicles()
        if self._registered or test_login:
            return self._vehicles
        if await self._register_device():
            self.reset_session()
            while not self._registered:
                # Device registration does not always immediately take effect
                await asyncio.sleep(3)
                await self._authenticate()
            return self._vehicles

    async def validate_session(self, vin):
        """
        Validate if current session is ready for an API command/query.

        Verifies session cookie is still valid and re-authenticates if necessary.
        Sets server-side vehicle context as needed.

        Args:
            vin (str): VIN of desired server-side vehicle context.

        Returns:
            bool: `True` if session is ready to send a command or query to the Subaru API with the desired `vin` context.

        Raises:
            SubaruException: If validation fails and a new session fails to be established.
        """
        result = False
        js_resp = await self.__open(API_VALIDATE_SESSION, GET)
        _LOGGER.debug(pprint.pformat(js_resp))
        if js_resp["success"]:
            if vin != self._current_vin:
                # API call for VIN that is not the current remote context.
                _LOGGER.debug("Switching Subaru API vehicle context to: %s", vin)
                if await self._select_vehicle(vin):
                    result = True
            else:
                result = True
        else:
            await self._authenticate(vin)
            # New session cookie.  Must call selectVehicle.json before any other API call.
            if await self._select_vehicle(vin):
                result = True

        return result

    def reset_session(self):
        """Clear session cookies."""
        self._websession.cookie_jar.clear()

    async def get(self, url, params=None):
        """
        Send HTTPS GET request to Subaru Remote Services API.

        Args:
            url (str): URL path that will be concatenated after `subarulink.const.MOBILE_API_BASE_URL`
            params (Dict, optional): HTTP GET request parameters

        Returns:
            Dict: JSON response as a Dict

        Raises:
            SubaruException: If request fails.
        """
        if self._authenticated:
            return await self.__open(url, method=GET, headers=self._head, params=params)

    async def post(self, url, params=None, json_data=None):
        """
        Send HTTPS POST request to Subaru Remote Services API.

        Args:
            url (str): URL path that will be concatenated after `subarulink.const.MOBILE_API_BASE_URL`
            params (Dict, optional): HTTP POST request parameters
            json_data (Dict, optional): HTTP POST request JSON data as a Dict

        Returns:
            Dict: JSON response as a Dict

        Raises:
            SubaruException: If request fails.
        """
        if self._authenticated:
            return await self.__open(url, method=POST, headers=self._head, params=params, json_data=json_data)

    async def _authenticate(self, vin=None) -> bool:
        """Authenticate to Subaru Remote Services API."""
        if self._username and self._password and self._device_id:
            post_data = {
                "env": "cloudprod",
                "loginUsername": self._username,
                "password": self._password,
                "deviceId": self._device_id,
                "passwordToken": None,
                "selectedVin": vin,
                "pushToken": None,
                "deviceType": "android",
            }
            js_resp = await self.__open(API_LOGIN, POST, data=post_data, headers=self._head)
            if js_resp.get("success"):
                _LOGGER.debug("Client authentication successful")
                _LOGGER.debug(pprint.pformat(js_resp))
                self._authenticated = True
                self._registered = js_resp["data"]["deviceRegistered"]
                i = js_resp["data"]["currentVehicleIndex"]
                self._current_vin = js_resp["data"]["vehicles"][i]["vin"]
                return True
            if js_resp.get("errorCode"):
                _LOGGER.debug(pprint.pformat(js_resp))
                error = js_resp.get("errorCode")
                if error == ERROR_INVALID_CREDENTIALS:
                    _LOGGER.error("Client authentication failed")
                    raise InvalidCredentials(error)
                if error == ERROR_PASSWORD_WARNING:
                    _LOGGER.error("Multiple Password Failures.")
                    raise InvalidCredentials(error)
                raise SubaruException(error)
        raise IncompleteCredentials("Connection requires email and password and device id.")

    async def _select_vehicle(self, vin):
        """Select active vehicle for accounts with multiple VINs."""
        params = {}
        params["vin"] = vin
        params["_"] = int(time.time())
        js_resp = await self.get(API_SELECT_VEHICLE, params=params)
        _LOGGER.debug(pprint.pformat(js_resp))
        if js_resp.get("success"):
            self._current_vin = vin
            _LOGGER.debug("Current vehicle: vin=%s", js_resp["data"]["vin"])
            return js_resp["data"]
        raise SubaruException("Failed to switch vehicle %s" % js_resp.get("errorCode"))

    async def _refresh_vehicles(self):
        js_resp = await self.__open(API_REFRESH_VEHICLES, GET, params={"_": int(time.time())})
        _LOGGER.debug(pprint.pformat(js_resp))
        vehicles = js_resp["data"]["vehicles"]
        if len(vehicles) > 1:
            vehicles = await self._refresh_multi_vehicle(vehicles)
        self._vehicles.extend(vehicles)

    async def _refresh_multi_vehicle(self, vehicles):
        # refreshVehicles.json returns unreliable data if multiple cars on account
        # use selectVehicle.json to get each car's info
        result = []
        for vehicle in vehicles:
            vin = vehicle["vin"]
            result.append(await self._select_vehicle(vin))
        return result

    async def _register_device(self):
        _LOGGER.debug("Authorizing device via web API")
        post_data = {
            "username": self._username,
            "password": self._password,
            "deviceId": self._device_id,
        }
        resp = await self.__open(WEB_API_LOGIN, POST, data=post_data, baseurl=WEB_API_BASE_URL, decode_json=False,)
        js_resp = None
        if resp:
            js_resp = await self.__open(
                WEB_API_AUTHORIZE_DEVICE,
                GET,
                params={"deviceId": self._device_id},
                baseurl=WEB_API_BASE_URL,
                decode_json=False,
            )
        if js_resp:
            _LOGGER.info("Device successfully authorized")
            return await self._set_device_name()

    async def _set_device_name(self):
        _LOGGER.debug("Setting Device Name to %s", self._device_name)
        js_resp = await self.__open(
            WEB_API_NAME_DEVICE,
            GET,
            params={"deviceId": self._device_id, "deviceName": self._device_name},
            baseurl=WEB_API_BASE_URL,
            decode_json=False,
        )
        if js_resp:
            _LOGGER.debug("Set Device Name Successful")
            return True

    async def __open(
        self, url, method=GET, headers=None, data=None, json_data=None, params=None, baseurl="", decode_json=True,
    ):
        """Open url."""
        if not baseurl:
            baseurl = MOBILE_API_BASE_URL
        url: URL = URL(baseurl + url)

        _LOGGER.debug("%s: %s", method.upper(), url)
        async with self._lock:
            try:
                resp = await getattr(self._websession, method)(
                    url, headers=headers, params=params, data=data, json=json_data
                )
                if resp.status > 299:
                    _LOGGER.error(pprint.pformat(resp.request_info))
                    _LOGGER.error(pprint.pformat(await resp.text()))
                    raise SubaruException("HTTP %d: %s" % (resp.status, resp))
                if decode_json:
                    js_resp = await resp.json()
                    if "success" not in js_resp and "serviceType" not in js_resp:
                        raise SubaruException("Unexpected response: %s" % resp)
                    return js_resp
                return resp
            except aiohttp.ClientResponseError as err:
                raise SubaruException(err.status) from err
            except aiohttp.ClientConnectionError as err:
                raise SubaruException("aiohttp.ClientConnectionError") from err
