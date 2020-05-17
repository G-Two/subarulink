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
        """Initialize the locks for the vehicle."""
        super().__init__(data, controller)
        self.type = "Door Lock"
        self.hass_type = "lock"
        self.name = self._name()
        self.uniq_name = self._uniq_name()
        self.bin_type = 0x7

    async def lock(self):
        """Send lock command."""
        data = await self._controller.lock(self._vin)
        if data and data["data"]["success"]:
            return True

    async def unlock(self):
        """Send unlock command."""
        data = await self._controller.unlock(self._vin)
        if data and data["data"]["success"]:
            return True

    @staticmethod
    def has_battery():
        """Return whether the device has a battery."""
        return False
