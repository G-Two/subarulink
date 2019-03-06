import time
from multiprocessing import RLock
from teslajsonpy.connection import Connection
from teslajsonpy.BatterySensor import Battery, Range
from teslajsonpy.Lock import Lock, ChargerLock
from teslajsonpy.Climate import Climate, TempSensor
from teslajsonpy.BinarySensor import ParkingSensor, ChargerConnectionSensor
from teslajsonpy.Charger import ChargerSwitch, RangeSwitch
from teslajsonpy.GPS import GPS, Odometer
from teslajsonpy.Exceptions import TeslaException
from functools import wraps
import logging
from .Exceptions import RetryLimitError
_LOGGER = logging.getLogger(__name__)


class Controller:
    def __init__(self, email, password, update_interval):
        self.__connection = Connection(email, password)
        self.__vehicles = []
        self.update_interval = update_interval
        self.__update = {}
        self.__climate = {}
        self.__charging = {}
        self.__state = {}
        self.__driving = {}
        self.__gui = {}
        self._last_update_time = {}  # succesful attempts by car
        self._last_wake_up_time = {}  # succesful wake_ups by car
        self._last_attempted_update_time = 0  # all attempts by controller
        self.__lock = RLock()
        self._car_online = {}

        cars = self.get_vehicles()
        self._last_attempted_update_time = time.time()

        for car in cars:
            self._last_update_time[car['id']] = 0
            self._last_wake_up_time[car['id']] = 0
            self.__update[car['id']] = True
            self._car_online[car['id']] = (car['state'] == 'online')
            self.__climate[car['id']] = False
            self.__charging[car['id']] = False
            self.__state[car['id']] = False
            self.__driving[car['id']] = False
            self.__gui[car['id']] = False

            try:
                self.update(car['id'], wake_if_asleep=False)
            except (TeslaException, RetryLimitError):
                pass
            self.__vehicles.append(Climate(car, self))
            self.__vehicles.append(Battery(car, self))
            self.__vehicles.append(Range(car, self))
            self.__vehicles.append(TempSensor(car, self))
            self.__vehicles.append(Lock(car, self))
            self.__vehicles.append(ChargerLock(car, self))
            self.__vehicles.append(ChargerConnectionSensor(car, self))
            self.__vehicles.append(ChargerSwitch(car, self))
            self.__vehicles.append(RangeSwitch(car, self))
            self.__vehicles.append(ParkingSensor(car, self))
            self.__vehicles.append(GPS(car, self))
            self.__vehicles.append(Odometer(car, self))

    def wake_up(f):
        """Wraps a API f so it will attempt to wake the vehicle if asleep.

        The command f is run once if the vehicle_id was last reported
        online. Assuming f returns None and wake_if_asleep is True, 5 attempts
        will be made to wake the vehicle to reissue the command. In addition,
        if there is a `could_not_wake_buses` error, it will retry the command
        Args:
        inst (Controller): The instance of a controller
        vehicle_id (string): The vehicle to attempt to wake.
        TODO: This currently requires a vehicle_id, but update() does not; This
              should also be updated to allow that case
        wake_if_asleep (bool): Keyword arg to force a vehicle awake. Must be
                               set in the wrapped function f
        Throws:
        RetryLimitError
        """
        @wraps(f)
        def wrapped(*args, **kwargs):
            def valid_result(result):
                """Is TeslaAPI result succesful.

                Parameters
                ----------
                result : tesla API result
                    This is the result of a Tesla Rest API call.

                Returns
                -------
                bool
                  Tesla API failure can be checked in a dict with a bool in
                  ['response']['result'], a bool, or None or
                  ['response']['reason'] == 'could_not_wake_buses'
                  Returns true when a failure state not detected.
                """
                try:
                    return (result is not None and result is not False and
                            (result is True or
                             (isinstance(result, dict) and
                              isinstance(result['response'], dict) and
                              ('result' in result['response'] and
                               result['response']['result'] is True) or
                              ('reason' in result['response'] and
                               result['response']['reason'] !=
                               'could_not_wake_buses') or
                              ('result' not in result['response']))))
                except TypeError as exception:
                    _LOGGER.error("Result: %s, %s", result, exception)
            retries = 0
            sleep_delay = 2
            inst = args[0]
            vehicle_id = args[1]
            result = None
            if (vehicle_id is not None and vehicle_id in inst._car_online and
                    inst._car_online[vehicle_id]):
                try:
                    result = f(*args, **kwargs)
                except TeslaException:
                    pass
            if valid_result(result):
                return result
            _LOGGER.debug("Wrapped %s -> %s \n"
                          "Additional info: args:%s, kwargs:%s, "
                          "vehicle_id:%s, _car_online:%s",
                          f.__name__, result, args, kwargs, vehicle_id,
                          inst._car_online)
            inst._car_online[vehicle_id] = False
            while ('wake_if_asleep' in kwargs and kwargs['wake_if_asleep']
                   and
                   # Check online state
                   (vehicle_id is None or
                    (vehicle_id is not None and
                     vehicle_id in inst._car_online and
                     not inst._car_online[vehicle_id]))):
                result = inst._wake_up(vehicle_id, *args, **kwargs)
                _LOGGER.debug("Wake Attempt(%s): %s", retries, result)
                if not result:
                    if retries < 5:
                        time.sleep(sleep_delay**(retries+2))
                        retries += 1
                        continue
                    else:
                        inst._car_online[vehicle_id] = False
                        raise RetryLimitError
                else:
                    break
            # try function five more times
            retries = 0
            while True:
                try:
                    result = f(*args, **kwargs)
                    _LOGGER.debug("Retry Attempt(%s): %s", retries, result)
                except TeslaException:
                    pass
                finally:
                    retries += 1
                time.sleep(sleep_delay**(retries+1))
                if valid_result(result):
                    return result
                elif retries >= 5:
                    raise RetryLimitError
        return wrapped

    def get_vehicles(self):
        return self.__connection.get('vehicles')['response']

    @wake_up
    def post(self, vehicle_id, command, data={}, wake_if_asleep=True):
        return self.__connection.post('vehicles/%i/%s' %
                                      (vehicle_id, command), data)

    @wake_up
    def get(self, vehicle_id, command, wake_if_asleep=False):
        return self.__connection.get('vehicles/%i/%s' % (vehicle_id, command))

    def data_request(self, vehicle_id, name, wake_if_asleep=False):
        return self.get(vehicle_id, 'data_request/%s' % name,
                        wake_if_asleep=False)['response']

    def command(self, vehicle_id, name, data={}, wake_if_asleep=True):
        return self.post(vehicle_id, 'command/%s' % name, data,
                         wake_if_asleep=True)

    def list_vehicles(self):
        return self.__vehicles

    def _wake_up(self, vehicle_id, *args, **kwargs):
        cur_time = int(time.time())
        if (not self._car_online[vehicle_id] or
                (cur_time - self._last_wake_up_time[vehicle_id] > 300)):
            result = self.post(vehicle_id,
                               'wake_up',
                               wake_if_asleep=False)  # avoid wrapper loop
            self._car_online[vehicle_id] = (result['response']['state'] ==
                                            'online')
            self._last_wake_up_time[vehicle_id] = cur_time
            _LOGGER.debug("Wakeup %s: %s", vehicle_id,
                          result['response']['state'])
        return self._car_online[vehicle_id]

    def update(self, car_id=None, wake_if_asleep=False, force=False):
        """Updates all vehicle attributes in the cache.

        This command will connect to the Tesla API and first update the list of
        online vehicles assuming no attempt for at least the [update_interval].
        It will then update all the cached values for cars that are awake
        assuming no update has occurred for at least the [update_interval].

        Args:
        inst (Controller): The instance of a controller
        car_id (string): The vehicle to update. If None, all cars are updated.
        wake_if_asleep (bool): Keyword arg to force a vehicle awake. This is
                               processed by the wake_up decorator.
        force (bool): Keyword arg to force a vehicle update regardless of the
                      update_interval

        Returns:
        True if any update succeeded for any vehicle else false
        Throws:
        RetryLimitError
        """
        cur_time = time.time()
        with self.__lock:
            #  Update the online cars using get_vehicles()
            last_update = self._last_attempted_update_time
            if (force or cur_time - last_update > self.update_interval):
                cars = self.get_vehicles()
                for car in cars:
                    self._car_online[car['id']] = (car['state'] == 'online')
                self._last_attempted_update_time = cur_time
            # Only update online vehicles that haven't been updated recently
            # The throttling is per car's last succesful update
            # Note: This separate check is because there may be individual cars
            # to update.
            update_succeeded = False
            for id, v in self._car_online.items():
                # If specific car_id provided, only update match
                if (car_id is not None and car_id != id):
                    continue
                if (v and
                    (id in self.__update and self.__update[id]) and
                    (force or id not in self._last_update_time or
                        ((cur_time - self._last_update_time[id]) >
                            self.update_interval))):
                    # Only update cars with update flag on
                    try:
                        data = self.get(id, 'data', wake_if_asleep)
                    except TeslaException:
                        data = None
                    if data and data['response']:
                        response = data['response']
                        self.__climate[car_id] = response['climate_state']
                        self.__charging[car_id] = response['charge_state']
                        self.__state[car_id] = response['vehicle_state']
                        self.__driving[car_id] = response['drive_state']
                        self.__gui[car_id] = response['gui_settings']
                        self._car_online[car_id] = (response['state']
                                                    == 'online')
                        self._last_update_time[car_id] = time.time()
                        update_succeeded = True
            return update_succeeded

    def get_climate_params(self, car_id):
        return self.__climate[car_id]

    def get_charging_params(self, car_id):
        return self.__charging[car_id]

    def get_state_params(self, car_id):
        return self.__state[car_id]

    def get_drive_params(self, car_id):
        return self.__driving[car_id]

    def get_gui_params(self, car_id):
        return self.__gui[car_id]

    def get_updates(self, car_id=None):
        if car_id is not None:
            return self.__update[car_id]
        else:
            return self.__update

    def set_updates(self, car_id, value):
        self.__update[car_id] = value
