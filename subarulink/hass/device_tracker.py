#  SPDX-License-Identifier: Apache-2.0
"""
subarulink.hass - A subpackage intended for Home Assistant integrations.

device_tracker.py - Subaru location tracker for Home Assistant

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
import subarulink.const as sc
from subarulink.hass.vehicle import VehicleDevice


class GPS(VehicleDevice):
    """Home-assistant class for GPS of Subaru vehicles."""

    def __init__(self, data, controller):
        """Initialize the Vehicle's GPS information.

        Parameters
        ----------
        data : dict
            The base state for a Subaru vehicle.
            https://tesla-api.timdorr.com/vehicle/state/data
        controller : subarulink.Controller
            The controller that controls updates to the Subaru API.

        Returns
        -------
        None

        """
        super().__init__(data, controller)
        self.__longitude = 0
        self.__latitude = 0
        self.__heading = 0
        self.__speed = 0
        self.__location = None

        self.last_seen = 0
        self.last_updated = 0
        self.type = "location tracker"
        self.hass_type = "devices_tracker"
        self.bin_type = 0x6

        self.name = self._name()

        self.uniq_name = self._uniq_name()

    def get_location(self):
        """Return the current location."""
        return self.__location

    async def async_update(self):
        """Update the current GPS location."""
        await super().async_update()
        data = await self._controller.get_data(self._vin)
        if data.get("location"):
            self.__longitude = data["location"][sc.LONGITUDE]
            self.__latitude = data["location"][sc.LATITUDE]
            self.__heading = data["location"][sc.HEADING]
            self.__speed = data["location"][sc.SPEED]
        if self.__longitude and self.__latitude:
            self.__location = {
                "longitude": self.__longitude,
                "latitude": self.__latitude,
                "heading": self.__heading,
                "speed": self.__speed,
            }

    @staticmethod
    def has_battery():
        """Return whether the device has a battery."""
        return False
