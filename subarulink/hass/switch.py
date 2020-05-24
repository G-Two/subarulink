#  SPDX-License-Identifier: Apache-2.0
"""
subarulink.hass - A subpackage intended for Home Assistant integrations.

switch.py - classes for subaru homeassistant switch entities

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
import subarulink.const as sc
from subarulink.hass.vehicle import VehicleDevice


class EVChargeSwitch(VehicleDevice):
    """Home-Assistant class for the charger of a Subaru VehicleDevice."""

    def __init__(self, data, controller):
        """Initialize the Charger Switch."""
        super().__init__(data, controller)
        self.__charger_state = False
        self.type = "charger switch"
        self.hass_type = "switch"
        self.name = self._name()
        self.uniq_name = self._uniq_name()

    async def async_update(self):
        """Update the charging state of the Subaru Vehicle."""
        await super().async_update()
        data = await self._controller.get_data(self._vin)
        if data:
            self.__charger_state = (
                data["status"][sc.EV_CHARGER_STATE_TYPE] == "CHARGING"
            )

    async def start_charge(self):
        """Start charging the Subaru Vehicle."""
        if not self.__charger_state:
            data = await self._controller.charge_start(self._vin)
            if data and data["data"]["success"]:
                self.__charger_state = True

    def is_charging(self):
        """Return whether the Subaru Vehicle is charging."""
        return self.__charger_state

    @staticmethod
    def has_battery():
        """Return whether the Subaru charger has a battery."""
        return False


class UpdateSwitch(VehicleDevice):
    """Home-Assistant class for a switch to initiate vehicle update request."""

    def __init__(self, data, controller):
        """Initialize the Locate Switch."""
        super().__init__(data, controller)
        self.type = "update switch"
        self.hass_type = "switch"
        self.name = self._name()
        self.uniq_name = self._uniq_name()
        self._state = False

    async def update(self):
        """Force an update."""
        self._state = True
        await self._controller.update(self._vin, force=True)
        await super().async_update()
        self._state = False

    @staticmethod
    def has_battery():
        """Return whether this entity has a battery."""
        return False
