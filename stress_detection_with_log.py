import serial
import numpy as np
import tensorflow as tf
import time
import matplotlib.pyplot as plt

# === Load Trained CNN Model === #
model = tf.keras.models.load_model("models/anshu_cnn_base_model.h5")
print("✅ Model loaded successfully.")

# === Setup Serial Port === # 
COM_PORT = 'COM7'
BAUD_RATE = 115200

# Logging lists
timestamps = []
stress_probs = []
latencies = []

start_time = time.time()
duration = 60  # seconds

try:
    ser = serial.Serial(COM_PORT, BAUD_RATE)
    print("🔌 Serial connection established. Reading EEG...")

    while True:
        if time.time() - start_time > duration:
            break

        line = ser.readline().decode("latin-1").strip()
        values = line.split(',')

        if len(values) >= 2 and values[0].isdigit() and values[1].isdigit():
            # Get raw EEG values
            fp1 = float(values[0])
            fp2 = float(values[1])

            input_data = np.array([[[fp1, fp2]]], dtype=np.float32)

            t1 = time.time()
            prediction = model.predict(input_data, verbose=0)
            t2 = time.time()

            latency = t2 - t1
            stress_prob = prediction[0][1]  # Class 1 = stress
            timestamp = t2 - start_time

            # Store logs
            latencies.append(latency)
            stress_probs.append(stress_prob)
            timestamps.append(timestamp)

            print(f"[{timestamp:.2f}s] 🧠 Stress: {stress_prob * 100:.2f}% | ⏱️ Latency: {latency * 1000:.2f} ms")

        time.sleep(0.05)

except Exception as e:
    print(f"[!] Error: {e}")

finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
    print("🔌 Serial connection closed.")

    # === Save log to CSV with full timestamp === #
    import csv
    from datetime import datetime

    csv_filename = "stress_log.csv"
    try:
        with open(csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Stress Probability", "Latency (ms)"])
            for t, s, l in zip(timestamps, stress_probs, latencies):
                time_str = datetime.now().strftime("%d:%m:%Y:%H:%M:%S")
                stress_pct = f"{s * 100:.2f}%"
                latency_ms = f"{l * 1000:.3f}"
                writer.writerow([time_str, stress_pct, latency_ms])
        print(f"📄 Logged data to {csv_filename}")
    except Exception as e:
        print(f"[!] Failed to write CSV: {e}")

    # === Plotting Stress over Time === #
    if timestamps and stress_probs:
        stress_percentages = [s * 100 for s in stress_probs]
        avg_stress_pct = sum(stress_percentages) / len(stress_percentages)
        avg_latency_ms = sum(latencies) / len(latencies) * 1000

        plt.figure(figsize=(10, 5))
        plt.plot(timestamps, stress_percentages, label="Stress Probability (%)", color="crimson")
        plt.xlabel("Time (s)")
        plt.ylabel("Stress Probability (%)")
        plt.ylim(0, 100)
        plt.title(
            f"🧠 Stress Confidence Over {duration} Seconds\n"
            f"Avg Stress: {avg_stress_pct:.2f}% | Avg Latency: {avg_latency_ms:.2f} ms"
        )
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.savefig("stress_over_time.png")
        plt.show()
