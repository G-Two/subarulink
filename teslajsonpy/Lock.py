from teslajsonpy.vehicle import VehicleDevice
import time


class Lock(VehicleDevice):
    def __init__(self, data, controller):
        super().__init__(data, controller)
        self.__manual_update_time = 0
        self.__lock_state = False

        self.type = 'door lock'
        self.hass_type = 'lock'

        self.name = self._name()

        self.uniq_name = self._uniq_name()
        self.bin_type = 0x7
        self.update()

    def update(self):
        self._controller.update(self._id, wake_if_asleep=False)
        data = self._controller.get_state_params(self._id)
        if data and (time.time() - self.__manual_update_time > 60):
            self.__lock_state = data['locked']

    def lock(self):
        if not self.__lock_state:
            data = self._controller.command(self._id, 'door_lock',
                                            wake_if_asleep=True)
            if data['response']['result']:
                self.__lock_state = True
            self.__manual_update_time = time.time()

    def unlock(self):
        if self.__lock_state:
            data = self._controller.command(self._id, 'door_unlock',
                                            wake_if_asleep=True)
            if data['response']['result']:
                self.__lock_state = False
            self.__manual_update_time = time.time()

    def is_locked(self):
        return self.__lock_state

    @staticmethod
    def has_battery():
        return False


class ChargerLock(VehicleDevice):
    def __init__(self, data, controller):
        super().__init__(data, controller)
        self.__manual_update_time = 0
        self.__lock_state = False

        self.type = 'charger door lock'
        self.hass_type = 'lock'

        self.name = self._name()

        self.uniq_name = self._uniq_name()
        self.bin_type = 0x7
        self.update()

    def update(self):
        self._controller.update(self._id, wake_if_asleep=False)
        data = self._controller.get_charging_params(self._id)
        if data and (time.time() - self.__manual_update_time > 60):
            self.__lock_state = not ((data['charge_port_door_open']) and (data['charge_port_door_open']) and (data['charge_port_latch'] != 'Engaged'))

    def lock(self):
        if not self.__lock_state:
            data = self._controller.command(self._id, 'charge_port_door_close',
                                            wake_if_asleep=True)
            if data['response']['result']:
                self.__lock_state = True
            self.__manual_update_time = time.time()

    def unlock(self):
        if self.__lock_state:
            data = self._controller.command(self._id, 'charge_port_door_open',
                                            wake_if_asleep=True)
            if data['response']['result']:
                self.__lock_state = False
            self.__manual_update_time = time.time()

    def is_locked(self):
        return self.__lock_state

    @staticmethod
    def has_battery():
        return False
