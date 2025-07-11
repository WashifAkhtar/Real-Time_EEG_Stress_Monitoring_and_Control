import serial
import numpy as np
import tensorflow as tf
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import csv
from datetime import datetime

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

# === Setup CSV Logging === #
csv_filename = f"stress_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
# Open the file in append mode so we can write incrementally
csv_file = open(csv_filename, mode='w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["Timestamp", "Relative Time (s)", "Stress Probability (%)", "Latency (ms)"])
print(f"📄 Logging data to {csv_filename}")

# === Setup Plot === #
plt.figure(figsize=(10, 6))
line, = plt.plot([], [], 'r-', linewidth=2)
plt.xlabel("Time (s)")
plt.ylabel("Stress Probability (%)")
plt.title("Real-time EEG Stress Monitoring")
plt.grid(True)
plt.ylim(0, 100)
plt.xlim(0, 60)  # Start with a 60-second window

# Add text annotations for averages
avg_text = plt.text(0.02, 0.92, "Average Stress: 0.0%", transform=plt.gca().transAxes, 
                  bbox=dict(facecolor='white', alpha=0.7), fontsize=10)

# Add stress level indicator box
stress_indicator = plt.text(0.02, 0.85, "NORMAL", transform=plt.gca().transAxes,
                          bbox=dict(facecolor='green', alpha=0.7), fontsize=10, 
                          color='white', fontweight='bold', ha='left')

# Add threshold lines
plt.axhline(y=50, color='yellow', linestyle='--', alpha=0.7, label='Moderate Stress (50%)')
plt.axhline(y=90, color='red', linestyle='--', alpha=0.7, label='High Stress (90%)')

# Function to update the plot
def update_plot(frame):
    if timestamps:
        # Update plot data
        line.set_data(timestamps, [s * 100 for s in stress_probs])
        
        # Adjust x-axis limits to show the last 60 seconds of data
        if timestamps[-1] > 60:
            plt.xlim(max(0, timestamps[-1] - 60), timestamps[-1])
        
        # Calculate and update average stress
        avg_stress = sum([s * 100 for s in stress_probs]) / len(stress_probs) if stress_probs else 0
        avg_latency = sum(latencies) / len(latencies) * 1000 if latencies else 0
        
        # Update text annotations
        avg_text.set_text(f"Average Stress: {avg_stress:.1f}%")
        
        # Update stress indicator based on thresholds
        if avg_stress > 90:
            stress_indicator.set_text("HIGH STRESS")
            stress_indicator.set_bbox(dict(facecolor='red', alpha=0.8))
        elif avg_stress > 50:
            stress_indicator.set_text("MODERATE STRESS")
            stress_indicator.set_bbox(dict(facecolor='orange', alpha=0.8))
        else:
            stress_indicator.set_text("NORMAL")
            stress_indicator.set_bbox(dict(facecolor='green', alpha=0.8))
        
        # Update title with information
        plt.title(f"🧠 Stress Monitoring | Latency: {avg_latency:.1f}ms")
    
    return line, avg_text, stress_indicator,

# Start the animation
ani = FuncAnimation(plt.gcf(), update_plot, interval=200, blit=True)

# Add legend for threshold lines
plt.legend(loc='upper right')

# Function to handle data collection and processing
def process_eeg_data():
    global timestamps, stress_probs, latencies, start_time
    
    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE)
        print("🔌 Serial connection established. Reading EEG...")
        
        while True:
            try:
                line = ser.readline().decode("latin-1").strip()
                values = line.split(',')
                
                if len(values) >= 2 and values[0].isdigit() and values[1].isdigit():
                    # Get raw EEG values
                    fp1 = float(values[0])
                    fp2 = float(values[1])
                    
                    # Prepare input for model
                    input_data = np.array([[[fp1, fp2]]], dtype=np.float32)
                    
                    # Measure prediction time
                    t1 = time.time()
                    prediction = model.predict(input_data, verbose=0)
                    t2 = time.time()
                    
                    # Calculate metrics
                    latency = t2 - t1
                    stress_prob = prediction[0][1]  # Class 1 = stress
                    timestamp = t2 - start_time
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    
                    # Store logs
                    latencies.append(latency)
                    stress_probs.append(stress_prob)
                    timestamps.append(timestamp)
                    
                    # Write to CSV
                    csv_writer.writerow([current_time, f"{timestamp:.3f}", f"{stress_prob * 100:.2f}", f"{latency * 1000:.2f}"])
                    csv_file.flush()  # Ensure data is written immediately
                    
                    print(f"[{timestamp:.2f}s] 🧠 Stress: {stress_prob * 100:.2f}% | ⏱️ Latency: {latency * 1000:.2f} ms")
                    
                time.sleep(0.05)
                
            except KeyboardInterrupt:
                print("\n⏹️ Monitoring stopped by user.")
                break
                
            except Exception as e:
                print(f"[!] Error processing data: {e}")
                continue
                
    except Exception as e:
        print(f"[!] Error establishing serial connection: {e}")
        
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
        print("🔌 Serial connection closed.")
        
        # Close CSV file
        if 'csv_file' in locals() and not csv_file.closed:
            csv_file.close()
            print(f"✅ Data saved to {csv_filename}")

# Run in non-blocking mode
import threading
data_thread = threading.Thread(target=process_eeg_data)
data_thread.daemon = True  # Thread will exit when main program exits
data_thread.start()

# Show the plot (this will block the main thread)
plt.tight_layout()
plt.show()

# Cleanup after plot is closed
if 'csv_file' in locals() and not csv_file.closed:
    csv_file.close()
    print(f"✅ Data saved to {csv_filename}")

print("📊 Program ended.")