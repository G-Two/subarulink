from teslajsonpy.vehicle import VehicleDevice


class Battery(VehicleDevice):
    def __init__(self, data, controller):
        VehicleDevice.__init__(self, data, controller)
        self.__id = data['id']
        self.__vin = data['vin']
        self.__vehicle_id = data['vehicle_id']
        self.__controller = controller
        self.__battery_level = 0
        self.__charging_state = None
        self.__charge_port_door_open = None

        self.type = 'battery sensor.'
        self.measurement = '%'
        self.hass_type = 'sensor'

        self.name = 'Tesla model {} {}'.format(
            str(self.__vin[3]).upper(), self.type)

        self.uniq_name = 'Tesla model {} {} {}'.format(
            str(self.__vin[3]).upper(), self.__vin, self.type)
        self.bin_type = 0x5
        self.update()

    def update(self):
        self.__controller.update(self.__id)
        data = self.__controller.get_charging_params(self.__id)
        self.__battery_level = data['battery_level']
        self.__charging_state = data['charging_state']

    @staticmethod
    def has_battery():
        return False

    def battery_level(self):
        return self.__battery_level
