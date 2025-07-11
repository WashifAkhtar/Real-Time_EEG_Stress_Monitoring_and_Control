# data/collect_data.py

import serial
import csv
import time
import datetime
import os

COM_PORT = 'COM7'  # Replace with your Arduino's COM port
BAUD_RATE = 115200  # Must match the Arduino's BAUD_RATE
FILE_PATH = 'data/signal.csv'  # File to store EEG data

try:
    ser = serial.Serial(COM_PORT, BAUD_RATE)

    file_exists = os.path.isfile(FILE_PATH)
    is_empty = not file_exists or os.stat(FILE_PATH).st_size == 0

    with open(FILE_PATH, 'a', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)

        if is_empty:
            csvwriter.writerow(['Timestamp', 'Fp1', 'Fp2'])

        max_duration = 1200  # seconds
        start_time = time.time()

        print("Collecting data...")

        while time.time() - start_time < max_duration:
            data = ser.readline().decode("latin-1").strip()
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            values = data.split(',')

            if len(values) > 1 and values[0].isdigit() and values[1].isdigit():
                csvwriter.writerow([current_time, values[0], values[1]])
                # print([current_time, values[0], values[1]])

except Exception as e:
    print(f"Error: {e}")

finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
    print("Serial connection closed.")
