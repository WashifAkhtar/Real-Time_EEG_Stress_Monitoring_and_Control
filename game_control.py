  # game_control.py

import serial
import numpy as np                                          
import tensorflow as tf
from pynput.keyboard import Key, Controller
import time

# === Load Trained Model === #
model = tf.keras.models.load_model("models/anshu_cnn_base_model.h5")
print("🎮 Model loaded.")       

# === Keyboard Setup === #
keyboard = Controller()
prev_key = None  # Track previously pressed key to avoid flickering

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

            # Predict stress
            prediction = model.predict(input_data, verbose=0)
            stress_prob = prediction[0][1]  # Stress class prob

            print(f"🧠 Stress: {stress_prob*100:.2f}%")

            if stress_prob >= 0.5:
                if prev_key != 'w':
                    if prev_key == Key.space:
                        keyboard.release(Key.space)
                    keyboard.press('w')
                    prev_key = 'w'
                    print("⬆️ Pressing W (Stress)")
            else:
                if prev_key != Key.space:
                    if prev_key == 'w':
                        keyboard.release('w')
                    keyboard.press(Key.space)
                    prev_key = 's'
                    print("⬇️ Pressing Space (Relax)")

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