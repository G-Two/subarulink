from teslajsonpy.vehicle import VehicleDevice
import time


class Lock(VehicleDevice):
    def __init__(self, data, controller):
        VehicleDevice.__init__(self, data, controller)
        self.__id = data['id']
        self.__vehicle_id = data['vehicle_id']
        self.__vin = data['vin']
        self.__state = data['state']
        self.__controller = controller
        self.__manual_update_time = 0
        self.__lock_state = False

        self.type = 'door lock.'
        self.hass_type = 'lock'

        self.name = 'Tesla model {} {}'.format(
            str(self.__vin[3]).upper(), self.type)

        self.uniq_name = 'Tesla model {} {} {}'.format(
            str(self.__vin[3]).upper(), self.__vin, self.type)
        self.bin_type = 0x7
        self.update()

    def update(self):
        self.__controller.update(self.__id)
        data = self.__controller.get_state_params(self.__id)
        if time.time() - self.__manual_update_time > 60:
            self.__lock_state = data['locked']

    def lock(self):
        if not self.__lock_state:
            data = self.__controller.command(self.__id, 'door_lock')
            if data['response']['result']:
                self.__lock_state = True
            self.__manual_update_time = time.time()

    def unlock(self):
        if self.__lock_state:
            data = self.__controller.command(self.__id, 'door_unlock')
            if data['response']['result']:
                self.__lock_state = False
            self.__manual_update_time = time.time()

    def is_locked(self):
        return self.__lock_state

    @staticmethod
    def has_battery():
        return False
