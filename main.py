import time
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import configuration as conf

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1015(i2c)
ads.gain = 16
channels = {sensor: AnalogIn(ads, sensor) for sensor in conf.SENSORS}

def print_sensor_data(n_measurements=10):
    data = [[] for i in range(len(conf.SENSORS))]
    for j in range(n_measurements):
        time.sleep(1/n_measurements)
        for i, sensor in enumerate(conf.SENSORS):
            # raw = channels[sensor].value
            voltage = channels[sensor].voltage *1000
            data[i].append(voltage)
    results = [time.time()] + [sum(data[i])/len(data[i]) for i in range(len(conf.SENSORS))]
    print(results)
    return results


def monitor():
    while True:
        data = print_sensor_data()

        file='data/sensor_readings.csv'
        with open(file, 'w') as filetowrite:
            row = ",".join([str(v) for v in data])
            filetowrite.write(row)

if __name__ == "__main__":
    monitor()
