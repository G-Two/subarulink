from teslajsonpy.vehicle import Vehicle


class ParkingSensor(Vehicle):
    def __init__(self, data, controller):
        Vehicle.__init__(self, data, controller)
        self.__id = data['id']
        self.__vehicle_id = data['vehicle_id']
        self.__vin = data['vin']
        self.controller = controller
        self.__logger = self.controller.get_logger()
        self.__state = False
        self.type = 'parking sensor'
        self.update()

    def update(self):
        self.controller.update(self.__id)
        data = self.controller.get_drive_params(self.__id)
        if not data['shift_state'] or data['shift_state'] == 'P':
            self.__state = True
        else:
            self.__state = False

    def get_value(self):
        return self.__state

    @staticmethod
    def has_battery():
        return False


class ChargerConnectionSensor(Vehicle):
    def __init__(self, data, controller):
        Vehicle.__init__(self, data, controller)
        self.__id = data['id']
        self.__vehicle_id = data['vehicle_id']
        self.__vin = data['vin']
        self.controller = controller
        self.__logger = self.controller.get_logger()
        self.__state = False
        self.type = 'charger sensor'
        self.update()

    def update(self):
        self.controller.update(self.__id)
        data = self.controller.get_charging_params(self.__id)
        if data['charging_state'] in ["Disconnected", "Stopped", "NoPower"]:
            self.__state = False
        else:
            self.__state = True

    def get_value(self):
        return self.__state

    @staticmethod
    def has_battery():
        return False