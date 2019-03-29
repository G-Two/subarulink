#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  SPDX-License-Identifier: Apache-2.0
"""
Python Package for controlling Tesla API.

For more details about this api, please refer to the documentation at
https://github.com/zabuldon/teslajsonpy
"""
import time

from teslajsonpy.vehicle import VehicleDevice


class ChargerSwitch(VehicleDevice):
    """Home-Assistant class for the charger of a Tesla VehicleDevice."""

    def __init__(self, data, controller):
        """Initialize the Charger Switch.

        Parameters
        ----------
        data : dict
            The base state for a Tesla vehicle.
            https://tesla-api.timdorr.com/vehicle/state/chargestate
        controller : teslajsonpy.Controller
            The controller that controls updates to the Tesla API.

        Returns
        -------
        None

        """
        super().__init__(data, controller)
        self.__manual_update_time = 0
        self.__charger_state = False
        self.type = 'charger switch'
        self.hass_type = 'switch'
        self.name = self._name()
        self.uniq_name = self._uniq_name()
        self.bin_type = 0x8
        self.update()

    def update(self):
        """Update the charging state of the Tesla Vehicle."""
        self._controller.update(self._id, wake_if_asleep=False)
        data = self._controller.get_charging_params(self._id)
        if data and (time.time() - self.__manual_update_time > 60):
            if data['charging_state'] != "Charging":
                self.__charger_state = False
            else:
                self.__charger_state = True

    def start_charge(self):
        """Start charging the Tesla Vehicle."""
        if not self.__charger_state:
            data = self._controller.command(self._id, 'charge_start',
                                            wake_if_asleep=True)
            if data and data['response']['result']:
                self.__charger_state = True
            self.__manual_update_time = time.time()

    def stop_charge(self):
        """Stop charging the Tesla Vehicle."""
        if self.__charger_state:
            data = self._controller.command(self._id, 'charge_stop',
                                            wake_if_asleep=True)
            if data and data['response']['result']:
                self.__charger_state = False
            self.__manual_update_time = time.time()

    def is_charging(self):
        """Return whether the Tesla Vehicle is charging."""
        return self.__charger_state

    @staticmethod
    def has_battery():
        """Return whether the Tesla charger has a battery."""
        return False


class RangeSwitch(VehicleDevice):
    """Home-Assistant class for setting range limit for charger."""

    def __init__(self, data, controller):
        """Initialize the charger range switch."""
        super().__init__(data, controller)
        self.__manual_update_time = 0
        self.__maxrange_state = False
        self.type = 'maxrange switch'
        self.hass_type = 'switch'
        self.name = self._name()
        self.uniq_name = self._uniq_name()
        self.bin_type = 0x9
        self.update()

    def update(self):
        """Update the status of the range setting."""
        self._controller.update(self._id, wake_if_asleep=False)
        data = self._controller.get_charging_params(self._id)
        if data and (time.time() - self.__manual_update_time > 60):
            self.__maxrange_state = data['charge_to_max_range']

    def set_max(self):
        """Set the charger to max range for trips."""
        if not self.__maxrange_state:
            data = self._controller.command(self._id, 'charge_max_range',
                                            wake_if_asleep=True)
            if data['response']['result']:
                self.__maxrange_state = True
            self.__manual_update_time = time.time()

    def set_standard(self):
        """Set the charger to standard range for daily commute."""
        if self.__maxrange_state:
            data = self._controller.command(self._id, 'charge_standard',
                                            wake_if_asleep=True)
            if data and data['response']['result']:
                self.__maxrange_state = False
            self.__manual_update_time = time.time()

    def is_maxrange(self):
        """Return whether max range setting is set."""
        return self.__maxrange_state

    @staticmethod
    def has_battery():
        """Return whether the device has a battery."""
        return False
