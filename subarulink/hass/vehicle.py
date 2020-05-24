#  SPDX-License-Identifier: Apache-2.0
"""
subarulink.hass - A subpackage intended for Home Assistant integrations.

vehicle.py - implements Subaru device base class for Home Assistant

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
import logging

_LOGGER = logging.getLogger(__name__)


class VehicleDevice:
    """Home-assistant class of Subaru vehicles.

    This is intended to be partially inherited by a Home-Assitant entity.
    """

    def __init__(self, data, controller):
        """Initialize the Vehicle.

        Parameters
        ----------
        data : dict
            Identifier info for a Subaru vehicle.
        controller : subarulink.Controller
            The controller that controls updates to the Subaru API.

        Returns
        -------
        None

        """
        self._id = data["id"]
        self._display_name = data["display_name"]
        self._vin = data["vin"]
        self._controller = controller
        self.should_poll = True
        self.type = "device"

    def _name(self):
        return "{} {}".format(self._display_name, self.type)

    def _uniq_name(self):
        return "Subaru Model {} {} {}".format(
            str(self._vin[3]).upper(), self._vin[-6:], self.type
        )

    def id(self):
        # pylint: disable=invalid-name
        """Return the id of this Vehicle."""
        return self._id

    def car_name(self):
        """Return the car name of this Vehicle."""
        return self._display_name

    def vin(self):
        """Return the VIN of this Vehicle."""
        return self._vin

    async def async_update(self):
        """Update the car."""
        await self._controller.hass_update(self._vin)
