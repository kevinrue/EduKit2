# CamJam EduKit 2 - Sensors
# Worksheet 3 - Temperature

# Import Libraries
import os
import glob
import time
import datetime
import RPi.GPIO as GPIO
import numpy

# Set the GPIO naming convention
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Set the three GPIO pins for Output
GPIO.setup(18, GPIO.OUT) # red
GPIO.setup(24, GPIO.OUT) # blue
GPIO.setup(22, GPIO.OUT) # buzz

# Initialize the GPIO Pins
os.system('modprobe w1-gpio')  # Turns on the GPIO module
os.system('modprobe w1-therm') # Turns on the Temperature module

# Finds the correct device file that holds the temperature data
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

# A function that reads the sensors data
def read_temp_raw():
    f = open(device_file, 'r') # Opens the temperature device file
    lines = f.readlines() # Returns the text
    f.close()
    return lines

# Convert the value of the sensor into a temperature
def read_temp():
    lines = read_temp_raw() # Read the temperature 'device file'

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
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

# Format of each line in the output log file
log_line = "{0:0.0f}\t{1:0.1f}"

# Print a header for the output log file
print("time_s\ttemp_c")

# Initialise baseline temperature to a dummy value
temp_c_base = -274

# Initialise an array to store the last 10 temperature measured
# to a dummy value
temp_c_latest = numpy.array(range(-284,-274))

# Reference time for the experiment
t0 = datetime.datetime.now()

# Monitor temperature until program is stopped
while True:
    # Current datetime
    time_new = datetime.datetime.now()
    # Current temperature
    temp_c = read_temp()
    # Duration since time 0
    time_delta = time_new - t0
    # Duration since time 0 in seconds
    time_s = time_delta.total_seconds()
    # 
    print(log_line.format(time_s,temp_c))
    # if temp_c > 30:
    #     print("Hot!")
    # elif tempC < 20:
    #     print("Cold!")
    # else:
    #     print("Cosy...")
    time.sleep(1)
