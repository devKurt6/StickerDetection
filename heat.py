import serial
import numpy as np
import matplotlib.pyplot as plt
import time

# Open serial connection (update 'COM3' or '/dev/ttyUSB0' as per your port)
ser = serial.Serial('COM3', 9600)  # Update with your correct serial port
time.sleep(2)  # Wait for the connection to initialize

def read_thermal_data():
    """Read the 8x8 thermal data from the serial output."""
    pixels = []
    while len(pixels) < 64:
        # Read a line from serial (expecting it to send 8x8 values per reading)
        line = ser.readline().decode('utf-8').strip()
        # Each line should contain the temperature data in brackets, we only keep the numerical part
        for value in line.split('['):
            if ']' in value:
                try:
                    # Extract numerical value, if present, and add to list
                    pixel_value = float(value.split(']')[0])
                    pixels.append(pixel_value)
                except ValueError:
                    continue  # Skip invalid entries
    return np.array(pixels).reshape(8, 8)

# Set up the initial plot
plt.ion()  # Enable interactive mode
fig, ax = plt.subplots()
heatmap = ax.imshow(np.zeros((8, 8)), cmap='plasma', interpolation='nearest')
plt.colorbar(heatmap, label='Temperature (°C)')
plt.title("AMG8833 Thermal Camera Real-Time Heatmap")

try:
    while True:
        # Read thermal data from Arduino
        pixels = read_thermal_data()

        # Update the heatmap data
        heatmap.set_data(pixels)

        # Redraw the heatmap
        plt.draw()

        # Pause for a short time to allow the plot to update (1 second)
        plt.pause(1)

except KeyboardInterrupt:
    print("Program interrupted")

finally:
    ser.close()  # Close the serial connection when done
