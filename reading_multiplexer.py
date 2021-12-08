import math
import statistics
import time
from typing import Tuple

import adafruit_tca9548a # type: ignore
import board # type: ignore
import requests

from i2clibraries.i2c_hmc5883l import i2c_hmc5883l

UPDATE_REQUEST_URL = "http://ruwashing.enadeau.duckdns.org/api/machine/{id}"
MAX_FAIL_READ = 5


class ReadingError(Exception):
    pass


i2c = board.I2C()
tca = adafruit_tca9548a.TCA9548A(i2c)


def scan_multiplexer():
    """
    Scan all the channel of the multiplexer and prints the addresses of the device
    connected.
    """
    for channel in range(8):
        print("===" * 10)
        if tca[channel].try_lock():
            print(f"Channel {channel}:")
            addresses = tca[channel].scan()
            print([hex(address) for address in addresses if address != 0x70])
            tca[channel].unlock()


def norm(vector: Tuple[float, ...]) -> float:
    """
    Returns the L2-norm of the given vector.
    """
    return math.sqrt(sum(x ** 2 for x in vector))


class Machine:
    def __init__(self, machine_id: int, sensor_channel: int) -> None:
        self.id = machine_id
        self.sensor_channel = sensor_channel

    def update_status(self):
        try:
            new_status = "ON" if self.ison() else "OFF"
        except ReadingError:
            new_status = "UNKNOWN"
        data = {"status": new_status}
        response = requests.put(UPDATE_REQUEST_URL.format(id=self.id), json=data)
        response.raise_for_status()

    def ison(self) -> bool:
        """
        Read data from the sensor to decide if the machine is on.
        """
        return self.variance() > 100

    def variance(self) -> float:
        """
        Takes 10 measurements of the magnetic field spaced by 0.1 second and returns the
        variance of the norm of those measurements.
        """
        data_points = []
        for _ in range(10):
            data_points.append(norm(self.read_sensor()))
            time.sleep(0.1)
        return statistics.variance(data_points)

    def read_sensor(self) -> Tuple[float, float, float]:
        """
        Read a data point from the sensor

        Raises `ReadingError` if it cannot read from the sensor after 5 attempts.
        """
        if tca[self.sensor_channel].try_lock():
            num_fail = 0
            while True:
                try:
                    sensor = i2c_hmc5883l(1)
                    axes = sensor.getAxes()
                    break
                except OSError as e:
                    num_fail += 1
                    time.sleep(0.1)
                    if num_fail > MAX_FAIL_READ:
                        raise ReadingError(
                            f"Failed to read from the sensor after {MAX_FAIL_READ} attempt"
                        ) from e
            tca[self.sensor_channel].unlock()
        return axes

    def __repr__(self) -> str:
        return f"Machine(mahcine_id={self.id}, sensor_channel={self.sensor_channel})"


machine1 = Machine(1, 1)
machine3 = Machine(3, 3)


while True:
    machine1.update_status()
    machine3.update_status()
    time.sleep(1)


def save_machine_data():
    MACHINES = [Machine(1, 1), Machine(3, 3)]
    start = time.time()
    for machine in MACHINES:
        with open(f"data{machine.id}.csv", "w") as fp:
            pass
    i = len(MACHINES)
    while True:
        for machine in MACHINES:
            axes = machine.read_sensor()
            timemark = time.time() - start
            with open(f"data{machine.id}.csv", "a") as fp:
                fp.write(f"{timemark}, {axes[0]}, {axes[1]}, {axes[2]}\n")
            i += 1
            print(i)
        time.sleep(0.1)


save_machine_data()
