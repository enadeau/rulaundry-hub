import board
import time
import adafruit_tca9548a
from i2clibraries.i2c_hmc5883l import i2c_hmc5883l


i2c = board.I2C()
tca = adafruit_tca9548a.TCA9548A(i2c)

for channel in range(8):
    print("===" * 10)
    if tca[channel].try_lock():
        print(f"Channel {channel}:")
        addresses = tca[channel].scan()
        print([hex(address) for address in addresses if address != 0x70])
        if channel in (1, 3):
            sensor = i2c_hmc5883l(1)
            sensor.setContinuousMode()
            print(sensor.getAxes())
        tca[channel].unlock()

CHANNELS = [1, 3]

for channel in CHANNELS:
    with open(f"data{channel}.csv", "w"):
        pass

start = time.time()
i = 3
while True:
    for channel in CHANNELS:
        if tca[channel].try_lock():
            sensor = i2c_hmc5883l(1)
            sensor.setContinuousMode()
            axes = sensor.getAxes()
            tca[channel].unlock()
        timemark = time.time() - start
        with open(f"data{channel}.csv", "a") as fp:
            fp.write(f"{timemark}, {axes[0]}, {axes[1]}, {axes[2]}\n")
        i += 1
        print(i)
    time.sleep(0.5)
