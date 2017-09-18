import time

from teslajsonpy.connection import Connection
from teslajsonpy.BatterySensor import Battery
from teslajsonpy.Lock import Lock
from teslajsonpy.Climate import Climate, TempSensor
from teslajsonpy.BinarySensor import ParkingSensor, ChargerConnectionSensor
from teslajsonpy.Charger import ChargerSwitch
from teslajsonpy.GPS import GPS
from json import dumps


class Controller:
    def __init__(self, email, password, update_interval, logger):
        self.__connection = Connection(email, password, logger)
        self.__vehicles = []
        self.update_interval = update_interval
        self.__climate = {}
        self.__charging = {}
        self.__state = {}
        self.__driving = {}
        self.__last_update_time = {}
        self.__logger = logger
        cars = self.__connection.get('vehicles')['response']
        for car in cars:
            self.__last_update_time[car['id']] = 0
            self.update(car['id'])
            self.__vehicles.append(Climate(car, self))
            self.__vehicles.append(Battery(car, self))
            self.__vehicles.append(TempSensor(car, self))
            self.__vehicles.append(Lock(car, self))
            self.__vehicles.append(ChargerConnectionSensor(car, self))
            self.__vehicles.append(ChargerSwitch(car, self))
            self.__vehicles.append(ParkingSensor(car, self))
            self.__vehicles.append(GPS(car, self))

    def post(self, vehicle_id, command, data={}):
        self.__logger.debug('vehicles/%i/%s' % (vehicle_id, command))
        return self.__connection.post('vehicles/%i/%s' % (vehicle_id, command), data)

    def get(self, vehicle_id, command):
        self.__logger.debug('vehicles/%i/%s' % (vehicle_id, command))
        return self.__connection.get('vehicles/%i/%s' % (vehicle_id, command))

    def data_request(self, vehicle_id, name):
        return self.get(vehicle_id, 'data_request/%s' % name)['response']

    def command(self, vehicle_id, name, data={}):
        return self.post(vehicle_id, 'command/%s' % name, data)

    def list_vehicles(self):
        return self.__vehicles

    def wake_up(self, vehicle_id):
        self.__logger.debug('{} {}'.format(vehicle_id, 'wake_up'))
        self.post(vehicle_id, 'wake_up')

    def update(self, car_id):
        cur_time = time.time()
        if cur_time - self.__last_update_time[car_id] > self.update_interval:
            self.wake_up(car_id)
            data = self.get(car_id, 'data')['response']
            self.__climate[car_id] = data['climate_state']
            self.__charging[car_id] = data['charge_state']
            self.__state[car_id] = data['vehicle_state']
            self.__driving[car_id] = data['drive_state']
            self.__last_update_time[car_id] = time.time()
            self.__logger.debug(
                'Update requested:\n\t'
                'Cat_ID: {}\n\t'
                'TS: \n\t\t'
                'Last Update:{}\n\t\t'
                'Current: {} \n\t\t'
                'Delta: {}\n\t'
                'Data: {}'.format(
                    car_id, self.__last_update_time[car_id], cur_time, cur_time - self.__last_update_time[car_id],
                    dumps(data)))

    def get_climate_params(self, car_id):
        return self.__climate[car_id]

    def get_charging_params(self, car_id):
        return self.__charging[car_id]

    def get_state_params(self, car_id):
        return self.__state[car_id]

    def get_drive_params(self, car_id):
        return self.__driving[car_id]
