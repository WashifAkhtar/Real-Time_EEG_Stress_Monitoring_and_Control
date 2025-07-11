# arduino_control.py

import serial    
import numpy as np
import tensorflow as tf
import time

# === Load CNN Model === #
model = tf.keras.models.load_model("models/anshu_cnn_base_model.h5")
print("🤖 Model loaded.")

# === Serial Port Setup === #
COM_PORT = 'COM7'
BAUD_RATE = 115200

try:
    ser = serial.Serial(COM_PORT, BAUD_RATE)
    print("🔌 Connected to Arduino.")           

    while True:
        line = ser.readline().decode("latin-1").strip()
        values = line.split(',')

        if len(values) >= 2 and values[0].isdigit() and values[1].isdigit():
            fp1 = float(values[0])
            fp2 = float(values[1])
            input_data = np.array([[[fp1, fp2]]], dtype=np.float32)

            # Predict stress level
            prediction = model.predict(input_data, verbose=0)
            stress_prob = prediction[0][1]  # Stress class probability
 
            print(f"🧠 Stress: {stress_prob*100:.2f}%")

            if stress_prob >= 0.5:
                ser.write(b'1')  # Stress = ON
                print("⚡ Sent '1' to Arduino (Stress)")
            else:
                ser.write(b'0')  # Relax = OFF
                print("💤 Sent '0' to Arduino (Relax)")

        time.sleep(0.05)

except Exception as e:
    print(f"[!] Error: {e}")

finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
    print("🛑 Arduino control session ended.")
