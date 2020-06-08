#  SPDX-License-Identifier: Apache-2.0
"""
An example console application that uses the subarulink package.

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
import argparse
import asyncio
from datetime import datetime
import logging
import os.path
from pprint import pprint
import shelve
import shlex
import sys

from aiohttp import ClientSession
import stdiomask

from subarulink import Controller, SubaruException
import subarulink.const as sc

CONFIG_FILE = ".subarulink.cfg"
LOGGER = logging.getLogger("subarulink")
STREAMHANDLER = logging.StreamHandler()
STREAMHANDLER.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
LOGGER.addHandler(STREAMHANDLER)
LOOP = asyncio.get_event_loop()


class CLI:  # pylint: disable=too-few-public-methods
    """A basic shell for interacting with Subaru's Remote Services API."""

    def __init__(self, config_file):
        """Initialize CLI class for subarulink controller."""
        self._config = {}
        self._get_config(config_file)
        self._ctrl = None
        self._current_vin = None
        self._current_api_gen = None
        self._current_hasEV = None
        self._current_hasRES = None
        self._current_hasRemote = None
        self._session = None
        self._car_data = None
        self._cars = None
        self._hvac_mode = None
        self._hvac_speed = None
        self._hvac_temp = None

    def _get_config(self, config_file):
        """Read config file, or create one with user input."""
        if not os.path.isfile(config_file):
            LOGGER.info("Creating config file: %s", config_file)
        else:
            LOGGER.info("Opening config file: %s", config_file)
        with shelve.open(config_file) as shelf:
            if "username" not in shelf:
                username = input("Enter Subaru Starlink username: ")
            else:
                username = shelf["username"]

            if "password" not in shelf:
                password = stdiomask.getpass("Enter Subaru Starlink password: ")
            else:
                password = shelf["password"]

            if "pin" not in shelf:
                pin = stdiomask.getpass("Enter Subaru Starlink PIN: ")
            else:
                pin = shelf["pin"]

            if "device_name" not in shelf:
                device_name = "subarulink"
                shelf["device_name"] = device_name

            if "device_id" not in shelf:
                device_id = int(datetime.now().timestamp())
                shelf["device_id"] = device_id

            if "save_creds" not in shelf or shelf.get("save_creds") == "N":
                while True:
                    save_creds = input(
                        "Remember these credentials? [Y]es, [N]o, [D]on't ask again > "
                    )
                    if save_creds in ["N", "n", "D", "d"]:
                        shelf["save_creds"] = save_creds
                        break
                    if save_creds in ["Y", "y"]:
                        shelf["save_creds"] = save_creds
                        shelf["username"] = username
                        shelf["password"] = password
                        shelf["pin"] = pin
                        break

            self._config["username"] = username
            self._config["password"] = password
            self._config["pin"] = pin
            self._config["device_name"] = shelf["device_name"]
            self._config["device_id"] = shelf["device_id"]
        os.chmod(config_file, 0o600)

    @property
    def _current_name(self):
        return self._ctrl.vin_to_name(self._current_vin)

    async def _quit(self):
        await self._session.close()
        sys.exit(0)

    async def _vehicle_select(self):
        while True:
            print("\nAvailable Vehicles:")
            for i in range(len(self._cars)):
                print(
                    "[%d] %s (%s)"
                    % (i + 1, self._ctrl.vin_to_name(self._cars[i]), self._cars[i])
                )
            if len(self._cars) == 1:
                selected = 0
            else:
                selected = input("\nSelect Vehicle> ")
                if not selected.isnumeric():
                    continue
                selected = int(selected) - 1
            if selected in range(len(self._cars)):
                self._current_vin = self._cars[selected]
                self._current_hasEV = self._ctrl.get_ev_status(self._current_vin)
                # self._current_hasRES = self._ctrl.get_res(self._current_vin)
                self._current_api_gen = self._ctrl.get_api_gen(self._current_vin)
                if self._current_api_gen == "g2":
                    await self._fetch()
                return

    def _set_hvac_params(self):
        modes = [
            sc.MODE_AUTO,
            sc.MODE_FACE,
            sc.MODE_FEET,
            sc.MODE_SPLIT,
            sc.MODE_FEET_DEFROST,
            sc.MODE_DEFROST,
        ]
        speeds = [
            sc.FAN_SPEED_AUTO,
            sc.FAN_SPEED_LOW,
            sc.FAN_SPEED_MED,
            sc.FAN_SPEED_HI,
        ]

        while True:
            print("Enter temperature (%d-%d):" % (sc.TEMP_MIN, sc.TEMP_MAX))
            self._hvac_temp = input("> ")
            if self._hvac_temp.isnumeric():
                self._hvac_temp = int(self._hvac_temp)
                if sc.TEMP_MIN < self._hvac_temp < sc.TEMP_MAX:
                    break

        self._hvac_mode = _select_from_list("Select mode:", modes)
        self._hvac_speed = _select_from_list("Select fan speed:", speeds)

    async def _hvac(self, args):
        if len(args) == 0:
            print("hvac <set|start|stop>")
        elif args[0] == "set":
            self._set_hvac_params()
        elif args[0] == "stop":
            await self._ctrl.remote_stop(self._current_vin)
        elif args[0] == "start":
            if None in [self._hvac_mode, self._hvac_speed, self._hvac_temp]:
                print("Specify settings with 'hvac set' first.")
            await self._ctrl.remote_start(
                self._current_vin,
                self._hvac_temp,
                self._hvac_mode,
                sc.HEAT_SEAT_OFF,
                sc.HEAT_SEAT_OFF,
                sc.REAR_DEFROST_OFF,
                self._hvac_speed,
                sc.RECIRCULATE_ON,
                sc.REAR_AC_OFF,
            )
        else:
            print("hvac: invalid arg: %s" % args[0])

    def _show(self, args):
        if len(args) != 1:
            print("show <summary|all>")
        elif args[0] == "all":
            pprint(self._car_data)
        elif args[0] == "summary":
            timediff = datetime.now() - datetime.fromtimestamp(
                self._car_data["status"][sc.TIMESTAMP]
            )
            print(
                "\nVehicle last reported data %d days, %d hours, %d minutes ago \n"
                % (
                    timediff.days,
                    timediff.seconds // 3600,
                    (timediff.seconds) // 60 % 60,
                )
            )
            if self._current_hasEV:
                print(
                    "EV Charge: %s%%"
                    % self._car_data["status"][sc.EV_STATE_OF_CHARGE_PERCENT],
                    end="",
                )
                print(
                    "\tAux Battery: %sV" % self._car_data["status"][sc.BATTERY_VOLTAGE]
                )
                print(
                    "EV Plug Status: %s"
                    % self._car_data["status"][sc.EV_IS_PLUGGED_IN],
                    end="",
                )
                print(
                    "EV Distance to Empty: %s miles"
                    % self._car_data["status"][sc.EV_DISTANCE_TO_EMPTY]
                )
            print(
                "Odometer: %0.1f miles"
                % _meters_to_miles(self._car_data["status"][sc.ODOMETER])
            )
            print(
                "External Temp: %0.1f °F"
                % _c_to_f(self._car_data["status"][sc.EXTERNAL_TEMP])
            )
        else:
            print("show: invalid arg: %s" % args[0])

    async def _fetch(self):
        print(
            "\nFetching data for %s..." % self._ctrl.vin_to_name(self._current_vin),
            end="",
            flush=True,
        )
        self._car_data = await self._ctrl.get_data(self._current_vin)
        print("Completed")

    async def _connect(self):
        print("Connecting to Subaru Remote Services API...", end="", flush=True)
        try:
            if await self._ctrl.connect():
                print("Successfully connected")
                self._cars = self._ctrl.get_vehicles()
                await self._vehicle_select()
                if self._current_api_gen == "g2":
                    self._show(["summary"])
                elif self._current_api_gen == "g1":
                    print(
                        "%s is a Generation 1 telematics vehicle which has not been tested."
                        % self._current_name
                    )
                else:
                    print("Unknown telematics version: %s" % self._current_api_gen)
        except SubaruException:
            print("Unable to connect.  Check Username/Password.")
            await self._session.close()
            return False
        return True

    async def _cli_loop(self):
        print("\nEnter a command. For a list of commands, enter '?'.")

        while True:
            print("%s" % self._current_name, end="")
            try:
                cmd, *args = shlex.split(input("> "))
            except ValueError:
                continue

            try:
                if cmd == "quit":
                    await self._quit()

                elif cmd in ["help", "?"]:
                    print("\nCommands:")
                    print("  help    - display this help")
                    print("  vehicle - change vehicle")
                    print("  lock    - lock vehicle doors")
                    print("  unlock  - unlock vehicle doors")
                    print("  lights  - turn on lights")
                    print("  horn    - sound horn")
                    if self._current_api_gen == "g2":
                        print("  show    - show vehicle information")
                        print("  update  - request update from vehicle")
                        print("  fetch   - fetch most recent update")
                        print("  charge  - start EV charging")
                        print("  hvac    - remote HVAC control")
                    print("  quit\n")

                elif cmd == "vehicle":
                    await self._vehicle_select()

                elif cmd == "lock":
                    await self._ctrl.lock(self._current_vin)

                elif cmd == "unlock":
                    await self._ctrl.unlock(self._current_vin)

                elif cmd == "lights":
                    await self._ctrl.lights(self._current_vin)

                elif cmd == "horn":
                    await self._ctrl.horn(self._current_vin)

                elif cmd == "show" and self._current_api_gen == "g2":
                    self._show(args)

                elif cmd == "update" and self._current_api_gen == "g2":
                    await self._ctrl.update(self._current_vin)

                elif cmd == "fetch" and self._current_api_gen == "g2":
                    await self._ctrl.fetch(self._current_vin)

                elif cmd == "charge" and self._current_api_gen == "g2":
                    await self._ctrl.charge_start(self._current_vin)

                elif cmd == "hvac" and self._current_api_gen == "g2":
                    await self._hvac(args)

                else:
                    print("invalid command: {}".format(cmd))

            except SubaruException as exc:
                print(exc.message)

    async def run(self):
        """Initialize connection and start CLI loop."""
        self._session = ClientSession()
        self._ctrl = Controller(
            self._session,
            self._config["username"],
            self._config["password"],
            self._config["device_id"],
            self._config["pin"],
            self._config["device_name"],
        )
        try:
            if await self._connect():
                await self._cli_loop()
        except (KeyboardInterrupt, EOFError):
            await self._quit()


def _meters_to_miles(meters):
    return float(meters) * 0.00062137119


def _c_to_f(temp_c):
    return float(temp_c) * 1.8 + 32.0


def _select_from_list(msg, items):
    while True:
        print(msg)
        for i, val in enumerate(items):
            print(" [%d] %s" % (i + 1, val))
        choice = input("> ")
        if choice.isnumeric():
            choice = int(choice) - 1
            if choice in range(len(items)):
                return items[choice]


def main():
    """Run a basic CLI that uses the subarulink package."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbosity",
        type=int,
        choices=[0, 1, 2],
        default=0,
        help="Verbosity Level: 0=Error[default] 1=Info 2=Debug",
    )
    parser.add_argument(
        "-r", "--reset", help="Reset saved account information", action="store_true"
    )
    args = parser.parse_args()
    if args.verbosity == 1:
        LOGGER.setLevel(logging.INFO)
    elif args.verbosity == 2:
        LOGGER.setLevel(logging.DEBUG)
    else:
        LOGGER.setLevel(logging.ERROR)

    home_dir = os.path.expanduser("~")
    config_file = os.path.join(home_dir, CONFIG_FILE)

    if args.reset:
        if os.path.isfile(config_file):
            os.remove(config_file)
            print("Deleted %s" % config_file)
        else:
            print("Config file %s not found." % config_file)
        sys.exit(0)

    cli = CLI(config_file)
    LOOP.run_until_complete(cli.run())
