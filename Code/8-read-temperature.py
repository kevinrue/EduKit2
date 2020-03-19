#!python
# CamJam EduKit 2 - Sensors
# Worksheet 3 - Temperature

# Import Libraries
import os
import glob
import RPi.GPIO as GPIO
import time
import argparse
import sys
import datetime
import numpy

# Set the GPIO naming convention
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

parser = argparse.ArgumentParser(description='Track temperature relative to a baseline.')

parser.add_argument('--outfile', default=sys.stdout, type=argparse.FileType('w', bufsize=1),
                    help='''file where the time and temperature should be logged.
                    Defaults to the standard output.''')

# Parse command-line arguments
args = parser.parse_args()

sys.stdout.write('=== Settings ===\n')
sys.stdout.write("outfile: {}\n".format(args.outfile))

# Initialise the baseline temperature to a dummy value
base_temp = -274

# Initialise a list to store the `base_window` latest temperatures
latest_temp = []

# Initialise the reference time point of the experiment
# all subsequent time points will be measured relative to this one, in seconds
t0 = datetime.datetime.now()

# Define the format of an line of data in the output file
data_line = "{0}\t{1}\n"

# Initialize the GPIO Pins
os.system('modprobe w1-gpio')  # Turns on the GPIO module
os.system('modprobe w1-therm')  # Turns on the Temperature module

# Finds the correct device file that holds the temperature data
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'


# A function that reads the sensors data
def read_temp_raw():
    f = open(device_file, 'r')  # Opens the temperature device file
    lines = f.readlines()  # Returns the text
    f.close()
    return lines


# Convert the value of the sensor into a temperature
def read_temp():
    lines = read_temp_raw()  # Read the temperature 'device file'

    # While the first line does not contain 'YES', wait for 0.2s
    # and then read the device file again.
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()

    # Look for the position of the '=' in the second line of the
    # device file.
    equals_pos = lines[1].find('t=')

    # If the '=' is found, convert the rest of the line after the
    # '=' into degrees Celsius, then degrees Fahrenheit
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c


def time_since_t0():
    # Get the current time
    time_now = datetime.datetime.now()
    # Calculate the relative time elapsed since the reference time point
    time_relative = time_now - t0
    # Convert the relative time to seconds
    time_s = time_relative.total_seconds()
    return time_s


# Write a header for time and temperature in output file (or std out)
args.outfile.write('time\ttemperature\n')

# Reset the count of (successful) measurements
count_cycles = 0

# Collecte temperature
while True:
    # Wait a second
    time.sleep(1)
    # Read the temperature
    temp = read_temp()
    # Get the time since t0 in seconds (as close as possible to the temperature measurement)
    time_s = time_since_t0()
    if not temp: # if no temperature could be read, move on to the next iteration (avoid writing an empty data line)
        continue
    # Increment the count of (successful)
    count_cycles += 1
    # Print a dot on the standard output
    sys.stdout.write('.')
    # Print a newline every 80 dots
    if (count_cycles % 80) == 0:
        sys.stdout.write('\n')
    # Write time and temperature in output file (or std out)
    args.outfile.write(data_line.format(time_s, temp))
