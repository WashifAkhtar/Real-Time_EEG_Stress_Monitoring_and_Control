import serial    
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from datetime import datetime
import time
import csv

# === Load CNN Model === #
model = tf.keras.models.load_model("models/anshu_cnn_base_model.h5")
print("🤖 Model loaded.")

# === Serial Port Setup === #
COM_PORT = 'COM7'
BAUD_RATE = 115200

# === Logging === #
timestamps = []
stress_probs = []
latencies = []
led_states = []

# Run duration in seconds (optional cap)
start_time = time.time()
duration = 60  # 2 minutes

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
            stress_prob = prediction[0][1]
            stress_pct = stress_prob * 100
            current_time = datetime.now().strftime("%d:%m:%Y:%H:%M:%S")
            led_state = "ON" if stress_prob >= 0.5 else "OFF"

            if stress_prob >= 0.5:
                ser.write(b'1')
                print("⚡ Sent '1' to Arduino (Stress)")
            else:
                ser.write(b'0')
                print("💤 Sent '0' to Arduino (Relax)")

            # Logging
            timestamps.append(current_time)
            stress_probs.append(stress_pct)
            latencies.append(latency)
            led_states.append(led_state)

            print(f"[{current_time}] 🧠 Stress: {stress_pct:.2f}% | LED: {led_state} | ⏱️ Latency: {latency*1000:.2f} ms")

        time.sleep(0.05)

except Exception as e:
    print(f"[!] Error: {e}")

finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
    print("🛑 Arduino control session ended.")

    # === Save CSV Log === #
    try:
        with open("arduino_stress_log.csv", mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Stress Probability (%)", "Latency (ms)", "LED State"])
            for t, s, l, led in zip(timestamps, stress_probs, latencies, led_states):
                writer.writerow([t, f"{s:.2f}%", f"{l * 1000:.3f}", led])
        print("📄 Logged data to arduino_stress_log.csv")
    except Exception as e:
        print(f"[!] Failed to write CSV: {e}")

    # === Plot Stress vs LED State === #
    if stress_probs:
        # Convert timestamp strings to relative seconds
        time_secs = list(range(len(stress_probs)))
        avg_latency = sum(latencies) / len(latencies) * 1000

        led_colors = ['red' if state == "ON" else 'blue' for state in led_states]

        plt.figure(figsize=(12, 6))
        plt.scatter(time_secs, stress_probs, c=led_colors, label="Stress % (Red=ON, Blue=OFF)", alpha=0.7)
        plt.plot(time_secs, stress_probs, color='gray', linestyle='--', alpha=0.4)
        plt.xlabel("Time (samples)")
        plt.ylabel("Stress Probability (%)")
        plt.title(f"📊 Real-Time Stress Detection vs. LED State\nAvg Latency: {avg_latency:.2f} ms")
        plt.ylim(0, 100)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig("arduino_stress_plot.png")
        plt.show()
