import time
from multiprocessing import RLock
from teslajsonpy.connection import Connection
from teslajsonpy.BatterySensor import Battery, Range
from teslajsonpy.Lock import Lock, ChargerLock
from teslajsonpy.Climate import Climate, TempSensor
from teslajsonpy.BinarySensor import ParkingSensor, ChargerConnectionSensor
from teslajsonpy.Charger import ChargerSwitch, RangeSwitch
from teslajsonpy.GPS import GPS, Odometer


class Controller:
    def __init__(self, email, password, update_interval, wake=True):
        self.__connection = Connection(email, password)
        self.__vehicles = []
        self.__should_wake = wake
        self.update_interval = update_interval
        self.__update = {}
        self.__climate = {}
        self.__charging = {}
        self.__state = {}
        self.__driving = {}
        self.__gui = {}
        self.__last_update_time = {}
        self.__lock = RLock()
        cars = self.__connection.get('vehicles')['response']
        for car in cars:
            car_id = car['id']
            self.__climate[car_id] = False
            self.__charging[car_id] = False
            self.__state[car_id] = False
            self.__driving[car_id] = False
            self.__gui[car_id] = False
            self.__last_update_time[car_id] = 0
            self.__update[car_id] = True
            self.update(car_id)
            self.__vehicles.append(Climate(car, self))
            self.__vehicles.append(Battery(car, self))
            self.__vehicles.append(Range(car, self))
            self.__vehicles.append(TempSensor(car, self))
            self.__vehicles.append(Lock(car, self))
            self.__vehicles.append(ChargerLock(car, self))
            self.__vehicles.append(ChargerConnectionSensor(car, self))
            self.__vehicles.append(ChargerSwitch(car, self))
            self.__vehicles.append(RangeSwitch(car, self))
            self.__vehicles.append(ParkingSensor(car, self))
            self.__vehicles.append(GPS(car, self))
            self.__vehicles.append(Odometer(car, self))

    def post(self, vehicle_id, command, data={}):
        return self.__connection.post('vehicles/%i/%s' % (vehicle_id, command), data)

    def get(self, vehicle_id, command):
        return self.__connection.get('vehicles/%i/%s' % (vehicle_id, command))

    def data_request(self, vehicle_id, name):
        return self.get(vehicle_id, 'data_request/%s' % name)['response']

    def command(self, vehicle_id, name, data={}):
        return self.post(vehicle_id, 'command/%s' % name, data)

    def list_vehicles(self):
        return self.__vehicles

    def wake_up(self, vehicle_id):
        self.post(vehicle_id, 'wake_up')

    def update(self, car_id):
        cur_time = time.time()
        with self.__lock:
            if (self.__update[car_id] and
             (cur_time - self.__last_update_time[car_id] > self.update_interval)):
                if self.__should_wake is False:
                    cars = self.__connection.get('vehicles')['response']
                    for car in cars:
                        if car['id'] == car_id and car['state'] != "online":
                            return False
                self.wake_up(car_id)
                data = self.get(car_id, 'data')
                if data and data['response']:
                    self.__climate[car_id] = data['response']['climate_state']
                    self.__charging[car_id] = data['response']['charge_state']
                    self.__state[car_id] = data['response']['vehicle_state']
                    self.__driving[car_id] = data['response']['drive_state']
                    self.__gui[car_id] = data['response']['gui_settings']
                    self.__last_update_time[car_id] = time.time()
                else:
                    self.__climate[car_id] = False
                    self.__charging[car_id] = False
                    self.__state[car_id] = False
                    self.__driving[car_id] = False
                    self.__gui[car_id] = False
                return True

    def get_climate_params(self, car_id):
        return self.__climate[car_id]

    def get_charging_params(self, car_id):
        return self.__charging[car_id]

    def get_state_params(self, car_id):
        return self.__state[car_id]

    def get_drive_params(self, car_id):
        return self.__driving[car_id]

    def get_gui_params(self, car_id):
        return self.__gui[car_id]

    def get_updates(self, car_id=None):
        if car_id is not None:
            return self.__update[car_id]
        else:
            return self.__update

    def set_updates(self, car_id, value):
        self.__update[car_id] = value
