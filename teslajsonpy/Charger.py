from teslajsonpy.vehicle import VehicleDevice
import time


class ChargerSwitch(VehicleDevice):
    def __init__(self, data, controller):
        VehicleDevice.__init__(self, data, controller)
        self.__id = data['id']
        self.__vehicle_id = data['vehicle_id']
        self.__vin = data['vin']
        self.__state = data['state']
        self.__controller = controller
        self.__manual_update_time = 0
        self.__charger_state = False
        self.type = 'charger switch.'
        self.hass_type = 'switch'
        self.name = 'Tesla model {} {}'.format(
            str(self.__vin[3]).upper(), self.type)
        self.uniq_name = 'Tesla model {} {} {}'.format(
            str(self.__vin[3]).upper(), self.__vin, self.type)
        self.bin_type = 0x8
        self.update()

    def update(self):
        self.__controller.update(self.__id)
        data = self.__controller.get_charging_params(self.__id)
        if time.time() - self.__manual_update_time > 60:
            if data['charging_state'] != "Charging":
                self.__charger_state = False
            else:
                self.__charger_state = True

    def start_charge(self):
        if not self.__charger_state:
            data = self.__controller.command(self.__id, 'charge_start')
            if data['response']['result']:
                self.__charger_state = True
            self.__manual_update_time = time.time()

    def stop_charge(self):
        if self.__charger_state:
            data = self.__controller.command(self.__id, 'charge_stop')
            if data['response']['result']:
                self.__charger_state = False
            self.__manual_update_time = time.time()

    def is_charging(self):
        return self.__charger_state

    @staticmethod
    def has_battery():
        return False
