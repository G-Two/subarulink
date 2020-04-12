#  SPDX-License-Identifier: Apache-2.0
"""
subarulink.hass - A subpackage intended for Home Assistant integrations.

lock.py - Subaru door locks for Home Assistant

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
from subarulink.hass.vehicle import VehicleDevice


class Lock(VehicleDevice):
    """Home-assistant lock class for Subaru vehicles.

    This is intended to be partially inherited by a Home-Assitant entity.
    """

    def __init__(self, data, controller):
        """Initialize the locks for the vehicle.

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
        self.__manual_update_time = 0
        self.__lock_state = False

        self.type = "door lock"
        self.hass_type = "lock"

        self.name = self._name()

        self.uniq_name = self._uniq_name()
        self.bin_type = 0x7

    async def lock(self):
        """Send lock command."""
        data = await self._controller.lock(self._vin)
        if data and data["data"]["success"]:
            self.__lock_state = True

    async def unlock(self):
        """Send unlock command."""
        data = await self._controller.unlock(self._vin)
        if data and data["data"]["success"]:
            self.__lock_state = False

    def is_locked(self):
        """Return whether doors are locked.

        Subaru API does not report lock status.  This state cannot be depended on.
        """
        return self.__lock_state

    @staticmethod
    def has_battery():
        """Return whether the device has a battery."""
        return False
