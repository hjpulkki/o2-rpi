import time
import sys
import csv
import select
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import configuration as conf

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create ADC object
ads = ADS.ADS1015(i2c)
ads.gain = 16

# Create sensor channels
channels = {sensor: AnalogIn(ads, sensor) for sensor in conf.SENSORS}

# Calibration file
CALIBRATION_FILE = "data/calibration.csv"

calibration_data = {sensor: 0 for sensor in conf.SENSORS}

# Load calibration data
try:
    with open(CALIBRATION_FILE, "r") as f:
        reader = csv.reader(f)
        rows = list(reader)
        if rows:
            last_accepted = [row for row in rows if row[-1] == "accepted"]
            if last_accepted:
                last_calib = last_accepted[-1]
                for i, sensor in enumerate(conf.SENSORS):
                    calibration_data[sensor] = float(last_calib[i + 1])
except FileNotFoundError:
    pass  # No previous calibration

# Function to print sensor readings
def print_sensor_data():
    print("\nSensor   Raw    Voltage(V)   O₂%")
    print("-" * 36)
    for sensor in conf.SENSORS:
        raw = channels[sensor].value
        voltage = channels[sensor].voltage*1000
        o2_percentage = voltage * calibration_data[sensor]
        print(f"P{sensor-1}   {raw:5}   {voltage:6.3f} V   {o2_percentage:6.2f}%")
    print("\nPress 'C' to recalibrate. Press CTRL+C to exit.")

# Calibration function
def calibrate_sensors():
    print("\n🚀 Starting calibration... Expose sensors to **20.9% O₂** (air).")
    time.sleep(2)  # Allow user to prepare
    new_gains = {}

    for sensor in conf.SENSORS:
        voltage = channels[sensor].voltage*1000
        new_gain = 20.9 / voltage
        new_gains[sensor] = new_gain
        print(f"✅ Sensor P{sensor-1}: Measurement = {voltage} mV, New Gain = {new_gain:.6f}")

    accept = input("\nAccept calibration? (y/n): ").strip().lower()
    if accept == "y":
        with open(CALIBRATION_FILE, "a") as f:
            writer = csv.writer(f)
            writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S")] + [new_gains[s] for s in conf.SENSORS] + ["accepted"])
        for sensor in conf.SENSORS:
            calibration_data[sensor] = new_gains[sensor]
        print("\n✅ Calibration saved and applied!\n")
    else:
        print("\n❌ Calibration discarded.\n")

# Main monitoring function
def monitor():
    print("\nPress 'C' to recalibrate. Press CTRL+C to exit.")

    while True:
        # key = input("\nPress 'C' to recalibrate, 'R' to read current values. Press CTRL+C to exit.: ").strip().lower()

        key = sys.stdin.read(1)
        key = key.strip().lower()
        if key == "c":
            calibrate_sensors()
        if key == "r" or key == "":
            print_sensor_data()

        # time.sleep(1)

# Run the program
if __name__ == "__main__":
    monitor()
