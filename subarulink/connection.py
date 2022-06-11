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
    API_2FA_AUTH_VERIFY,
    API_2FA_CONTACT,
    API_2FA_SEND_VERIFICATION,
    API_LOGIN,
    API_SELECT_VEHICLE,
    API_VALIDATE_SESSION,
    ERROR_INVALID_ACCOUNT,
    ERROR_INVALID_CREDENTIALS,
    ERROR_PASSWORD_WARNING,
    MOBILE_API_SERVER,
    MOBILE_API_VERSION,
    MOBILE_APP,
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

    def __init__(
        self,
        websession: aiohttp.ClientSession,
        username,
        password,
        device_id,
        device_name,
        country,
    ) -> None:
        """
        Initialize connection object.

        Args:
            websession (aiohttp.ClientSession): An instance of aiohttp.ClientSession.
            username (str): Username used for the MySubaru mobile app.
            password (str): Password used for the MySubaru mobile app.
            device_id (str): Alphanumeric designator that Subaru API uses to track individual device authorization.
            device_name (str): Human friendly name that is associated with `device_id` (shows on mysubaru.com profile "devices").
            country (str): Country of MySubaru Account [CAN, USA].
        """
        self._username = username
        self._password = password
        self._device_id = device_id
        self._country = country
        self._lock = asyncio.Lock()
        self._device_name = device_name
        self._vehicles = []
        self._head = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; Android SDK built for x86 Build/QSR1.191030.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.185 Mobile Safari/537.36",
            "Origin": "file://",
            "X-Requested-With": MOBILE_APP[self._country],
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Accept": "*/*",
        }
        self._websession = websession
        self._authenticated = False
        self._registered = False
        self._current_vin = None
        self._list_of_vins = []
        self._session_login_time = None
        self._auth_contact_options = None

    async def connect(self):
        """
        Connect to and establish session with Subaru Starlink mobile app API.

        Returns:
            List: A list of strs containing the VIN of each vehicle registered in the Subaru account.

        Raises:
            InvalidCredentials: If login credentials are incorrect.
            IncompleteCredentials: If login credentials were not provided.
            SubaruException: If login fails for any other reason.

        """
        await self._authenticate()
        await self._get_vehicle_data()
        if not self.device_registered:
            await self._get_contact_methods()
        return self._vehicles

    @property
    def device_registered(self):
        """Device is registered."""
        return self._registered

    @property
    def auth_contact_methods(self):
        """Contact methods for 2FA."""
        return self._auth_contact_options

    async def request_auth_code(self, contact_method):
        """Request 2FA code be sent via specified contact method."""
        if contact_method not in self.auth_contact_methods:
            _LOGGER.error("Invalid 2FA contact method requested")
            return False
        _LOGGER.debug("Requesting 2FA code")
        post_data = {
            "contactMethod": contact_method,
            "languagePreference": "EN",
        }
        js_resp = await self.__open(
            API_2FA_SEND_VERIFICATION,
            POST,
            params=post_data,
        )
        if js_resp:
            _LOGGER.debug(pprint.pformat(js_resp))
            return True

    async def submit_auth_code(self, code, make_permanent=True):
        """Submit received 2FA code for validation."""
        if not code.isdecimal() or len(code) != 6:
            _LOGGER.error("2FA code must be 6 digits")
            return False
        _LOGGER.info("Validating 2FA response")
        post_data = {
            "deviceId": self._device_id,
            "deviceName": self._device_name,
            "verificationCode": code,
        }
        if make_permanent:
            post_data["rememberDevice"] = "on"

        js_resp = await self.__open(API_2FA_AUTH_VERIFY, POST, params=post_data)
        if js_resp:
            _LOGGER.debug(pprint.pformat(js_resp))
            if js_resp["success"]:
                _LOGGER.info("Device successfully authorized")
                while not self._registered:
                    # Device registration does not always immediately take effect
                    await asyncio.sleep(3)
                    await self._authenticate()
                    # Current server side vin context is ambiguous (even for single vehicle account??)
                    self._current_vin = None
                return True

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

        if result is False:
            await self._authenticate(vin)
            # New session cookie.  Must call selectVehicle.json before any other API call.
            if await self._select_vehicle(vin):
                result = True

        return result

    def get_session_age(self):
        """Return number of minutes since last authentication."""
        return (time.time() - self._session_login_time) // 60

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
                self._session_login_time = time.time()
                self._registered = js_resp["data"]["deviceRegistered"]
                self._list_of_vins = [v["vin"] for v in js_resp["data"]["vehicles"]]
                self._current_vin = None
                return True
            if js_resp.get("errorCode"):
                _LOGGER.debug(pprint.pformat(js_resp))
                error = js_resp.get("errorCode")
                if error == ERROR_INVALID_ACCOUNT:
                    _LOGGER.error("Invalid account")
                    raise InvalidCredentials(error)
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
        params = {"vin": vin, "_": int(time.time())}
        js_resp = await self.get(API_SELECT_VEHICLE, params=params)
        _LOGGER.debug(pprint.pformat(js_resp))
        if js_resp.get("success"):
            self._current_vin = vin
            _LOGGER.debug("Current vehicle: vin=%s", js_resp["data"]["vin"])
            return js_resp["data"]
        if not js_resp.get("success") and js_resp.get("errorCode") == "VEHICLESETUPERROR":
            # Occasionally happens every few hours. Resetting the session seems to deal with it.
            _LOGGER.warning("VEHICLESETUPERROR received. Resetting session.")
            self.reset_session()
            return False
        _LOGGER.debug("Failed to switch vehicle errorCode=%s", js_resp.get("errorCode"))
        # Something else is probably wrong with the backend server context - try resetting
        self.reset_session()
        raise SubaruException("Failed to switch vehicle %s - resetting session." % js_resp.get("errorCode"))

    async def _get_vehicle_data(self):
        for vin in self._list_of_vins:
            params = {"vin": vin, "_": int(time.time())}
            js_resp = await self.get(API_SELECT_VEHICLE, params=params)
            _LOGGER.debug(pprint.pformat(js_resp))
            self._vehicles.append(js_resp["data"])
            self._current_vin = vin

    async def _get_contact_methods(self):
        js_resp = await self.__open(API_2FA_CONTACT, POST)
        if js_resp:
            _LOGGER.debug(pprint.pformat(js_resp))
            self._auth_contact_options = js_resp.get("data")

    async def __open(
        self,
        url,
        method=GET,
        headers=None,
        data=None,
        json_data=None,
        params=None,
        baseurl="",
    ):
        """Open url."""
        if not baseurl:
            baseurl = f"https://{MOBILE_API_SERVER[self._country]}{MOBILE_API_VERSION}"
        url: URL = URL(baseurl + url)

        _LOGGER.debug("%s: %s, params=%s, json_data=%s", method.upper(), url, params, json_data)
        async with self._lock:
            try:
                resp = await getattr(self._websession, method)(
                    url, headers=headers, params=params, data=data, json=json_data
                )
                if resp.status > 299:
                    raise SubaruException("HTTP %d: %s %s" % (resp.status, await resp.text(), resp.request_info))
                js_resp = await resp.json()
                if "success" not in js_resp and "serviceType" not in js_resp:
                    raise SubaruException("Unexpected response: %s" % resp)
                return js_resp
            except aiohttp.ClientResponseError as err:
                raise SubaruException(err.status) from err
            except aiohttp.ClientConnectionError as err:
                raise SubaruException("aiohttp.ClientConnectionError") from err
