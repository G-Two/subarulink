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
        self._controller.update(self._id, wake_if_asleep=False)
        data = self._controller.get_drive_params(self._id)
        if data:
            self.__longitude = data['longitude']
            self.__latitude = data['latitude']
            self.__heading = data['heading']
        if self.__longitude and self.__latitude and self.__heading:
            self.__location = {'longitude': self.__longitude,
                               'latitude': self.__latitude,
                               'heading': self.__heading}

    @staticmethod
    def has_battery():
        return False


class Odometer(VehicleDevice):
    def __init__(self, data, controller):
        super().__init__(data, controller)
        self.__odometer = 0
        self.type = 'mileage sensor'
        self.measurement = 'LENGTH_MILES'
        self.hass_type = 'sensor'
        self.name = self._name()
        self.uniq_name = self._uniq_name()
        self.bin_type = 0xB
        self.update()
        self.__rated = True

    def update(self):
        self._controller.update(self._id, wake_if_asleep=False)
        data = self._controller.get_state_params(self._id)
        if data:
            self.__odometer = data['odometer']
        data = self._controller.get_gui_params(self._id)
        if data:
            if data['gui_distance_units'] == "mi/hr":
                self.measurement = 'LENGTH_MILES'
            else:
                self.measurement = 'LENGTH_KILOMETERS'
            self.__rated = (data['gui_range_display'] == "Rated")

    @staticmethod
    def has_battery():
        return False

    def get_value(self):
        return round(self.__odometer, 1)
