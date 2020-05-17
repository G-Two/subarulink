#  SPDX-License-Identifier: Apache-2.0
"""
subarulink.hass - A subpackage intended for Home Assistant integrations.

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
from subarulink.__version__ import __version__
from subarulink.exceptions import SubaruException
from subarulink.hass.binary_sensor import EVChargerConnection
from subarulink.hass.climate import Climate
from subarulink.hass.controller import HassController
from subarulink.hass.device_tracker import GPS
from subarulink.hass.lock import Lock
from subarulink.hass.sensor import (
    AverageMPG,
    Battery,
    EVBattery,
    EVChargeRate,
    EVRange,
    Odometer,
    Range,
    TempSensor,
)
from subarulink.hass.switch import EVChargeSwitch, LocateSwitch

__all__ = [
    "__version__",
    "AverageMPG",
    "Battery",
    "Climate",
    "EVBattery",
    "EVChargeRate",
    "EVChargerConnection",
    "EVChargeSwitch",
    "EVRange",
    "GPS",
    "HassController",
    "LocateSwitch",
    "Lock",
    "Odometer",
    "Range",
    "SubaruException",
    "TempSensor",
]
