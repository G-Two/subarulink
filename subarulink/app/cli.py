#  SPDX-License-Identifier: Apache-2.0
"""
An example console application that uses the subarulink package.

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
import argparse
import asyncio
from datetime import datetime
import json
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
STREAMHANDLER.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
LOGGER.addHandler(STREAMHANDLER)
LOOP = asyncio.get_event_loop()

OK = "\033[92m"
WARNING = "\033[93m"
FAIL = "\033[91m"
ENDC = "\033[0m"


class CLI:  # pylint: disable=too-few-public-methods
    """A basic shell for interacting with Subaru's Remote Services API."""

    def __init__(self, config_file):
        """Initialize CLI class for subarulink controller."""
        self._config = {}
        self._config_file = config_file
        self._get_config()
        self._ctrl = None
        self._current_vin = None
        self._current_api_gen = None
        self._current_hasEV = None
        self._current_hasRES = None
        self._current_hasRemote = None
        self._session = None
        self._car_data = None
        self._cars = None

    def _get_config(self):
        """Read config file, or create one with user input."""
        saved_config = {}
        write_config = False

        if os.path.isfile(self._config_file):
            LOGGER.info("Opening config file: %s", self._config_file)
            try:
                infile = open(self._config_file, "r")
                config_json = infile.read()
            except UnicodeDecodeError:
                # Update previous version's shelve config file to json
                LOGGER.warning(f"Updating {self._config_file} to JSON format.")
                infile.close()
                self._convert_to_json(self._config_file)
                infile = open(self._config_file, "r")
                config_json = infile.read()
            infile.close()
            saved_config = json.loads(config_json)
        else:
            write_config = True

        self._config = saved_config

        if "username" not in self._config:
            self._config["username"] = input("Enter Subaru Starlink username: ")

        if "password" not in self._config:
            self._config["password"] = stdiomask.getpass("Enter Subaru Starlink password: ")

        if "pin" not in self._config:
            self._config["pin"] = stdiomask.getpass("Enter Subaru Starlink PIN: ")

        if "device_id" not in self._config:
            self._config["device_id"] = int(datetime.now().timestamp())
            write_config = True

        self._config["device_name"] = "subarulink"

        if "save_creds" not in self._config or self._config.get("save_creds") == "N":
            while True:
                save_creds = input("Remember these credentials? [Y]es, [N]o, [D]on't ask again > ")
                if save_creds in ["N", "n"]:
                    break
                if save_creds in ["D", "d"]:
                    saved_config["save_creds"] = save_creds
                    write_config = True
                    break
                if save_creds in ["Y", "y"]:
                    saved_config["save_creds"] = save_creds
                    saved_config["username"] = self._config["username"]
                    saved_config["password"] = self._config["password"]
                    saved_config["pin"] = self._config["pin"]
                    write_config = True
                    break

        if write_config:
            self._save_config()

    def _save_config(self):
        config_to_save = self._config.copy()

        if config_to_save.get("save_creds") not in ["Y", "y"]:
            config_to_save.pop("username")
            config_to_save.pop("password")
            config_to_save.pop("pin")

        with open(self._config_file, "w") as outfile:
            outfile.write(json.dumps(config_to_save))
            LOGGER.info(f"Saved settings to config file: {self._config_file}")
        os.chmod(self._config_file, 0o600)

    def _convert_to_json(self, config_file):
        old_config = {}
        with shelve.open(config_file) as shelf:
            if "username" in shelf:
                old_config["username"] = shelf["username"]
            if "password" in shelf:
                old_config["password"] = shelf["password"]
            if "pin" in shelf:
                old_config["pin"] = shelf["pin"]
            old_config["device_name"] = "subarulink"
            if "device_id" in shelf:
                old_config["device_id"] = shelf["device_id"]
            if "save_creds" in shelf:
                old_config["save_creds"] = shelf["save_creds"]

        os.remove(config_file)
        LOGGER.warning("Deleted %s" % config_file)
        with open(config_file, "w") as outfile:
            outfile.write(json.dumps(old_config))
        LOGGER.info("Saved config file: %s", config_file)
        os.chmod(config_file, 0o600)

    @property
    def _current_name(self):
        return self._ctrl.vin_to_name(self._current_vin)

    async def _quit(self, code):
        await self._session.close()
        sys.exit(code)

    async def _vehicle_select(self, interactive=True, vin=None, reselect=False):
        if (interactive and self._config.get("default_vin") is None) or reselect:
            while True:
                selected = -1
                print("\nAvailable Vehicles:")
                for i in range(len(self._cars)):
                    print("[%d] %s (%s)" % (i + 1, self._ctrl.vin_to_name(self._cars[i]), self._cars[i]))
                if len(self._cars) == 1:
                    selected = 0
                if selected == -1:
                    selected = input("\nSelect Vehicle> ")
                    if not selected.isnumeric():
                        continue
                    selected = int(selected) - 1
                if selected in range(len(self._cars)):
                    break

            self._current_vin = self._cars[selected]

        elif vin:
            if vin in self._cars:
                self._current_vin = vin
            else:
                LOGGER.error(f"VIN {vin} does not exist in user account.")
                await self._quit(3)

        elif len(self._cars) == 1:
            self._current_vin = self._cars[0]

        elif self._config.get("default_vin") in self._cars:
            self._current_vin = self._config.get("default_vin")

        else:
            LOGGER.error("Multiple vehicles in account but VIN not specified in config or command line")
            await self._quit(1)

        self._current_hasEV = self._ctrl.get_ev_status(self._current_vin)
        self._current_hasRES = self._ctrl.get_res_status(self._current_vin)
        self._current_hasRemote = self._ctrl.get_remote_status(self._current_vin)
        self._current_api_gen = self._ctrl.get_api_gen(self._current_vin)

    async def _set_climate_params(self):
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
        seat_heat = [sc.HEAT_SEAT_OFF, sc.HEAT_SEAT_LOW, sc.HEAT_SEAT_MED, sc.HEAT_SEAT_HI]
        defrost = [sc.REAR_DEFROST_OFF, sc.REAR_DEFROST_ON]
        recirculate = [sc.RECIRCULATE_OFF, sc.RECIRCULATE_ON]
        rear_ac = [sc.REAR_AC_OFF, sc.REAR_AC_ON]
        self._config["hvac"] = {}
        while True:
            print("Enter temperature (%d-%d):" % (sc.TEMP_MIN, sc.TEMP_MAX))
            hvac_temp = input("> ")
            if hvac_temp.isnumeric():
                if sc.TEMP_MIN < int(hvac_temp) < sc.TEMP_MAX:
                    break

        self._config["climate"] = {}
        self._config["climate"][sc.TEMP] = hvac_temp
        self._config["climate"][sc.MODE] = _select_from_list("Select mode:", modes)
        self._config["climate"][sc.FAN_SPEED] = _select_from_list("Select fan speed:", speeds)
        self._config["climate"][sc.HEAT_SEAT_LEFT] = _select_from_list("Driver seat heat:", seat_heat)
        self._config["climate"][sc.HEAT_SEAT_RIGHT] = _select_from_list("Passenger seat heat:", seat_heat)
        self._config["climate"][sc.REAR_DEFROST] = _select_from_list("Rear defroster:", defrost)
        self._config["climate"][sc.RECIRCULATE] = _select_from_list("Recirculate:", recirculate)
        self._config["climate"][sc.REAR_AC] = _select_from_list("Rear AC:", rear_ac)
        save = _select_from_list("Save HVAC settings?", ["Yes", "No"])
        if save == "Yes":
            pprint(self._config["climate"])
            await self._ctrl.save_climate_settings(self._current_vin, self._config["climate"])

    async def _fetch_climate_settings(self):
        success = await self._ctrl.get_climate_settings(self._current_vin)
        if success:
            await self._fetch()
            pprint(self._car_data["climate"])

    async def _remote_start(self, args):
        if len(args) == 0:
            print("\nremote_start [set|show|start|stop]")
            print("  set   - enter climate settings")
            print("  show  - show saved climate settings")
            print("  on    - start engine")
            print("  off   - stop engine\n")
        elif args[0] == "set":
            await self._set_climate_params()
        elif args[0] == "show":
            await self._fetch_climate_settings()
        elif args[0] == "off":
            await self._ctrl.remote_stop(self._current_vin)
        elif args[0] == "on":
            if self._car_data.get("climate") is None:
                await self._fetch_climate_settings()
            await self._ctrl.remote_start(self._current_vin, self._car_data["climate"])
        else:
            print("remote_start: invalid arg: %s" % args[0])

    def _show(self, args):
        if len(args) != 1:
            print("\nshow [summary|all]")
            print("  summary - display summary information")
            print("  all     - display all data available\n")
        elif args[0] == "all":
            pprint(self._car_data)
        elif args[0] == "summary":
            timediff = datetime.now() - datetime.fromtimestamp(self._car_data["status"][sc.TIMESTAMP])
            print(
                "\nVehicle last reported data %d days, %d hours, %d minutes ago \n"
                % (timediff.days, timediff.seconds // 3600, (timediff.seconds) // 60 % 60,)
            )
            # Safety Plus Data
            print("Odometer: %0.1f miles" % _km_to_miles(self._car_data["status"][sc.ODOMETER]))
            print("Distance to Empty: %d miles" % _km_to_miles(self._car_data["status"][sc.DIST_TO_EMPTY]))
            print(
                "Average Fuel Consumption: %d MPG" % _L100km_to_mpg(self._car_data["status"][sc.AVG_FUEL_CONSUMPTION])
            )
            # Lat/Long assumes North America hemispheres since Starlink is a Subaru of America thing
            if self._car_data["status"].get(sc.LATITUDE) and self._car_data["status"].get(sc.LONGITUDE):
                print(
                    "Position: %f°N  %f°W  Heading: %d"
                    % (
                        self._car_data["status"].get(sc.LATITUDE),
                        (self._car_data["status"].get(sc.LONGITUDE) or 0) * -1,
                        (self._car_data["status"].get(sc.HEADING) or 0),
                    )
                )
            print("Vehicle State: %s" % self._car_data["status"][sc.VEHICLE_STATE])
            print("Tire Pressures (psi):")
            print(
                "  FL: %d   FR: %d "
                % (
                    _kpa_to_psi(self._car_data["status"][sc.TIRE_PRESSURE_FL]),
                    _kpa_to_psi(self._car_data["status"][sc.TIRE_PRESSURE_FR]),
                )
            )
            print(
                "  RL: %d   RR: %d "
                % (
                    _kpa_to_psi(self._car_data["status"][sc.TIRE_PRESSURE_RL]),
                    _kpa_to_psi(self._car_data["status"][sc.TIRE_PRESSURE_RR]),
                )
            )

            # Security Plus Data
            if self._current_hasRemote:
                print("External Temp: %0.1f °F" % _c_to_f(self._car_data["status"][sc.EXTERNAL_TEMP]))

            # EV Data
            if self._current_hasEV:
                print("EV Charge: %s%%" % self._car_data["status"][sc.EV_STATE_OF_CHARGE_PERCENT])
                print("Aux Battery: %sV" % self._car_data["status"][sc.BATTERY_VOLTAGE])
                print("EV Plug Status: %s" % self._car_data["status"][sc.EV_IS_PLUGGED_IN])
                print("EV Distance to Empty: %s miles" % self._car_data["status"][sc.EV_DISTANCE_TO_EMPTY])
        else:
            print("show: invalid arg: %s" % args[0])

    async def _fetch(self):
        LOGGER.info("Fetching data for %s..." % self._ctrl.vin_to_name(self._current_vin))
        self._car_data = await self._ctrl.get_data(self._current_vin)
        return True

    async def _connect(self, interactive=True, vin=None):
        LOGGER.info("Connecting to Subaru Remote Services API")
        try:
            if await self._ctrl.connect():
                LOGGER.info("Successfully connected")
                self._cars = self._ctrl.get_vehicles()
                await self._vehicle_select(interactive, vin)
                if interactive and self._current_api_gen == "g2":
                    await self._fetch()
                    self._show(["summary"])
                elif self._current_api_gen == "g1":
                    LOGGER.warning(
                        "%s is a Generation 1 telematics vehicle which has not been tested." % self._current_name
                    )
                elif not interactive:
                    pass
                else:
                    LOGGER.error("Unknown telematics version: %s" % self._current_api_gen)
        except SubaruException as ex:
            LOGGER.error("Unable to connect: %s" % ex.message)
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
                    await self._quit(0)

                elif cmd in ["help", "?"]:
                    print("\nCommands:")
                    print("  help         - display this help")
                    if len(self._cars) > 1:
                        print("  vehicle      - change vehicle")
                        print("  default      - set this vehicle as default")
                    print("  lock         - lock vehicle doors")
                    print("  unlock       - unlock vehicle doors")
                    print("  lights       - turn on lights")
                    print("  horn         - sound horn")
                    if self._current_api_gen == "g2":
                        print("  show         - show vehicle information")
                        print("  update       - request update from vehicle")
                        print("  fetch        - fetch most recent update")
                    if self._current_hasEV:
                        print("  charge       - start EV charging")
                    if self._current_hasRES or self._current_hasEV:
                        print("  remote_start - remote start")
                    print("  quit\n")

                elif cmd == "vehicle":
                    await self._vehicle_select(reselect=True)

                elif cmd == "default":
                    self._config["default_vin"] = self._current_vin
                    self._save_config()

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
                    await self._fetch()

                elif cmd == "fetch" and self._current_api_gen == "g2":
                    await self._fetch()

                elif cmd == "charge" and self._current_hasEV:
                    await self._ctrl.charge_start(self._current_vin)

                elif cmd == "remote_start" and (self._current_hasRES or self._current_hasEV):
                    await self._remote_start(args)

                else:
                    print("invalid command: {}".format(cmd))

            except SubaruException as exc:
                LOGGER.error("SubaruException caught: %s", exc.message)

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
            await self._quit(0)

    async def single_command(self, cmd, vin):
        """Initialize connection and execute as single command."""
        success = False
        self._session = ClientSession()
        self._ctrl = Controller(
            self._session,
            self._config["username"],
            self._config["password"],
            self._config["device_id"],
            self._config["pin"],
            self._config["device_name"],
        )

        if await self._connect(interactive=False, vin=vin):
            try:
                if cmd == "status":
                    success = await self._fetch()
                    pprint(self._car_data)

                elif cmd == "lock":
                    success = await self._ctrl.lock(self._current_vin)

                elif cmd == "unlock":
                    success = await self._ctrl.unlock(self._current_vin)

                elif cmd == "lights":
                    success = await self._ctrl.lights(self._current_vin)

                elif cmd == "horn":
                    success = await self._ctrl.horn(self._current_vin)

                elif cmd == "locate":
                    success = await self._ctrl.update(self._current_vin)
                    await self._fetch()
                    pprint(self._car_data.get("location"))

                elif cmd == "remote_start":
                    success = await self._ctrl.remote_start(self._current_vin)

                elif cmd == "remote_stop":
                    success = await self._ctrl.remote_stop(self._current_vin)

                elif cmd == "charge":
                    success = await self._ctrl.charge_start(self._current_vin)

                else:
                    LOGGER.error("Unsupported command")

            except SubaruException as exc:
                LOGGER.error("SubaruException caught: %s", exc.message)

        if success:
            print(f"{OK}Command '{cmd}' completed for {self._current_vin}{ENDC}")
            sys.exit(0)
        else:
            print(f"{FAIL}Command '{cmd}' failed for {self._current_vin}{ENDC}")
            sys.exit(1)


def _km_to_miles(meters):
    return float(meters) * 0.62137119


def _c_to_f(temp_c):
    return float(temp_c) * 1.8 + 32.0


def _L100km_to_mpg(L100km):
    return round(235.215 / L100km, 1)


def _kpa_to_psi(kpa):
    return kpa / 68.95


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
    home_dir = os.path.expanduser("~")
    default_config = os.path.join(home_dir, CONFIG_FILE)

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title="command", description="execute single command and exit", dest="command")
    status_command = subparsers.add_parser("status", help="get vehicle status information")
    status_command.add_argument("--vin", required=False, help="VIN (required if not specified in config file)")
    lock_command = subparsers.add_parser("lock", help="lock doors")
    lock_command.add_argument("--vin", required=False, help="VIN (required if not specified in config file)")
    unlock_command = subparsers.add_parser("unlock", help="unlock doors")
    unlock_command.add_argument("--vin", required=False, help="VIN (required if not specified in config file)")
    lights_command = subparsers.add_parser("lights", help="turn on lights")
    lights_command.add_argument("--vin", required=False, help="VIN (required if not specified in config file)")
    horn_command = subparsers.add_parser("horn", help="sound horn")
    horn_command.add_argument("--vin", required=False, help="VIN (required if not specified in config file)")
    locate_command = subparsers.add_parser("locate", help="locate vehicle")
    locate_command.add_argument("--vin", required=False, help="VIN (required if not specified in config file)")
    start_command = subparsers.add_parser("remote_start", help="remote engine start")
    start_command.add_argument("--vin", required=False, help="VIN (required if not specified in config file)")
    stop_command = subparsers.add_parser("remote_stop", help="remote engine stop")
    stop_command.add_argument("--vin", required=False, help="VIN (required if not specified in config file)")
    charge_command = subparsers.add_parser("charge", help="start PHEV charging")
    charge_command.add_argument("--vin", required=False, help="VIN (required if not specified in config file)")

    parser.add_argument("-i", "--interactive", help="interactive mode", action="store_true", dest="interactive")
    parser.add_argument(
        "-c",
        "--config",
        default=default_config,
        help=f"specify config file (default is {default_config}",
        dest="config_file",
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        type=int,
        choices=[0, 1, 2],
        default=0,
        help="verbosity level: 0=error[default] 1=info 2=debug",
    )

    args = parser.parse_args()

    if args.verbosity == 1:
        LOGGER.setLevel(logging.INFO)
    elif args.verbosity == 2:
        LOGGER.setLevel(logging.DEBUG)
    else:
        LOGGER.setLevel(logging.ERROR)

    if args.interactive and args.command:
        print("Error - Cannot select both interactive mode and single command mode")
        sys.exit(4)

    if args.command:
        if not os.path.isfile(args.config_file):
            LOGGER.error(
                f"Config file '{args.config_file}' not found.  Please run interactively once before using single command mode."
            )
            sys.exit(2)
        LOGGER.info(f"Entering Single command mode: cmd={args.command}, vin={args.vin}")
        cli = CLI(args.config_file)
        LOOP.run_until_complete(cli.single_command(args.command, args.vin))
    if args.interactive:
        LOGGER.info("Entering interactive mode")
        cli = CLI(args.config_file)
        LOOP.run_until_complete(cli.run())
    else:
        parser.print_help()
