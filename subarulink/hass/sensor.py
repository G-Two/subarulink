#  SPDX-License-Identifier: Apache-2.0
"""
subarulink.hass - A subpackage intended for Home Assistant integrations.

sensor.py - Subaru sensor classes for Home Assistant

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
import subarulink.const as sc
from subarulink.hass.vehicle import VehicleDevice


class SubaruSensor(VehicleDevice):
    """Home Assistant Sensor class for a Subaru vehicle."""

    def __init__(self, data, title, data_field, controller):
        """Initialize a SubaruSensor."""
        super().__init__(data, controller)
        self.type = title
        self.hass_type = "sensor"
        self.name = self._name()
        self.uniq_name = self._uniq_name()
        self._data_field = data_field
        self._value = None

    @staticmethod
    def has_battery():
        """Return whether the device has a battery."""
        return False

    def get_value(self):
        """Return the value."""
        if self._value in sc.BAD_SENSOR_VALUES:
            return None
        return self._value

    async def async_update(self) -> None:
        """Update the state."""
        await super().async_update()
        data = await self._controller.get_data(self._vin)
        if data:
            self._value = data["status"][self._data_field]
