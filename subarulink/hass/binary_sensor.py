#  SPDX-License-Identifier: Apache-2.0
"""
subarulink.hass - A subpackage intended for Home Assistant integrations.

binary_sensor.py - Subaru binary sensor classes for Home Assistant

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
import subarulink.const as sc
from subarulink.hass.vehicle import VehicleDevice


class EVChargerConnection(VehicleDevice):
    """Home-assistant charger connection class for Subaru vehicles.

    This is intended to be partially inherited by a Home-Assitant entity.
    """

    def __init__(self, data, controller):
        """Initialize the charger cable connection sensor.

        Parameters
        ----------
        data : dict
            The base state for a Subaru vehicle.
        controller : subarulink.Controller
            The controller that controls updates to the Subaru API.

        Returns
        -------
        None

        """
        super().__init__(data, controller)
        self.__state = False

        self.type = "charger sensor"
        self.hass_type = "binary_sensor"
        self.name = self._name()
        self.sensor_type = "connectivity"

        self.uniq_name = self._uniq_name()
        self.bin_type = 0x2

    async def async_update(self):
        """Update the charger connection sensor."""
        await super().async_update()
        data = await self._controller.get_data(self._vin)
        if data:
            self.__state = "LOCKED_CONNECTED" in data["status"][sc.EV_IS_PLUGGED_IN]

    def get_value(self):
        """Return whether the charger cable is connected."""
        return self.__state

    @staticmethod
    def has_battery():
        """Return whether the device has a battery."""
        return False
