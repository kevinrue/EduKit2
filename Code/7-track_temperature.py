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

# Set the three GPIO pins for Output
GPIO.setup(18, GPIO.OUT) # red
GPIO.setup(24, GPIO.OUT) # blue
GPIO.setup(22, GPIO.OUT) # buzz

GPIO.output(18, GPIO.LOW)
GPIO.output(24, GPIO.LOW)
GPIO.output(22, GPIO.LOW)

parser = argparse.ArgumentParser(description='Track temperature relative to a baseline.')

parser.add_argument('-w', '--base_window', type=int, default=5,
                    help='''count of consecutive measurements within `base_range` degrees Celsius of each other
                    required to set a baseline temperature.''')

parser.add_argument('-B', '--base_range', type=float, default=0.1,
                    help='''maximal difference between `base_window` consecutive measurements to set a
                     baseline temperature.''')

parser.add_argument('outfile', type=argparse.FileType('w', bufsize=1),
                    help='''file where the time and temperature should be logged.
                    Defaults to the standard output.''')

parser.add_argument('start_temp_diff', type=float,
                    help='signed difference from baseline temperature to start the measurement cycle')

parser.add_argument('end_temp_diff', type=float,
                    help='signed difference from baseline temperature to end the measurement cycle')

# Parse command-line arguments
args = parser.parse_args()

sys.stdout.write('=== Settings ===\n')
sys.stdout.write("base_window: {}\n".format(args.base_window))
sys.stdout.write("base_range: {}\n".format(args.base_range))
sys.stdout.write("outfile: {}\n".format(args.outfile))
sys.stdout.write("start_temp_diff: {}\n".format(args.start_temp_diff))
sys.stdout.write("end_temp_diff: {}\n\n".format(args.end_temp_diff))

# Sanity checks
if args.start_temp_diff * args.end_temp_diff < 0:
    print('''WARNING: `start_temp_diff` and `end_temp_diff` should have identical signs''')

if abs(args.start_temp_diff) < abs(args.end_temp_diff):
    print('''WARNING: `start_temp_diff` should be larger than `end_temp_diff` to avoid an infinite loop''')

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

sys.stdout.write('\n=== Step 1: Setting baseline ===\n')

# Initialise the count of (successful) measurements
count_cycles = 0

# Cycle 1: Set baseline
# wait until `base_window` consecutive measurements are within `base_range` of each other to set base_temp and continue
while base_temp < -273.15:
    # Wait 0.9 seconds
    time.sleep(0.9)
    # Flash the blue led for 0.1 seconds
    GPIO.output(24, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(24, GPIO.LOW)
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
    # Add new measurement
    latest_temp.append(temp)
    # Keep only latest `base_window` measurements
    if len(latest_temp) > args.base_window:
        latest_temp.pop(0)
        # If a full window of measurements is available, check if a stable baseline was reached
        npa = numpy.array(latest_temp)
        if npa.ptp() < args.base_range:
            base_temp = npa.mean()
    # Write time and temperature in output file (or std out)
    args.outfile.write(data_line.format(time_s, temp))

sys.stdout.write('\n=== Step 1 complete: Baseline {0} degrees C ===\n'.format(base_temp))

sys.stdout.write('\n=== Step 2: Detect start of experiment ===\n')

# Reset the count of (successful) measurements
count_cycles = 0

# Turn on the blue led solid (indicate baseline is found)
GPIO.output(24, GPIO.HIGH)
# Buzz for 1s
GPIO.output(22, GPIO.HIGH)
time.sleep(0.25)
GPIO.output(22, GPIO.LOW)

# Cycle 2: Detect start of experiment
# wait until the temperature has changed sufficiently from the baseline to enter the measurement cycle and continue
while (temp - base_temp) < args.start_temp_diff:
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

sys.stdout.write('\n=== Step 3: Experiment in progress ===\n')

# Reset the count of (successful) measurements
count_cycles = 0

# Turn off the blue led solid (indicate baseline is found)
GPIO.output(24, GPIO.LOW)

# Cycle 3: Measurement cycle
# wait until the temperature has returned sufficiently close to the baseline to end the measurement cycle and terminate
while (temp - base_temp) > args.end_temp_diff:
    # Wait a second
    time.sleep(0.9)
    # Flash the red led for 0.1 seconds (indicate that the experiment is live)
    GPIO.output(18, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(18, GPIO.LOW)
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

# Turn on red led solid and buzz for 1s
GPIO.output(18, GPIO.HIGH)
GPIO.output(22, GPIO.HIGH)
time.sleep(1)

# Turn off LEDs
GPIO.output(18, GPIO.LOW)
GPIO.output(24, GPIO.LOW)

sys.stdout.write('\nExperiment complete.\n')