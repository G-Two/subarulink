from teslajsonpy.vehicle import Vehicle


class GPS(Vehicle):
    def __init__(self, data, controller):
        Vehicle.__init__(self, data, controller)
        self.__id = data['id']
        self.__vehicle_id = data['vehicle_id']
        self.__vin = data['vin']
        self.controller = controller
        self.type = 'device tracker'
        self.__logger = self.controller.get_logger()
        self.__longitude = 0
        self.__latitude = 0
        self.__heading = 0
        self.__location = {}
        self.last_seen = 0
        self.last_updated = 0
        self.update()

    def get_location(self):
        return self.__location

    def update(self):
        self.__logger.debug("Updating positioning params started. Vehicle ID: %s Sensor type is: %s"
                            % (self.__id, self.type))
        self.controller.update(self.__id)
        data = self.controller.get_drive_params(self.__id)
        self.__logger.debug(data)
        self.__longitude = data['longitude']
        self.__latitude = data['latitude']
        self.__heading = data['heading']
        if data['latitude'] and data['longitude'] and data['heading']:
            self.__location = {'longitude': self.__longitude,
                               'latitude': self.__latitude,
                               'heading': self.__heading}
        self.last_updated
        self.__logger.debug("Updating positioning params finished. Vehicle ID: %s Sensor type is: %s"
                            % (self.__id, self.type))

    @staticmethod
    def has_battery():
        return False
