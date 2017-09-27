class VehicleDevice:
    def __init__(self, data, controller):
        self._id = data['id']
        self._vehicle_id = data['vehicle_id']
        self._vin = data['vin']
        self._state = data['state']
        self._controller = controller
        self.should_poll = True

    def _name(self):
        return 'Tesla Model {} {}'.format(
            str(self._vin[3]).upper(), self.type)

    def _uniq_name(self):
        return 'Tesla Model {} {} {}'.format(
            str(self._vin[3]).upper(), self._vin, self.type)

    @staticmethod
    def is_armable():
        return False

    @staticmethod
    def is_armed():
        return False