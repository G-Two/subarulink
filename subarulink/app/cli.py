#  SPDX-License-Identifier: Apache-2.0
"""
An example console application that uses the subarulink package.

For more details about this api, please refer to the documentation at
https://github.com/G-Two/subarulink
"""
import argparse
import asyncio
from datetime import datetime, timezone
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
CONFIG_CLIMATE_PRESET = "remote_start_preset"


class CLI:  # pylint: disable=too-few-public-methods
    """A basic shell for interacting with Subaru's Remote Services API."""

    def __init__(self, config_file):
        """Initialize CLI class for subarulink controller."""
        self.config = {}
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
        self.config = saved_config

        if "country" not in self.config:
            while True:
                country = input("Select country [CAN, USA]: ").upper()
                if country in [COUNTRY_CAN, COUNTRY_USA]:
                    self.config["country"] = country
                    write_config = True
                    break

        if "username" not in self.config:
            self.config["username"] = input("Enter Subaru Starlink username: ")

        if "password" not in self.config:
            self.config["password"] = stdiomask.getpass("Enter Subaru Starlink password: ")

        if "pin" not in self.config:
            self.config["pin"] = stdiomask.getpass("Enter Subaru Starlink PIN: ")

        self.config["device_name"] = "subarulink"

        if "save_creds" not in self.config or self.config.get("save_creds") == "N":
            while True:
                save_creds = input("Remember these credentials? [Y]es, [N]o, [D]on't ask again > ").upper()
                self.config["save_creds"] = save_creds
                if save_creds == "N":
                    break
                if save_creds == "D":
                    write_config = True
                    break
                if save_creds == "Y":
                    write_config = True
                    break

        if "device_id" not in self.config:
            self.config["device_id"] = int(datetime.now().timestamp())
            write_config = True

        if write_config:
            self._save_config()

    def _save_config(self):
        config_to_save = self.config.copy()

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
        if len(self._cars) == 0:
            LOGGER.error(
                "No vehicles are associated with this account. If this is incorrect, there may be a temporary issue with the Subaru API. Please try again."
            )
            await self._quit(1)

        elif len(self._cars) == 1:
            self._current_vin = self._cars[0]

        elif (interactive and self.config.get("default_vin") is None) or reselect:
            while True:
                selected = -1
                print("\nAvailable Vehicles:")
                for index, _vin in enumerate(self._cars):
                    print(
                        f"[{index + 1}] {self._ctrl.vin_to_name(_vin)} ({_vin}) - {self._ctrl.get_model_year(_vin)} {self._ctrl.get_model_name(_vin)}"
                    )
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
                LOGGER.error("VIN %s does not exist in user account.", vin)
                await self._quit(1)

        elif self.config.get("default_vin") in self._cars:
            self._current_vin = self.config.get("default_vin")

        elif self.config.get("default_vin") not in self._cars:
            LOGGER.error("VIN %s does not exist in user account.", self.config.get("default_vin"))
            await self._quit(1)

        elif len(self._cars) > 1:
            LOGGER.error("Multiple vehicles in account but VIN not specified in config or command line (with --vin)")
            await self._quit(1)

        else:
            LOGGER.error("Something unexpected happened. Use -v2 for more debug information.")
            await self._quit(1)

        await self._fetch()
        self._current_has_ev = self._ctrl.get_ev_status(self._current_vin)
        self._current_has_res = self._ctrl.get_res_status(self._current_vin)
        self._current_has_remote = self._ctrl.get_remote_status(self._current_vin)
        self._current_api_gen = self._ctrl.get_api_gen(self._current_vin)

    async def _set_climate_params(self):
        user_presets = await self._ctrl.get_user_climate_preset_data(self._current_vin)
        if len(user_presets) > 3:
            print("There is a maximum of 4 user presets - please delete a preset with 'remote_start delete'")
            return

        if self.config["country"] == sc.COUNTRY_CAN:
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

        new_preset = {}
        new_preset[temp_field] = set_temp
        new_preset[sc.MODE] = _select_from_list("Select mode:", sc.VALID_CLIMATE_OPTIONS[sc.MODE])
        new_preset[sc.FAN_SPEED] = _select_from_list("Select fan speed:", sc.VALID_CLIMATE_OPTIONS[sc.FAN_SPEED])
        new_preset[sc.HEAT_SEAT_LEFT] = _select_from_list(
            "Driver seat heat:", sc.VALID_CLIMATE_OPTIONS[sc.HEAT_SEAT_LEFT]
        )
        new_preset[sc.HEAT_SEAT_RIGHT] = _select_from_list(
            "Passenger seat heat:", sc.VALID_CLIMATE_OPTIONS[sc.HEAT_SEAT_RIGHT]
        )
        new_preset[sc.REAR_DEFROST] = _select_from_list("Rear defroster:", sc.VALID_CLIMATE_OPTIONS[sc.REAR_DEFROST])
        new_preset[sc.RECIRCULATE] = _select_from_list("Recirculate:", sc.VALID_CLIMATE_OPTIONS[sc.RECIRCULATE])
        new_preset[sc.REAR_AC] = _select_from_list("Rear AC:", sc.VALID_CLIMATE_OPTIONS[sc.REAR_AC])
        new_preset[sc.RUNTIME] = _select_from_list("Runtime:", sc.VALID_CLIMATE_OPTIONS[sc.RUNTIME])
        new_preset["name"] = input("Enter name for this preset (30 chars max)> ")[:30]
        pprint(new_preset)
        save = _select_from_list(f"Save climate settings as '{new_preset['name']}'?", ["Yes", "No"])
        if save == "Yes":
            user_presets.append(new_preset)
            if await self._ctrl.update_user_climate_presets(self._current_vin, user_presets):
                print("Climate presets updated")

    async def _unlock(self, args):
        if len(args) == 0:
            print("\nunlock [all|drivers|tailgate]")
            print("  all      - unlock all doors")
            print("  drivers  - unlock drivers door only")
            print("  tailgate - unlock tailgate only\n")
        elif args[0] == "all":
            await self._ctrl.unlock(self._current_vin)
        elif args[0] == "drivers":
            await self._ctrl.unlock(self._current_vin, sc.DRIVERS_DOOR)
        elif args[0] == "tailgate":
            await self._ctrl.unlock(self._current_vin, sc.TAILGATE_DOOR)
        else:
            print("unlock: invalid arg: %s" % args[0])

    async def _remote_start(self, args):
        if len(args) == 0:
            print("\nremote_start [on|off|list|add|delete|default]")
            print("  on      - start engine")
            print("  off     - stop engine")
            print("  list    - list available presets")
            print("  add     - add a new climate preset")
            print("  delete  - delete a climate preset")
            print("  default - select default preset\n")

        elif args[0] == "on":
            presets_list = await self._ctrl.list_climate_preset_names(self._current_vin)
            preset = _select_from_list("Select preset: ", presets_list)
            await self._ctrl.remote_start(self._current_vin, preset)

        elif args[0] == "off":
            await self._ctrl.remote_stop(self._current_vin)

        elif args[0] == "list":
            print("Available remote start presets:")
            presets_list = await self._ctrl.list_climate_preset_names(self._current_vin)
            _print_list(presets_list)

        elif args[0] == "add":
            await self._set_climate_params()

        elif args[0] == "delete":
            user_presets = await self._ctrl.get_user_climate_preset_data(self._current_vin)
            user_presets = [i[sc.PRESET_NAME] for i in user_presets]
            if len(user_presets) > 0:
                preset = _select_from_list("Select preset to delete: ", user_presets)
                print(f"Deleting '{preset}'")
                if await self._ctrl.delete_climate_preset_by_name(self._current_vin, preset):
                    print(f"Successfully deleted '{preset}'")
            else:
                print("No user presets found")

        elif args[0] == "default":
            preset_list = await self._ctrl.list_climate_preset_names(self._current_vin)
            preset = _select_from_list("Select preset: ", preset_list)
            self.config[CONFIG_CLIMATE_PRESET] = preset
            self._save_config()
            print(f"Saved '{self.config[CONFIG_CLIMATE_PRESET]}' as remote start default")

        else:
            print("remote_start: invalid arg: %s" % args[0])

    def _summary_data(self):
        """Get printable vehicle summary data."""
        timediff = datetime.now(timezone.utc) - self._car_data["status"][sc.TIMESTAMP]
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
        # if self._current_has_remote and self._current_api_gen == FEATURE_G2_TELEMATICS:
        #     lines.append("12V Battery: %sV" % self._car_data["status"].get(sc.BATTERY_VOLTAGE))
        #     if sc.EXTERNAL_TEMP in self._car_data["status"]:
        #         lines.append("External Temp: %0.1f °F" % _c_to_f(self._car_data["status"][sc.EXTERNAL_TEMP]))
        #     else:
        #         lines.append("External Temp: Unknown")

        # EV Data
        if self._current_has_ev:
            lines.append("EV Charge: %s%%" % self._car_data["status"][sc.EV_STATE_OF_CHARGE_PERCENT])
            lines.append("EV Distance to Empty: %s miles" % self._car_data["status"][sc.EV_DISTANCE_TO_EMPTY])
            lines.append("EV Plug Status: %s" % self._car_data["status"][sc.EV_IS_PLUGGED_IN])
            lines.append("EV Charge Status: %s" % self._car_data["status"][sc.EV_CHARGER_STATE_TYPE])
            if self._car_data["status"][sc.EV_CHARGER_STATE_TYPE] == CHARGING:
                finish_time = self._car_data["status"][sc.EV_TIME_TO_FULLY_CHARGED_UTC]
                local_tz = datetime.now().astimezone().tzinfo
                time_left = finish_time - datetime.now(timezone.utc)
                finish_time = finish_time.astimezone(local_tz)
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
                await self._register_device()
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

    async def _register_device(self):
        attempts_left = 3
        if not self._ctrl.device_registered:
            method = _select_from_list(
                "This device is not recognized. Request new 2FA code to be sent to",
                list(self._ctrl.contact_methods.items()),
            )[0]
            await self._ctrl.request_auth_code(method)
            while attempts_left:
                code = input(f"Enter 2FA code received at {self._ctrl.contact_methods[method]}: ")
                if await self._ctrl.submit_auth_code(code):
                    return True
                attempts_left -= 1
                LOGGER.error("Verification failed, %d/3 attempts remaining.", attempts_left)
            raise SubaruException("Maximum 2FA attempts exceeded")
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
                    self.config["default_vin"] = self._current_vin
                    self._save_config()

                elif cmd == "lock":
                    await self._ctrl.lock(self._current_vin)

                elif cmd == "unlock":
                    await self._unlock(args)

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
            self.config["username"],
            self.config["password"],
            self.config["device_id"],
            self.config["pin"],
            self.config["device_name"],
            country=self.config["country"],
        )

    async def run(self):
        """Initialize connection and start CLI loop."""
        self._init_controller()
        try:
            if await self._connect():
                await self._cli_loop()
        except (KeyboardInterrupt, EOFError):
            await self._quit(0)

    async def single_command(self, cmd, vin, config):
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
                    preset = config.get(CONFIG_CLIMATE_PRESET)
                    if preset:
                        success = await self._ctrl.remote_start(self._current_vin, preset)
                    else:
                        raise SubaruException("Default climate preset must be selected via interactive mode first")

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
        _print_list(items)
        choice = input("> ")
        if choice.isnumeric():
            choice = int(choice) - 1
            if choice in range(len(items)):
                return items[choice]


def _print_list(items):
    for i, val in enumerate(items):
        print(" [%d] %s" % (i + 1, val))


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
        LOOP.run_until_complete(cli.single_command(args.command, args.vin, cli.config))
    if args.interactive:
        LOGGER.info("Entering interactive mode")
        cli = CLI(args.config_file)
        LOOP.run_until_complete(cli.run())
    else:
        parser.print_help()
