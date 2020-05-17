#  SPDX-License-Identifier: Apache-2.0
"""
subarulink - A Python Package for interacting with Subaru Starlink Remote Services API.

connection.py - provides management for HTTP sessions to Subaru API

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
import asyncio
import logging
import pprint
import time

import aiohttp
from yarl import URL

from subarulink.exceptions import IncompleteCredentials, SubaruException

_LOGGER = logging.getLogger(__name__)


class Connection:
    """Connection to Subaru Starlink API."""

    def __init__(
        self,
        websession: aiohttp.ClientSession,
        username,
        password,
        device_id,
        device_name,
    ) -> None:
        """Initialize connection object."""
        self.username = username
        self.password = password
        self.device_id = device_id
        self.lock = asyncio.Lock()
        self.device_name = device_name
        self.vehicles = []
        self.vehicle_key = None
        self.default_vin = None
        self.baseurl = "https://mobileapi.prod.subarucs.com/g2v15"
        self.head = {}
        self.head[
            "User-Agent"
        ] = "Mozilla/5.0 (Linux; Android 10; Android SDK built for x86 Build/QSR1.191030.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.185 Mobile Safari/537.36"
        self.head["Origin"] = "file://"
        self.head["X-Requested-With"] = "com.subaru.telematics.app.remote"
        self.head["Accept-Language"] = "en-US,en;q=0.9"
        self.head["Accept-Encoding"] = "gzip, deflate"
        self.head["Accept"] = "*/*"
        self.websession = websession
        self.authenticated = False
        self.authorized = False
        self.current_vin = None

    async def connect(self):
        """Connect to and establish session with Subaru Remote Services API."""
        if await self._authenticate():
            await self._refresh_vehicles()
            if self.authorized:
                return self.vehicles
            if await self._authorize_device():
                return self.vehicles
        return None

    async def validate_session(self, vin):
        """Validate if current session cookie is still valid with Subaru Remote Services API and vehicle context is correct."""
        result = False
        resp = await self.__open("/validateSession.json", "get")
        js_resp = await resp.json()
        _LOGGER.debug(pprint.pformat(js_resp))
        if js_resp["success"]:
            if vin != self.current_vin:
                # API call for VIN that is not the current remote context.
                _LOGGER.debug("Switching Subaru API vehicle context to: %s", vin)
                if await self._select_vehicle(vin):
                    result = True
            else:
                result = True
        elif await self._authenticate(vin):
            # New session cookie.  Must call selectVehicle.json before any other API call.
            if await self._select_vehicle(vin):
                result = True
        else:
            self.authenticated = False
        return result

    async def get(self, command, params=None, data=None, json=None):
        """Send HTTPS GET request to Subaru Remote Services API."""
        if self.authenticated:
            resp = await self.__open(
                f"{command}",
                method="get",
                headers=self.head,
                params=params,
                data=data,
                json=json,
            )
            js_resp = await resp.json()
            return js_resp

    async def post(self, command, params=None, data=None, json=None):
        """Send HTTPS POST request to Subaru Remote Services API."""
        if self.authenticated:
            resp = await self.__open(
                f"{command}",
                method="post",
                headers=self.head,
                params=params,
                data=data,
                json=json,
            )
            js_resp = await resp.json()
            return js_resp

    async def _authenticate(self, vin=None) -> bool:
        """Authenticate to Subaru Remote Services API."""
        if self.username and self.password and self.device_id:
            post_data = {
                "env": "cloudprod",
                "loginUsername": self.username,
                "password": self.password,
                "deviceId": self.device_id,
                "passwordToken": None,
                "selectedVin": vin,
                "pushToken": None,
                "deviceType": "android",
            }
            resp = await self.__open(
                "/login.json", "post", data=post_data, headers=self.head
            )
            resp = await resp.json()
            if resp["success"]:
                _LOGGER.debug("Client authentication successful")
                _LOGGER.debug(pprint.pformat(resp))
                self.authenticated = True
                self.authorized = resp["data"]["deviceRegistered"]
                i = resp["data"]["currentVehicleIndex"]
                self.current_vin = resp["data"]["vehicles"][i]["vin"]
                return True
            if resp["errorCode"]:
                _LOGGER.error("Client authentication failed")
                raise SubaruException(resp["errorCode"])
            _LOGGER.error("Unknown failure")
            raise SubaruException(resp)
        raise IncompleteCredentials(
            "Connection requires email and password and device id."
        )

    async def _select_vehicle(self, vin):
        """Select active vehicle for accounts with multiple VINs."""
        params = {}
        params["vin"] = vin
        params["_"] = int(time.time())
        js_resp = await self.get("/selectVehicle.json", params=params)
        _LOGGER.debug(pprint.pformat(js_resp))
        if js_resp["success"]:
            self.current_vin = vin
            _LOGGER.debug("Current vehicle: vin=%s", js_resp["data"]["vin"])
            return js_resp["data"]
        self.current_vin = None
        return None

    async def _refresh_vehicles(self):
        resp = await self.__open(
            "/refreshVehicles.json", "get", params={"_": int(time.time())}
        )
        js_resp = await resp.json()
        _LOGGER.debug(pprint.pformat(js_resp))
        vehicles = js_resp["data"]["vehicles"]
        if len(vehicles) > 1:
            vehicles = await self._refresh_multi_vehicle(vehicles)
        for vehicle in vehicles:
            car = {}
            car["vin"] = vehicle["vin"]
            car["id"] = vehicle["vehicleKey"]
            car["display_name"] = vehicle["vehicleName"]
            if "g2" in vehicle["features"]:
                car["api_gen"] = "g2"
            elif "g1" in vehicle["features"]:
                car["api_gen"] = "g1"
            else:
                car["api_gen"] = "g0"
            if "PHEV" in vehicle["features"]:
                car["hasEV"] = True
            else:
                car["hasEV"] = False
            if "RES" in vehicle["features"]:
                car["hasRES"] = True
            else:
                car["hasRES"] = False
            if "REMOTE" in vehicle["subscriptionFeatures"]:
                car["hasRemote"] = True
            else:
                car["hasRemote"] = False
            self.vehicles.append(car)

    async def _refresh_multi_vehicle(self, vehicles):
        # refreshVehicles.json returns unreliable data if multiple cars on account
        # use selectVehicle.json to get each car's info
        result = []
        for vehicle in vehicles:
            vin = vehicle["vin"]
            result.append(await self._select_vehicle(vin))
        return result

    async def _authorize_device(self):
        _LOGGER.debug("Authorizing device via web API")
        web_baseurl = "https://www.mysubaru.com"
        if self.username and self.password and self.device_id:
            post_data = {
                "username": self.username,
                "password": self.password,
                "deviceId": self.device_id,
            }
            resp = await self.__open(
                "/login", "post", data=post_data, baseurl=web_baseurl
            )
        resp = await self.__open(
            "/profile/updateDeviceEntry.json",
            "get",
            params={"deviceId": self.device_id},
            baseurl=web_baseurl,
        )
        if await resp.json():
            _LOGGER.debug("Device successfully authorized")
            return await self._set_device_name()
        return False

    async def _set_device_name(self):
        _LOGGER.debug("Setting Device Name to %s", self.device_name)
        web_baseurl = "https://www.mysubaru.com"
        resp = await self.__open(
            "/profile/addDeviceName.json",
            "get",
            params={"deviceId": self.device_id, "deviceName": self.device_name},
            baseurl=web_baseurl,
        )
        js_resp = await resp.json()
        if js_resp:
            _LOGGER.debug("Set Device Name Successful")
            return True
        _LOGGER.debug("Unknown Error during Set Device Name")
        return False

    async def __open(
        self,
        url,
        method="get",
        headers=None,
        data=None,
        json=None,
        params=None,
        baseurl="",
    ) -> None:
        """Open url."""
        if not baseurl:
            baseurl = self.baseurl
        url: URL = URL(baseurl + url)

        _LOGGER.debug("%s: %s", method.upper(), url)
        with await self.lock:
            try:
                resp = await getattr(self.websession, method)(
                    url, headers=headers, params=params, data=data, json=json
                )
                if resp.status > 299:
                    _LOGGER.debug(pprint.pformat(resp.request_info))
                    js_resp = await resp.json()
                    _LOGGER.debug(pprint.pformat(js_resp))
                    raise SubaruException(resp.status)
            except aiohttp.ClientResponseError as exception:
                raise SubaruException(exception.status)
            except aiohttp.ClientConnectionError:
                raise SubaruException("aiohttp.ClientConnectionError")
            return resp
