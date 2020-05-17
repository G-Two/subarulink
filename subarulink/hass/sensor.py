#  SPDX-License-Identifier: Apache-2.0
"""
subarulink.hass - A subpackage intended for Home Assistant integrations.

sensor.py - Subaru sensor classes for Home Assistant

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
from typing import Dict, Text

import subarulink.const as sc
from subarulink.hass.vehicle import VehicleDevice


class AverageMPG(VehicleDevice):
    """Home-Assistant AverageMPG class for a Subaru vehicle."""

    def __init__(self, data: Dict, controller) -> None:
        """Initialize the sensor."""
        super().__init__(data, controller)
        self.__value: int = 0
        self.__charging_state = None
        self.type: Text = "Avg Fuel Consumption"
        self.measurement: Text = "MPG"
        self.hass_type: Text = "sensor"
        self.name: Text = self._name()
        self.uniq_name: Text = self._uniq_name()
        self.bin_type: hex = 0x5

    async def async_update(self) -> None:
        """Update the state."""
        await super().async_update()
        data = await self._controller.get_data(self._vin)
        if data:
            self.__value = data["status"][sc.AVG_FUEL_CONSUMPTION]

    @staticmethod
    def has_battery() -> bool:
        """Return whether the device has a battery."""
        return False

    def get_value(self) -> int:
        """Return the value."""
        if self.__value == sc.BAD_AVG_FUEL_CONSUMPTION:
            return None
        return self.__value


class Battery(VehicleDevice):
    """Home-Assistant 12V battery class for a Subaru vehicle."""

    def __init__(self, data: Dict, controller) -> None:
        """Initialize the sensor."""
        super().__init__(data, controller)
        self.__battery_level: int = 0
        self.__charging_state = None
        self.type: Text = "12V Battery Voltage"
        self.measurement: Text = "V"
        self.hass_type: Text = "sensor"
        self.name: Text = self._name()
        self.uniq_name: Text = self._uniq_name()
        self.bin_type: hex = 0x5

    async def async_update(self) -> None:
        """Update the state."""
        await super().async_update()
        data = await self._controller.get_data(self._vin)
        if data:
            self.__battery_level = data["status"][sc.BATTERY_VOLTAGE]

    @staticmethod
    def has_battery() -> bool:
        """Return whether the device has a battery."""
        return False

    def get_value(self) -> int:
        """Return the value."""
        return self.__battery_level


class EVBattery(VehicleDevice):
    """Home-Assistant EV battery class for a Subaru vehicle."""

    def __init__(self, data: Dict, controller) -> None:
        """Initialize the sensor."""
        super().__init__(data, controller)
        self.__battery_level: int = 0
        self.type: Text = "EV Battery Level"
        self.measurement: Text = "%"
        self.hass_type: Text = "sensor"
        self.name: Text = self._name()
        self.uniq_name: Text = self._uniq_name()
        self.bin_type: hex = 0x5

    async def async_update(self) -> None:
        """Update the state."""
        await super().async_update()
        data = await self._controller.get_data(self._vin)
        if data:
            self.__battery_level = data["status"][sc.EV_STATE_OF_CHARGE_PERCENT]

    @staticmethod
    def has_battery() -> bool:
        """Return whether the device has a battery."""
        return False

    def get_value(self) -> int:
        """Return the value."""
        return self.__battery_level


class EVChargeRate(VehicleDevice):
    """Home-Assistant EV charge rate sensor class for a Subaru vehicle."""

    def __init__(self, data: Dict, controller) -> None:
        """Initialize the sensor."""
        super().__init__(data, controller)
        self.type: Text = "EV Charge Rate"
        self.hass_type: Text = "sensor"
        self.measurement: Text = "minutes"
        self.name: Text = self._name()
        self.uniq_name: Text = self._uniq_name()
        self.__time_to_full = 0
        self.vin = self._vin

    async def async_update(self) -> None:
        """Update the state."""
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


class EVRange(VehicleDevice):
    """Home-Assistant class of the EV range for a Subaru vehicle."""

    def __init__(self, data: Dict, controller) -> None:
        """Initialize the sensor."""
        super().__init__(data, controller)
        self.__battery_range = 0
        self.type = "EV Range"
        self.measurement = "LENGTH_MILES"
        self.hass_type = "sensor"
        self.name = self._name()
        self.uniq_name = self._uniq_name()
        self.bin_type = 0xA

    async def async_update(self):
        """Update the state."""
        await super().async_update()
        data = await self._controller.get_data(self._vin)
        if data:
            self.__battery_range = data["status"][sc.EV_DISTANCE_TO_EMPTY]

    @staticmethod
    def has_battery():
        """Return whether the device has a battery."""
        return False

    def get_value(self):
        """Return the value."""
        return self.__battery_range


class Range(VehicleDevice):
    """Home-Assistant class of the range for a Subaru vehicle."""

    def __init__(self, data: Dict, controller) -> None:
        """Initialize the sensor."""
        super().__init__(data, controller)
        self.__range = 0
        self.type = "Range"
        self.measurement = "LENGTH_MILES"
        self.hass_type = "sensor"
        self.name = self._name()
        self.uniq_name = self._uniq_name()
        self.bin_type = 0xA

    async def async_update(self):
        """Update the state."""
        await super().async_update()
        data = await self._controller.get_data(self._vin)
        if data:
            self.__range = data["status"][sc.DIST_TO_EMPTY]

    @staticmethod
    def has_battery():
        """Return whether the device has a battery."""
        return False

    def get_value(self):
        """Return the value."""
        if self.__range == sc.BAD_DISTANCE_TO_EMPTY_FUEL:
            return None
        return self.__range


class Odometer(VehicleDevice):
    """Home-assistant class for odometer of Subaru vehicles."""

    def __init__(self, data, controller):
        """Initialize the sensor."""
        super().__init__(data, controller)
        self.__odometer = 0
        self.type = "Odometer"
        self.measurement = "LENGTH_MILES"
        self.hass_type = "sensor"
        self.name = self._name()
        self.uniq_name = self._uniq_name()
        self.bin_type = 0xB
        self.__rated = True

    async def async_update(self):
        """Update the state."""
        await super().async_update()
        data = await self._controller.get_data(self._vin)
        if data:
            self.__odometer = data["status"][sc.ODOMETER]

    @staticmethod
    def has_battery():
        """Return whether the device has a battery."""
        return False

    def get_value(self):
        """Return the value."""
        return self.__odometer


class TempSensor(VehicleDevice):
    """Home-assistant class of temperature sensors for Subaru vehicles."""

    def __init__(self, data, controller):
        """Initialize the sensor."""
        super().__init__(data, controller)
        self.__outside_temp = 0
        self.type = "External Temp"
        self.measurement = "F"
        self.hass_type = "sensor"
        self.name = self._name()
        self.uniq_name = self._uniq_name()
        self.bin_type = 0x4

    def get_outside_temp(self):
        """Get outside temperature."""
        return self.__outside_temp

    async def async_update(self):
        """Update the state."""
        await super().async_update()
        data = await self._controller.get_data(self._vin)
        if data:
            self.__outside_temp = float(data["status"][sc.EXTERNAL_TEMP])

    @staticmethod
    def has_battery():
        """Return whether the device has a battery."""
        return False
