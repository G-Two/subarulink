#  SPDX-License-Identifier: Apache-2.0
"""
subarulink - A Python Package for interacting with Subaru Starlink Remote Services API.

For more details, please refer to the documentation at https://github.com/G-Two/subarulink
"""

from subarulink import const
from subarulink.controller import Controller
from subarulink.exceptions import (
    IncompleteCredentials,
    InvalidCredentials,
    InvalidPIN,
    PINLockoutProtect,
    RemoteServiceFailure,
    SubaruException,
    VehicleNotSupported,
)

from .__version__ import __version__

__all__ = [
    "Controller",
    "SubaruException",
    "InvalidCredentials",
    "InvalidPIN",
    "IncompleteCredentials",
    "PINLockoutProtect",
    "RemoteServiceFailure",
    "VehicleNotSupported",
    "const",
    "__version__",
]

__pdoc__ = {"app": False}
