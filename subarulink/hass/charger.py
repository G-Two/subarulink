#  SPDX-License-Identifier: Apache-2.0
"""
subarulink.hass - A subpackage intended for Home Assistant integrations.

charger.py - classes for PHEV Subarus

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
from typing import Dict, Text

import subarulink.const as sc
from subarulink.hass.vehicle import VehicleDevice


class ChargerSwitch(VehicleDevice):
    """Home-Assistant class for the charger of a Subaru VehicleDevice."""

    def __init__(self, data, controller):
        """Initialize the Charger Switch.

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
        self.__manual_update_time = 0
        self.__charger_state = False
        self.type = "charger switch"
        self.hass_type = "switch"
        self.name = self._name()
        self.uniq_name = self._uniq_name()
        self.bin_type = 0x8

    async def async_update(self):
        """Update the charging state of the Subaru Vehicle."""
        await super().async_update()
        data = await self._controller.get_data(self._vin)
        if data:
            self.__charger_state = (
                "CHARGING" in data["status"][sc.EV_TIME_TO_FULLY_CHARGED]
            )

    async def start_charge(self):
        """Start charging the Subaru Vehicle."""
        if not self.__charger_state:
            data = await self._controller.charge_start(self._vin)
            if data and data["data"]["success"]:
                self.__charger_state = True

    async def stop_charge(self):
        """Stop charging the Subaru Vehicle."""
        if self.__charger_state:
            data = await self._controller.charge_stop(self._vin)
            if data and data["data"]["success"]:
                self.__charger_state = False

    def is_charging(self):
        """Return whether the Subaru Vehicle is charging."""
        return self.__charger_state

    @staticmethod
    def has_battery():
        """Return whether the Subaru charger has a battery."""
        return False


class ChargingSensor(VehicleDevice):
    """Home-Assistant charging sensor class for a Subaru VehicleDevice."""

    def __init__(self, data: Dict, controller) -> None:
        """Initialize the Charger sensor.

        Args:
            data (Dict): The charging parameters for a Subaru vehicle.
            controller (Controller): The controller that controls updates to the Subaru API.

        """
        super().__init__(data, controller)
        self.type: Text = "charging rate sensor"
        self.hass_type: Text = "sensor"
        self.name: Text = self._name()
        self.uniq_name: Text = self._uniq_name()
        self.bin_type: hex = 0xC
        self.__time_to_full = 0
        self.measurement = "LENGTH_MILES"
        self.vin = self._vin

    async def async_update(self) -> None:
        """Update the battery state."""
        await super().async_update()
        data = await self._controller.get_data(self._vin)
        if data:
            self.__time_to_full = data["status"][sc.EV_TIME_TO_FULLY_CHARGED]

    @staticmethod
    def has_battery() -> bool:
        """Return whether the device has a battery."""
        return False

    @property
    def time_left(self) -> float:
        """Return the time left to full in hours."""
        return self.__time_to_full
