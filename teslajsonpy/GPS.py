from teslajsonpy.vehicle import VehicleDevice


class GPS(VehicleDevice):
    def __init__(self, data, controller):
        super().__init__(data, controller)
        self.__longitude = 0
        self.__latitude = 0
        self.__heading = 0
        self.__location = {}

        self.last_seen = 0
        self.last_updated = 0
        self.type = 'location tracker'
        self.hass_type = 'devices_tracker'
        self.bin_type = 0x6

        self.name = self._name()

        self.uniq_name = self._uniq_name()
        self.update()

    def get_location(self):
        return self.__location

    def update(self):
        self._controller.update(self._id)
        data = self._controller.get_drive_params(self._id)
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
