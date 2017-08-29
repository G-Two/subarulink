class VehicleDevice:
    def __init__(self, data, controller):
        self.__id = data['id']
        self.__vehicle_id = data['vehicle_id']
        self.__vin = data['vin']
        self.__state = data['state']
        self.__remote_start_enabled = data['remote_start_enabled']
        self.__in_service = data['in_service']
        self.__controller = controller
        self.should_poll = True

    def get_vin(self):
        return self.__vin

    def get_vehicle_id(self):
        return self.__vehicle_id

    def get_id(self):
        return self.__id

    def in_service(self):
        return self.__in_service

    @staticmethod
    def is_armable():
        return False

    @staticmethod
    def is_armed():
        return False