#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  SPDX-License-Identifier: Apache-2.0
"""
Python Package for controlling Tesla API.

For more details about this api, please refer to the documentation at
https://github.com/zabuldon/teslajsonpy
"""


class TeslaException(Exception):
    """Class of Tesla API exceptions."""

    def __init__(self, code, *args, **kwargs):
        """Initialize exceptions for the Tesla API."""
        self.message = ""
        super().__init__(*args, **kwargs)
        self.code = code
        if self.code == 401:
            self.message = 'UNAUTHORIZED'
        elif self.code == 404:
            self.message = 'NOT_FOUND'
        elif self.code == 405:
            self.message = 'MOBILE_ACCESS_DISABLED'
        elif self.code == 423:
            self.message = 'ACCOUNT_LOCKED'
        elif self.code == 429:
            self.message = 'TOO_MANY_REQUESTS'
        elif self.code == 500:
            self.message = 'SERVER_ERROR'
        elif self.code == 503:
            self.message = 'SERVICE_MAINTENANCE'
        elif self.code > 299:
            self.message = "UNKNOWN_ERROR"


class RetryLimitError(TeslaException):
    """Class of exceptions for hitting retry limits."""

    def __init__(self, *args, **kwargs):
        # pylint: disable=super-init-not-called
        """Initialize exceptions for the Tesla retry limit API."""
        pass
