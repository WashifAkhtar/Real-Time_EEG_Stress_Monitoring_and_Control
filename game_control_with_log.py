import serial
import numpy as np
import tensorflow as tf
from pynput.keyboard import Key, Controller
import matplotlib.pyplot as plt
from datetime import datetime
import time
import csv

# === Load Trained Model === #
model = tf.keras.models.load_model("models/anshu_cnn_base_model.h5")
print("🎮 Model loaded.")       

# === Keyboard Setup === #
keyboard = Controller()
prev_key = None  # Track previously pressed key to avoid flickering

# === Serial Port Setup === #
COM_PORT = 'COM7'
BAUD_RATE = 115200

# === Logging Lists === #
timestamps = []
stress_levels = []
key_presses = []
latencies = []

# Set duration for test (optional)
start_time = time.time()
duration = 60  # seconds

try:
    ser = serial.Serial(COM_PORT, BAUD_RATE)
    print("🔌 Connected to Arduino.")

    while True:
        if time.time() - start_time > duration:
            break

        line = ser.readline().decode("latin-1").strip()
        values = line.split(',')

        if len(values) >= 2 and values[0].isdigit() and values[1].isdigit():
            fp1 = float(values[0])
            fp2 = float(values[1])
            input_data = np.array([[[fp1, fp2]]], dtype=np.float32)

            t1 = time.time()
            prediction = model.predict(input_data, verbose=0)
            t2 = time.time()

            latency = t2 - t1
            stress_prob = prediction[0][1]  # Stress class prob
            stress_pct = stress_prob * 100
            timestamp = t2 - start_time
            latencies.append(latency)

            action = ""

            if stress_prob >= 0.5:
                if prev_key != 'w':
                    if prev_key == Key.space:
                        keyboard.release(Key.space)
                    keyboard.press('w')
                    prev_key = 'w'
                    action = 'W'
                    print("⬆️ Pressing W (Stress)")
            else:
                if prev_key != Key.space:
                    if prev_key == 'w':
                        keyboard.release('w')
                    keyboard.press(Key.space)
                    prev_key = 's'
                    action = 'Space'
                    print("⬇️ Pressing Space (Relax)")

            # Logging
            stress_levels.append(stress_pct)
            timestamps.append(timestamp)
            key_presses.append(action)

            print(f"[{timestamp:.2f}s] 🧠 Stress: {stress_pct:.2f}% | ⌨️ Key: {action} | ⏱️ Latency: {latency * 1000:.2f} ms")

        time.sleep(0.05)

except Exception as e:
    print(f"[!] Error: {e}")

finally:
    # Release keys
    keyboard.release('w')
    keyboard.release(Key.space)
    if 'ser' in locals() and ser.is_open:
        ser.close()
    print("🛑 Game control session ended.")

    # === Save Log to CSV === #
    csv_filename = "game_control_log.csv"
    try:
        with open(csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Stress Probability (%)", "Key Pressed", "Latency (ms)"])
            for t, s, k, l in zip(timestamps, stress_levels, key_presses, latencies):
                time_str = datetime.now().strftime("%d:%m:%Y:%H:%M:%S")
                writer.writerow([time_str, f"{s:.2f}%", k, f"{l * 1000:.3f}"])
        print(f"📄 Logged data to {csv_filename}")
    except Exception as e:
        print(f"[!] Failed to write CSV: {e}")

    # === Plotting === #
    if timestamps and stress_levels:
        avg_latency_ms = sum(latencies) / len(latencies) * 1000
        colors = ['red' if k == 'W' else 'blue' for k in key_presses]

        plt.figure(figsize=(12, 6))
        plt.scatter(timestamps, stress_levels, c=colors, label="Stress % (Red=W, Blue=Space)", alpha=0.8)
        plt.plot(timestamps, stress_levels, color='gray', alpha=0.3)
        plt.xlabel("Time (s)")
        plt.ylabel("Stress Probability (%)")
        plt.title(f"🎮 Real-Time Stress Prediction vs Game Control\nAvg Latency: {avg_latency_ms:.2f} ms")
        plt.ylim(0, 100)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig("game_control_stress_plot.png")
        plt.show()
      