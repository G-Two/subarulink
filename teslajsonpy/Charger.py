from teslajsonpy.vehicle import VehicleDevice
import time


class ChargerSwitch(VehicleDevice):
    def __init__(self, data, controller):
        super().__init__(data, controller)
        self.__manual_update_time = 0
        self.__charger_state = False
        self.type = 'charger switch'
        self.hass_type = 'switch'
        self.name = self._name()
        self.uniq_name = self._uniq_name()
        self.bin_type = 0x8
        self.update()

    def update(self):
        self._controller.update(self._id, wake_if_asleep=False)
        data = self._controller.get_charging_params(self._id)
        if data and (time.time() - self.__manual_update_time > 60):
            if data['charging_state'] != "Charging":
                self.__charger_state = False
            else:
                self.__charger_state = True

    def start_charge(self):
        if not self.__charger_state:
            data = self._controller.command(self._id, 'charge_start',
                                            wake_if_asleep=True)
            if data and data['response']['result']:
                self.__charger_state = True
            self.__manual_update_time = time.time()

    def stop_charge(self):
        if self.__charger_state:
            data = self._controller.command(self._id, 'charge_stop',
                                            wake_if_asleep=True)
            if data and data['response']['result']:
                self.__charger_state = False
            self.__manual_update_time = time.time()

    def is_charging(self):
        return self.__charger_state

    @staticmethod
    def has_battery():
        return False


class RangeSwitch(VehicleDevice):
    def __init__(self, data, controller):
        super().__init__(data, controller)
        self.__manual_update_time = 0
        self.__maxrange_state = False
        self.type = 'maxrange switch'
        self.hass_type = 'switch'
        self.name = self._name()
        self.uniq_name = self._uniq_name()
        self.bin_type = 0x9
        self.update()

    def update(self):
        self._controller.update(self._id, wake_if_asleep=False)
        data = self._controller.get_charging_params(self._id)
        if data and (time.time() - self.__manual_update_time > 60):
            self.__maxrange_state = data['charge_to_max_range']

    def set_max(self):
        if not self.__maxrange_state:
            data = self._controller.command(self._id, 'charge_max_range',
                                            wake_if_asleep=True)
            if data['response']['result']:
                self.__maxrange_state = True
            self.__manual_update_time = time.time()

    def set_standard(self):
        if self.__maxrange_state:
            data = self._controller.command(self._id, 'charge_standard',
                                            wake_if_asleep=True)
            if data and data['response']['result']:
                self.__maxrange_state = False
            self.__manual_update_time = time.time()

    def is_maxrange(self):
        return self.__maxrange_state

    @staticmethod
    def has_battery():
        return False
