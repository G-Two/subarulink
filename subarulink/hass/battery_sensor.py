#  SPDX-License-Identifier: Apache-2.0
"""
subarulink.hass - A subpackage intended for Home Assistant integrations.

battery_sensor.py - classes for PHEV Subarus

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
from typing import Dict, Text

import subarulink.const as sc
from subarulink.hass.vehicle import VehicleDevice


class Battery(VehicleDevice):
    """Home-Assistant battery class for a Subaru VehicleDevice."""

    def __init__(self, data: Dict, controller) -> None:
        """Initialize the Battery sensor.

        Args:
            data (Dict): The charging parameters for a Subaru vehicle.
            controller (Controller): The controller that controls updates to the Subaru API.

        """
        super().__init__(data, controller)
        self.__battery_level: int = 0
        self.__charging_state = None
        self.type: Text = "battery sensor"
        self.measurement: Text = "%"
        self.hass_type: Text = "sensor"
        self.name: Text = self._name()
        self.uniq_name: Text = self._uniq_name()
        self.bin_type: hex = 0x5

    async def async_update(self) -> None:
        """Update the battery state."""
        await super().async_update()
        data = await self._controller.get_data(self._vin)
        if data:
            self.__battery_level = data["status"][sc.EV_STATE_OF_CHARGE_PERCENT]
            self.__charging_state = data["status"][sc.EV_CHARGER_STATE_TYPE]

    @staticmethod
    def has_battery() -> bool:
        """Return whether the device has a battery."""
        return False

    def get_value(self) -> int:
        """Return the battery level."""
        return self.__battery_level


class Range(VehicleDevice):
    """Home-Assistant class of the battery range for a Subaru VehicleDevice."""

    def __init__(self, data: Dict, controller) -> None:
        """Initialize the Battery range sensor.

        Parameters
        ----------
        data : dict
            The charging parameters for a Subaru vehicle.
        controller : subarulink.Controller
            The controller that controls updates to the Subaru API.

        Returns
        -------
        None

        """
        super().__init__(data, controller)
        self.__battery_range = 0
        self.type = "EV Range"
        self.measurement = "LENGTH_MILES"
        self.hass_type = "sensor"
        self.name = self._name()
        self.uniq_name = self._uniq_name()
        self.bin_type = 0xA

    async def async_update(self):
        """Update the battery range state."""
        await super().async_update()
        data = await self._controller.get_data(self._vin)
        if data:
            self.__battery_range = data["status"][sc.EV_DISTANCE_TO_EMPTY]

    @staticmethod
    def has_battery():
        """Return whether the device has a battery."""
        return False

    def get_value(self):
        """Return the battery range."""
        return self.__battery_range
