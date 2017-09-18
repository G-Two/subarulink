from teslajsonpy.vehicle import VehicleDevice


class GPS(VehicleDevice):
    def __init__(self, data, controller):
        VehicleDevice.__init__(self, data, controller)
        self.__id = data['id']
        self.__vehicle_id = data['vehicle_id']
        self.__vin = data['vin']
        self.__controller = controller

        self.__longitude = 0
        self.__latitude = 0
        self.__heading = 0
        self.__location = {}

        self.last_seen = 0
        self.last_updated = 0
        self.type = 'location tracker.'
        self.hass_type = 'devices_tracker'
        self.bin_type = 0x6

        self.name = 'Tesla model {} {}'.format(
            str(self.__vin[3]).upper(), self.type)

        self.uniq_name = 'Tesla model {} {} {}'.format(
            str(self.__vin[3]).upper(), self.__vin, self.type)
        self.update()

    def get_location(self):
        return self.__location

    def update(self):
        self.__controller.update(self.__id)
        data = self.__controller.get_drive_params(self.__id)
        self.__longitude = data['longitude']
        self.__latitude = data['latitude']
        self.__heading = data['heading']
        if data['latitude'] and data['longitude'] and data['heading']:
            self.__location = {'longitude': self.__longitude,
                               'latitude': self.__latitude,
                               'heading': self.__heading}

    @staticmethod
    def has_battery():
        return False
