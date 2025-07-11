# stress_detection.py

import serial
import numpy as np
import tensorflow as tf
import time

# === Load Trained CNN Model === #
model = tf.keras.models.load_model("models/anshu_cnn_base_model.h5")
print("✅ Model loaded successfully.")

# === Setup Serial Port === # 
COM_PORT = 'COM7'
BAUD_RATE = 115200

try:
    ser = serial.Serial(COM_PORT, BAUD_RATE)
    print("🔌 Serial connection established. Reading EEG...")

    while True:
        line = ser.readline().decode("latin-1").strip()
        values = line.split(',')

        if len(values) >= 2 and values[0].isdigit() and values[1].isdigit():
            # Get raw EEG values
            fp1 = float(values[0])
            fp2 = float(values[1])

            # Reshape for CNN input: (1, 1, 2)
            input_data = np.array([[[fp1, fp2]]], dtype=np.float32)

            # Predict stress level
            prediction = model.predict(input_data, verbose=0)
            stress_prob = prediction[0][1]  # Class 1 = stress

            print(f"🧠 Stress Probability: {stress_prob * 100:.2f}%")

        time.sleep(0.05)  # Reduce flicker / control read speed

except Exception as e:
    print(f"[!] Error: {e}")

finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
    print("🔌 Serial connection closed.")
