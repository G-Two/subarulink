#  SPDX-License-Identifier: Apache-2.0
"""
Provides exceptions specific to the subarulink package.

For more details, please refer to the documentation at https://github.com/G-Two/subarulink
"""


class SubaruException(Exception):
    """Class of Subaru API exceptions."""

    def __init__(self, message, *args, **kwargs):
        """Initialize exceptions for the Subaru Starlink API."""
        self.message = message
        super().__init__(*args, **kwargs)


class InvalidPIN(SubaruException):
    """Class of exceptions for invalid PIN number."""


class IncompleteCredentials(SubaruException):
    """Class of exceptions for not providing required credentials."""


class InvalidCredentials(SubaruException):
    """Class of exceptions for attempting to login with invalid credentials."""


class PINLockoutProtect(SubaruException):
    """Class of exception to notify previous invalid PIN is not being used to avoid account lockout."""


class VehicleNotSupported(SubaruException):
    """Class of exception when service requested is not supported by vehicle/subscription."""


class RemoteServiceFailure(SubaruException):
    """Class of exception when remote service fails."""
