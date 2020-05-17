#  SPDX-License-Identifier: Apache-2.0
"""
subarulink.hass - A subpackage intended for Home Assistant integrations.

climate.py - remote start functionality

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
import time

import subarulink.const as sc
from subarulink.hass.vehicle import VehicleDevice


class Climate(VehicleDevice):
    """Home-assistant class of HVAC for Subaru vehicles.

    This is intended to be partially inherited by a Home-Assitant entity.
    """

    def __init__(self, data, controller):
        """Initialize the environmental controls.

        Vehicles have both a driver and passenger.

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
        self.__temp_setting = 72
        self.__fan_setting = sc.FAN_SPEED_MED
        self.__mode = sc.MODE_SPLIT
        self.__rear_defrost = sc.REAR_DEFROST_OFF
        self.__rear_ac = sc.REAR_AC_OFF
        self.__recirculate = sc.RECIRCULATE_OFF
        self.__left_seat = sc.HEAT_SEAT_OFF
        self.__right_seat = sc.HEAT_SEAT_OFF
        self.__is_climate_on = False
        self.__start_time = None
        self.__duration = 600
        self.__manual_update_time = time.time()

        self.type = "HVAC (climate) system"
        self.hass_type = "climate"
        self.measurement = "F"

        self.name = self._name()

        self.uniq_name = self._uniq_name()
        self.bin_type = 0x3

    def is_hvac_enabled(self):
        """Return whether HVAC is running."""
        if self.__start_time:
            if time.time() - self.__start_time >= self.__duration:
                return False
            return True
        return False

    def get_goal_temp(self):
        """Return driver set temperature."""
        return self.__temp_setting

    def get_fan_setting(self):
        """Return fan status."""
        return self.__fan_setting

    def get_mode(self):
        """Return HVAC mode."""
        return self.__mode

    async def async_update(self):
        """Update the HVAC state."""
        await super().async_update()
        # data = self._controller.get_data(self._vin)
        # if data:
        #     last_update = self._controller.get_last_update_time(self._vin)
        #     if last_update >= self.__manual_update_time:
        #         self.__is_auto_conditioning_on = data["is_auto_conditioning_on"]
        #         self.__is_climate_on = data["is_climate_on"]
        #         self.__driver_temp_setting = (
        #             data["driver_temp_setting"]
        #             if data["driver_temp_setting"]
        #             else self.__driver_temp_setting
        #         )
        #         self.__passenger_temp_setting = (
        #             data["passenger_temp_setting"]
        #             if data["passenger_temp_setting"]
        #             else self.__passenger_temp_setting
        #         )
        #     self.__outside_temp = (
        #         data["outside_temp"] if data["outside_temp"] else self.__outside_temp
        #     )
        #     self.__fan_status = data["fan_status"]

    async def set_temperature(self, temp):
        """Set HVAC target temperature."""
        self.__temp_setting = temp

    async def set_status(self, enabled):
        """Enable or disable the HVAC."""
        self.__manual_update_time = time.time()
        if enabled:
            await self._controller.remote_start(
                self._vin,
                self.__temp_setting,
                self.__mode,
                self.__left_seat,
                self.__right_seat,
                self.__rear_defrost,
                self.__fan_setting,
                self.__recirculate,
                self.__rear_ac,
            )
            self.__start_time = time.time()
        else:
            await self._controller.remote_stop(self._vin)

    @staticmethod
    def has_battery():
        """Return whether the device has a battery."""
        return False
