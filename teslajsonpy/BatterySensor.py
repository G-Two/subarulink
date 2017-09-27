from teslajsonpy.vehicle import VehicleDevice


class Battery(VehicleDevice):
    def __init__(self, data, controller):
        super().__init__(data, controller)
        self.__battery_level = 0
        self.__charging_state = None
        self.__charge_port_door_open = None
        self.type = 'battery sensor'
        self.measurement = '%'
        self.hass_type = 'sensor'
        self.name = self._name()
        self.uniq_name = self._uniq_name()
        self.bin_type = 0x5
        self.update()

    def update(self):
        self._controller.update(self._id)
        data = self._controller.get_charging_params(self._id)
        self.__battery_level = data['battery_level']
        self.__charging_state = data['charging_state']

    @staticmethod
    def has_battery():
        return False

    def battery_level(self):
        return self.__battery_level
