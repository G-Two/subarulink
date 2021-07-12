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
import shlex
import sys

from aiohttp import ClientSession
import stdiomask

from subarulink import Controller, SubaruException
import subarulink.const as sc
from subarulink.const import CHARGING, COUNTRY_CAN, COUNTRY_USA, FEATURE_G2_TELEMATICS

CONFIG_FILE = "subarulink.cfg"
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
        self._current_has_ev = None
        self._current_has_res = None
        self._current_has_remote = None
        self._session = None
        self._car_data = None
        self._cars = None

    def _get_config(self):
        """Read config file, or create one with user input."""
        saved_config = {}
        write_config = False

        if os.path.isfile(self._config_file):
            LOGGER.info("Opening config file: %s", self._config_file)
            with open(self._config_file) as infile:
                config_json = infile.read()
            saved_config = json.loads(config_json)
        else:
            write_config = True
        self._config = saved_config

        if "country" not in self._config:
            while True:
                country = input("Select country [CAN, USA]: ").upper()
                if country in [COUNTRY_CAN, COUNTRY_USA]:
                    self._config["country"] = country
                    write_config = True
                    break

        if "username" not in self._config:
            self._config["username"] = input("Enter Subaru Starlink username: ")

        if "password" not in self._config:
            self._config["password"] = stdiomask.getpass("Enter Subaru Starlink password: ")

        if "pin" not in self._config:
            self._config["pin"] = stdiomask.getpass("Enter Subaru Starlink PIN: ")

        self._config["device_name"] = "subarulink"

        if "save_creds" not in self._config or self._config.get("save_creds") == "N":
            while True:
                save_creds = input("Remember these credentials? [Y]es, [N]o, [D]on't ask again > ").upper()
                self._config["save_creds"] = save_creds
                if save_creds == "N":
                    break
                if save_creds == "D":
                    write_config = True
                    break
                if save_creds == "Y":
                    write_config = True
                    break

        if "device_id" not in self._config:
            self._config["device_id"] = int(datetime.now().timestamp())
            write_config = True

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
            LOGGER.info("Saved settings to config file: %s", self._config_file)
        os.chmod(self._config_file, 0o600)

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
                for index, _vin in enumerate(self._cars):
                    print("[%d] %s (%s)" % (index + 1, self._ctrl.vin_to_name(_vin), _vin))
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
            await self._fetch()

        elif vin:
            if vin in self._cars:
                self._current_vin = vin
            else:
                LOGGER.error("VIN %s does not exist in user account.", vin)
                await self._quit(3)

        elif len(self._cars) == 1:
            self._current_vin = self._cars[0]

        elif self._config.get("default_vin") in self._cars:
            self._current_vin = self._config.get("default_vin")

        else:
            LOGGER.error("Multiple vehicles in account but VIN not specified in config or command line")
            await self._quit(1)

        self._current_has_ev = self._ctrl.get_ev_status(self._current_vin)
        self._current_has_res = self._ctrl.get_res_status(self._current_vin)
        self._current_has_remote = self._ctrl.get_remote_status(self._current_vin)
        self._current_api_gen = self._ctrl.get_api_gen(self._current_vin)

    async def _set_climate_params(self):
        if self._config["country"] == sc.COUNTRY_CAN:
            temp_field = sc.TEMP_C
            temp_min = sc.TEMP_C_MIN
            temp_max = sc.TEMP_C_MAX
        else:
            temp_field = sc.TEMP_F
            temp_min = sc.TEMP_F_MIN
            temp_max = sc.TEMP_F_MAX
        while True:
            print("Enter temperature (%d-%d):" % (temp_min, temp_max))
            set_temp = input("> ")
            if set_temp.isnumeric():
                if temp_min <= int(set_temp) <= temp_max:
                    break

        self._config["climate"] = {}
        self._config["climate"][temp_field] = set_temp
        self._config["climate"][sc.MODE] = _select_from_list("Select mode:", sc.VALID_CLIMATE_OPTIONS[sc.MODE])
        self._config["climate"][sc.FAN_SPEED] = _select_from_list(
            "Select fan speed:", sc.VALID_CLIMATE_OPTIONS[sc.FAN_SPEED]
        )
        self._config["climate"][sc.HEAT_SEAT_LEFT] = _select_from_list(
            "Driver seat heat:", sc.VALID_CLIMATE_OPTIONS[sc.HEAT_SEAT_LEFT]
        )
        self._config["climate"][sc.HEAT_SEAT_RIGHT] = _select_from_list(
            "Passenger seat heat:", sc.VALID_CLIMATE_OPTIONS[sc.HEAT_SEAT_RIGHT]
        )
        self._config["climate"][sc.REAR_DEFROST] = _select_from_list(
            "Rear defroster:", sc.VALID_CLIMATE_OPTIONS[sc.REAR_DEFROST]
        )
        self._config["climate"][sc.RECIRCULATE] = _select_from_list(
            "Recirculate:", sc.VALID_CLIMATE_OPTIONS[sc.RECIRCULATE]
        )
        self._config["climate"][sc.REAR_AC] = _select_from_list("Rear AC:", sc.VALID_CLIMATE_OPTIONS[sc.REAR_AC])
        save = _select_from_list("Save climate settings?", ["Yes", "No"])
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

    def _summary_data(self):
        """Get printable vehicle summary data."""
        timediff = datetime.now() - datetime.fromtimestamp(self._car_data["status"][sc.TIMESTAMP])
        lines = []
        lines.append(
            "\nVehicle last reported data %d days, %d hours, %d minutes ago\n"
            % (
                timediff.days,
                timediff.seconds // 3600,
                (timediff.seconds) // 60 % 60,
            )
        )
        # Safety Plus Data
        lines.append("Odometer: %0.1f miles" % _km_to_miles(self._car_data["status"][sc.ODOMETER]))

        # Safety Plus + G2 Data
        if self._current_api_gen == FEATURE_G2_TELEMATICS:
            lines.append("Distance to Empty: %d miles" % _km_to_miles(self._car_data["status"][sc.DIST_TO_EMPTY]))
            lines.append(
                "Average Fuel Consumption: %d MPG"
                % _liters_per_100km_to_mpg(self._car_data["status"][sc.AVG_FUEL_CONSUMPTION])
            )
            lines.append("Vehicle State: %s" % self._car_data["status"][sc.VEHICLE_STATE])
            lines.append("Tire Pressures (psi):")
            lines.append(
                "  FL: %d   FR: %d "
                % (
                    _kpa_to_psi(self._car_data["status"][sc.TIRE_PRESSURE_FL]),
                    _kpa_to_psi(self._car_data["status"][sc.TIRE_PRESSURE_FR]),
                )
            )
            lines.append(
                "  RL: %d   RR: %d "
                % (
                    _kpa_to_psi(self._car_data["status"][sc.TIRE_PRESSURE_RL]),
                    _kpa_to_psi(self._car_data["status"][sc.TIRE_PRESSURE_RR]),
                )
            )

        # Lat/Long assumes North America hemispheres since Starlink is a Subaru of America thing
        if self._car_data["status"].get(sc.LATITUDE) and self._car_data["status"].get(sc.LONGITUDE):
            lines.append(
                "Position: %f°N  %f°W  Heading: %d"
                % (
                    self._car_data["status"].get(sc.LATITUDE),
                    (self._car_data["status"].get(sc.LONGITUDE) or 0) * -1,
                    (self._car_data["status"].get(sc.HEADING) or 0),
                )
            )

        # Security Plus Data
        if self._current_has_remote and self._current_api_gen == FEATURE_G2_TELEMATICS:
            lines.append("12V Battery: %sV" % self._car_data["status"].get(sc.BATTERY_VOLTAGE))
            if sc.EXTERNAL_TEMP in self._car_data["status"]:
                lines.append("External Temp: %0.1f °F" % _c_to_f(self._car_data["status"][sc.EXTERNAL_TEMP]))
            else:
                lines.append("External Temp: Unknown")

        # EV Data
        if self._current_has_ev:
            lines.append("EV Charge: %s%%" % self._car_data["status"][sc.EV_STATE_OF_CHARGE_PERCENT])
            lines.append("EV Distance to Empty: %s miles" % self._car_data["status"][sc.EV_DISTANCE_TO_EMPTY])
            lines.append("EV Plug Status: %s" % self._car_data["status"][sc.EV_IS_PLUGGED_IN])
            lines.append("EV Charge Status: %s" % self._car_data["status"][sc.EV_CHARGER_STATE_TYPE])
            if self._car_data["status"][sc.EV_CHARGER_STATE_TYPE] == CHARGING:
                finish_time = datetime.fromisoformat(self._car_data["status"][sc.EV_TIME_TO_FULLY_CHARGED_UTC])
                time_left = finish_time - datetime.now()
                lines.append(
                    "EV Time to Fully Charged: %s (%d minutes left)" % (finish_time, time_left.total_seconds() // 60)
                )
        return lines

    def _show(self, args):
        if len(args) != 1:
            print("\nshow [summary|all]")
            print("  summary - display summary information")
            print("  all     - display all data available\n")
        elif args[0] == "all":
            pprint(self._car_data)
        elif args[0] == "summary":
            print("\n".join(self._summary_data()))
        else:
            print("show: invalid arg: %s" % args[0])

    async def _fetch(self):
        LOGGER.info("Fetching data for %s...", self._ctrl.vin_to_name(self._current_vin))
        await self._ctrl.fetch(self._current_vin, force=True)
        self._car_data = await self._ctrl.get_data(self._current_vin)
        return True

    async def _connect(self, interactive=True, vin=None):
        LOGGER.info("Connecting to Subaru Remote Services API")
        try:
            if await self._ctrl.connect():
                LOGGER.info("Successfully connected")
                self._cars = self._ctrl.get_vehicles()
                await self._vehicle_select(interactive, vin)
                if interactive:
                    self._show(["summary"])
                elif not interactive:
                    pass
        except SubaruException as ex:
            LOGGER.error("Unable to connect: %s", ex.message)
            await self._session.close()
            return False
        return True

    async def _cli_loop(self):
        print("\nEnter a command. For a list of commands, enter '?'.")
        running = True

        while running:
            print("%s" % self._current_name, end="")
            try:
                cmd, *args = shlex.split(input("> "))
            except ValueError:
                continue

            try:
                if cmd == "quit":
                    await self._session.close()
                    running = False

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
                    print("  fetch        - fetch most recent update")
                    print("  show         - show vehicle information")
                    if self._current_has_remote:
                        print("  update       - request update from vehicle")
                    if self._current_has_ev:
                        print("  charge       - start EV charging")
                    if self._current_has_res or self._current_has_ev:
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

                elif cmd == "show":
                    self._show(args)

                elif cmd == "update" and self._current_has_remote:
                    await self._ctrl.update(self._current_vin, force=True)
                    await self._fetch()

                elif cmd == "fetch":
                    await self._fetch()

                elif cmd == "charge" and self._current_has_ev:
                    await self._ctrl.charge_start(self._current_vin)

                elif cmd == "remote_start" and (self._current_has_res or self._current_has_ev):
                    await self._remote_start(args)

                else:
                    print(f"invalid command: {cmd}")

            except SubaruException as exc:
                LOGGER.error("SubaruException caught: %s", exc.message)

    def _init_controller(self):
        self._session = ClientSession()
        self._ctrl = Controller(
            self._session,
            self._config["username"],
            self._config["password"],
            self._config["device_id"],
            self._config["pin"],
            self._config["device_name"],
            country=self._config["country"],
        )

    async def run(self):
        """Initialize connection and start CLI loop."""
        self._init_controller()
        try:
            if await self._connect():
                await self._cli_loop()
        except (KeyboardInterrupt, EOFError):
            await self._quit(0)

    async def single_command(self, cmd, vin):
        """Initialize connection and execute as single command."""
        success = False
        self._init_controller()
        if await self._connect(interactive=False, vin=vin):
            try:
                if cmd == "status":
                    success = await self._fetch()
                    pprint(self._car_data)

                elif cmd == "summary":
                    success = await self._fetch()
                    print("\n".join(self._summary_data()), "\n")

                elif cmd == "lock":
                    success = await self._ctrl.lock(self._current_vin)

                elif cmd == "unlock":
                    success = await self._ctrl.unlock(self._current_vin)

                elif cmd == "lights":
                    success = await self._ctrl.lights(self._current_vin)

                elif cmd == "horn":
                    success = await self._ctrl.horn(self._current_vin)

                elif cmd == "locate":
                    success = await self._ctrl.update(self._current_vin, force=True)
                    await self._fetch()
                    print(f"Longitude:\t{self._car_data['status'].get('longitude')}")
                    print(f"Latitude:\t{self._car_data['status'].get('latitude')}")
                    print(f"Heading:\t{self._car_data['status'].get('heading')}")

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
            print(f"{OK}Command '{cmd}' completed for {self._ctrl.vin_to_name(self._current_vin)}{ENDC}")
            sys.exit(0)
        else:
            print(f"{FAIL}Command '{cmd}' failed for {self._ctrl.vin_to_name(self._current_vin)}{ENDC}")
            sys.exit(1)


def _km_to_miles(meters):
    return float(meters or 0) * 0.62137119


def _c_to_f(temp_c):
    return float(temp_c or 0) * 1.8 + 32.0


def _liters_per_100km_to_mpg(liters_per_100km):
    if liters_per_100km:
        return round(235.215 / liters_per_100km, 1)
    return 0


def _kpa_to_psi(kpa):
    return (kpa or 0) / 68.95


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


def get_default_config_file():
    """
    Get the default config file for subarulink.

    If there is a config file located in home directory, use it.
    Otherwise use the subarulink directory within $XDG_CONFIG_PATH (~/.config for default).
    """
    home_dir = os.path.expanduser("~")
    home_config_file = os.path.join(home_dir, "".join((".", CONFIG_FILE)))
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME", os.path.join(home_dir, ".config"))
    xdg_config_path = os.path.join(xdg_config_home, "subarulink")
    xdg_config_file = os.path.join(xdg_config_path, CONFIG_FILE)

    if os.path.exists(home_config_file):
        config_file = home_config_file
    else:
        # Create the directory structure if it doesn't exist.
        os.makedirs(xdg_config_path, exist_ok=True)
        config_file = xdg_config_file
    return config_file


def main():
    """Run a basic CLI that uses the subarulink package."""
    default_config = get_default_config_file()

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(title="command", description="execute single command and exit", dest="command")
    status_command = subparsers.add_parser("status", help="get vehicle status information")
    status_command.add_argument("--vin", required=False, help="VIN (required if not specified in config file)")
    summary_command = subparsers.add_parser("summary", help="Get vehicle summary information.")
    summary_command.add_argument("--vin", required=False, help="VIN (required if not specified in config file)")
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

    parser.add_argument(
        "-i",
        "--interactive",
        help="interactive mode",
        action="store_true",
        dest="interactive",
    )
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
                "Config file '%s' not found.  Please run interactively once before using single command mode.",
                args.config_file,
            )
            sys.exit(2)
        LOGGER.info("Entering Single command mode: cmd=%s, vin=%s", args.command, args.vin)
        cli = CLI(args.config_file)
        LOOP.run_until_complete(cli.single_command(args.command, args.vin))
    if args.interactive:
        LOGGER.info("Entering interactive mode")
        cli = CLI(args.config_file)
        LOOP.run_until_complete(cli.run())
    else:
        parser.print_help()
