#  SPDX-License-Identifier: Apache-2.0
"""
subarulink.hass - A subpackage intended for Home Assistant integrations.

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
from subarulink.__version__ import __version__
from subarulink.exceptions import SubaruException
from subarulink.hass.battery_sensor import Battery, Range
from subarulink.hass.binary_sensor import ChargerConnectionSensor
from subarulink.hass.charger import ChargerSwitch, ChargingSensor
from subarulink.hass.climate import Climate, TempSensor
from subarulink.hass.controller import HassController
from subarulink.hass.gps import GPS, Odometer
from subarulink.hass.lock import Lock

__all__ = [
    "Battery",
    "Range",
    "ChargerConnectionSensor",
    "ChargingSensor",
    "ChargerSwitch",
    "Climate",
    "Connection",
    "TempSensor",
    "HassController",
    "SubaruException",
    "GPS",
    "Odometer",
    "Lock",
    "__version__",
]
