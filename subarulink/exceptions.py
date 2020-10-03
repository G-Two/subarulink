#  SPDX-License-Identifier: Apache-2.0
"""
subarulink - A Python Package for interacting with Subaru Starlink Remote Services API.

exceptions.py - provides exceptions specific to the package

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
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
