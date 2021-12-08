import time
from typing import Tuple

import adafruit_tca9548a
import board

from i2clibraries.i2c_hmc5883l import i2c_hmc5883l

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


class Machine:
    def __init__(self, machine_id: int, sensor_channel: int) -> None:
        self.id = machine_id
        self.sensor_channel = sensor_channel

    def ison(self) -> bool:
        """
        Read data from the sensor to decide if the machine is on.
        """
        raise NotImplementedError

    def read_sensor(self) -> Tuple[float, float, float]:
        """
        Read a data point from the sensor
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


scan_multiplexer()
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
