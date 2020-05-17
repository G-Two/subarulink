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

    def __init__(self, *args, **kwargs):
        # pylint: disable=super-init-not-called
        """Initialize exception."""
        pass


class RetryLimitError(SubaruException):
    """Class of exceptions for hitting retry limits."""

    def __init__(self, *args, **kwargs):
        # pylint: disable=super-init-not-called
        """Initialize exception."""
        pass


class IncompleteCredentials(SubaruException):
    """Class of exceptions for hitting retry limits."""

    def __init__(self, *args, **kwargs):
        # pylint: disable=super-init-not-called
        """Initialize exception."""
        pass
