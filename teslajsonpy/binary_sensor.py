#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  SPDX-License-Identifier: Apache-2.0
"""
Python Package for controlling Tesla API.

For more details about this api, please refer to the documentation at
https://github.com/zabuldon/teslajsonpy
"""
from teslajsonpy.vehicle import VehicleDevice


class ParkingSensor(VehicleDevice):
    """Home-assistant parking brake class for Tesla vehicles.

    This is intended to be partially inherited by a Home-Assitant entity.
    """

    def __init__(self, data, controller):
        """Initialize the parking brake sensor.

        Parameters
        ----------
        data : dict
            The base state for a Tesla vehicle.
            https://tesla-api.timdorr.com/vehicle/state/data
        controller : teslajsonpy.Controller
            The controller that controls updates to the Tesla API.

        Returns
        -------
        None

        """
        super().__init__(data, controller)
        self.__state = False

        self.type = 'parking brake sensor'
        self.hass_type = 'binary_sensor'
        self.sensor_type = 'power'

        self.name = self._name()

        self.uniq_name = self._uniq_name()
        self.bin_type = 0x1
        self.update()

    def update(self):
        """Update the parking brake sensor."""
        self._controller.update(self._id, wake_if_asleep=False)
        data = self._controller.get_drive_params(self._id)
        if data:
            if not data['shift_state'] or data['shift_state'] == 'P':
                self.__state = True
            else:
                self.__state = False

    def get_value(self):
        """Return whether parking brake engaged."""
        return self.__state

    @staticmethod
    def has_battery():
        """Return whether the device has a battery."""
        return False


class ChargerConnectionSensor(VehicleDevice):
    """Home-assistant charger connection class for Tesla vehicles.

    This is intended to be partially inherited by a Home-Assitant entity.
    """

    def __init__(self, data, controller):
        """Initialize the charger cable connection sensor.

        Parameters
        ----------
        data : dict
            The base state for a Tesla vehicle.
            https://tesla-api.timdorr.com/vehicle/state/data
        controller : teslajsonpy.Controller
            The controller that controls updates to the Tesla API.

        Returns
        -------
        None

        """
        super().__init__(data, controller)
        self.__state = False

        self.type = 'charger sensor'
        self.hass_type = 'binary_sensor'
        self.name = self._name()
        self.sensor_type = 'connectivity'

        self.uniq_name = self._uniq_name()
        self.bin_type = 0x2

    def update(self):
        """Update the charger connection sensor."""
        self._controller.update(self._id, wake_if_asleep=False)
        data = self._controller.get_charging_params(self._id)
        if data:
            if data['charging_state'] in ["Disconnected"]:
                self.__state = False
            else:
                self.__state = True

    def get_value(self):
        """Return whether the charger cable is connected."""
        return self.__state

    @staticmethod
    def has_battery():
        """Return whether the device has a battery."""
        return False
