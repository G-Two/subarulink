from teslajsonpy.vehicle import VehicleDevice


class ParkingSensor(VehicleDevice):
    def __init__(self, data, controller):
        super().__init__(data, controller)
        self.__state = False

        self.type = 'parking brake sensor'
        self.hass_type = 'binary_sensor'

        self.name = self._name()

        self.uniq_name = self._uniq_name()
        self.bin_type = 0x1
        self.update()

    def update(self):
        self._controller.update(self._id)
        data = self._controller.get_drive_params(self._id)
        if data:
            if not data['shift_state'] or data['shift_state'] == 'P':
                self.__state = True
            else:
                self.__state = False

    def get_value(self):
        return self.__state

    @staticmethod
    def has_battery():
        return False


class ChargerConnectionSensor(VehicleDevice):
    def __init__(self, data, controller):
        super().__init__(data, controller)
        self.__state = False

        self.type = 'charger sensor'
        self.hass_type = 'binary_sensor'
        self.name = self._name()

        self.uniq_name = self._uniq_name()
        self.bin_type = 0x2

    def update(self):
        self._controller.update(self._id)
        data = self._controller.get_charging_params(self._id)
        if data:
            if data['charging_state'] in ["Disconnected", "Stopped", "NoPower"]:
                self.__state = False
            else:
                self.__state = True

    def get_value(self):
        return self.__state

    @staticmethod
    def has_battery():
        return False
