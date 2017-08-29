from teslajsonpy.vehicle import Vehicle
import time


class Lock(Vehicle):
    def __init__(self, data, controller):
        Vehicle.__init__(self, data, controller)
        self.__id = data['id']
        self.__vehicle_id = data['vehicle_id']
        self.__vin = data['vin']
        self.__state = data['state']
        self.controller = controller
        self.__logger = self.controller.get_logger()

        self.__manual_update_time = 0
        self.__lock_state = False
        self.type = 'lock'
        self.update()

    def update(self):
        self.__logger.debug('Updating lock state started. Vehicle ID: %s' % self.__id)
        self.controller.update(self.__id)
        data = self.controller.get_state_params(self.__id)
        if time.time() - self.__manual_update_time > 60:
            self.__lock_state = data['locked']
        self.__logger.debug(data)
        self.__logger.debug('Updating lock state finished. Vehicle ID: %s' % self.__id)

    def lock(self):
        if not self.__lock_state:
            data = self.controller.command(self.__id, 'door_lock')
            print(data)

            if data['response']['result']:
                self.__lock_state = True
            self.__manual_update_time = time.time()

    def unlock(self):
        if self.__lock_state:
            data = self.controller.command(self.__id, 'door_unlock')
            print(data)
            if data['response']['result']:
                self.__lock_state = False
            self.__manual_update_time = time.time()

    def is_locked(self):
        return self.__lock_state

    @staticmethod
    def has_battery():
        return False
