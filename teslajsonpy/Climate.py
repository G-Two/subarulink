from teslajsonpy.vehicle import VehicleDevice
import time


class Climate(VehicleDevice):
    def __init__(self, data, controller):
        VehicleDevice.__init__(self, data, controller)
        self.__id = data['id']
        self.__vehicle_id = data['vehicle_id']
        self.__vin = data['vin']
        self.__state = data['state']
        self.__remote_start_enabled = data['remote_start_enabled']
        self.__in_service = data['in_service']
        self.__controller = controller
        self.__is_auto_conditioning_on = False
        self.__inside_temp = 0
        self.__outside_temp = 0
        self.__driver_temp_setting = 0
        self.__passenger_temp_setting = 0
        self.__is_climate_on = False
        self.__fan_status = 0
        self.__manual_update_time = 0

        self.type = 'HVAC (climate) system.'
        self.hass_type = 'climate'
        self.measurement = 'C'

        self.name = 'Tesla model {} {}'.format(
            str(self.__vin[3]).upper(), self.type)

        self.uniq_name = 'Tesla model {} {} {}'.format(
            str(self.__vin[3]).upper(), self.__vin, self.type)
        self.bin_type = 0x3

        self.update()

    def is_hvac_enabled(self):
        return self.__is_climate_on

    def get_current_temp(self):
        return self.__inside_temp

    def get_goal_temp(self):
        return self.__driver_temp_setting

    def get_fan_status(self):
        return self.__fan_status

    def update(self):
        self.__controller.update(self.__id)

        data = self.__controller.get_climate_params(self.__id)
        if time.time() - self.__manual_update_time > 60:
            self.__is_auto_conditioning_on = data['is_auto_conditioning_on']
            self.__is_climate_on = data['is_climate_on']
            self.__driver_temp_setting = data['driver_temp_setting'] \
                if data['driver_temp_setting'] else self.__driver_temp_setting
            self.__passenger_temp_setting = data['passenger_temp_setting'] \
                if data['passenger_temp_setting'] else self.__passenger_temp_setting
        self.__inside_temp = data['inside_temp'] if data['inside_temp'] else self.__inside_temp
        self.__outside_temp = data['outside_temp'] if data['outside_temp'] else self.__outside_temp
        self.__fan_status = data['fan_status']

    def set_temperature(self, temp):
        temp = round(temp, 1)
        self.__manual_update_time = time.time()
        data = self.__controller.command(self.__id, 'set_temps', {"driver_temp": temp, "passenger_temp": temp})
        if data['response']['result']:
            self.__driver_temp_setting = temp
            self.__passenger_temp_setting = temp

    def set_status(self, enabled):
        self.__manual_update_time = time.time()
        if enabled:
            data = self.__controller.command(self.__id, 'auto_conditioning_start')
            if data['response']['result']:
                self.__is_auto_conditioning_on = True
                self.__is_climate_on = True
        else:
            data = self.__controller.command(self.__id, 'auto_conditioning_stop')
            if data['response']['result']:
                self.__is_auto_conditioning_on = False
                self.__is_climate_on = False
        self.update()

    @staticmethod
    def has_battery():
        return False


class TempSensor(VehicleDevice):
    def __init__(self, data, controller):
        VehicleDevice.__init__(self, data, controller)
        self.__id = data['id']
        self.__vehicle_id = data['vehicle_id']
        self.__vin = data['vin']
        self.__controller = controller
        self.__inside_temp = 0
        self.__outside_temp = 0

        self.type = 'temperature sensor.'
        self.measurement = 'C'
        self.hass_type = 'sensor'

        self.name = 'Tesla model {} {}'.format(
            str(self.__vin[3]).upper(), self.type)

        self.uniq_name = 'Tesla model {} {} {}'.format(
            str(self.__vin[3]).upper(), self.__vin, self.type)
        self.bin_type = 0x4
        self.update()

    def get_inside_temp(self):
        return self.__inside_temp

    def get_outside_temp(self):
        return self.__outside_temp

    def update(self):
        self.__controller.update(self.__id)
        data = self.__controller.get_climate_params(self.__id)
        self.__inside_temp = data['inside_temp'] if data['inside_temp'] else self.__inside_temp
        self.__outside_temp = data['outside_temp'] if data['outside_temp'] else self.__outside_temp

    @staticmethod
    def has_battery():
        return False
