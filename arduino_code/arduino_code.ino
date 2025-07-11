#define SAMPLE_RATE 512  // Hz per channel
#define BAUD_RATE 115200
#define INPUT_PIN_1 A0
#define INPUT_PIN_2 A1
const int ledPin = 13;

void setup() {
  pinMode(ledPin, OUTPUT);
  Serial.begin(BAUD_RATE);
}

void loop() {
  // === 1. Serial Input for LED Control ===
  if (Serial.available()) {
    char signal = Serial.read();
    if (signal == '1') {
      digitalWrite(ledPin, HIGH); // Stress → LED ON
    } else if (signal == '0') {
      digitalWrite(ledPin, LOW);  // Relax → LED OFF
    }
  }

  // === 2. EEG Sampling & Transmission ===
  static unsigned long past = 0;
  unsigned long present = micros();
  unsigned long interval = present - past;
  past = present;

  static long timer = 0;
  timer -= interval;

  if (timer < 0) {
    timer += 1000000 / SAMPLE_RATE;

    int sensor_value_1 = analogRead(INPUT_PIN_1);
    int sensor_value_2 = analogRead(INPUT_PIN_2);

    // Output EEG data as CSV
    Serial.print(sensor_value_1);
    Serial.print(",");
    Serial.println(sensor_value_2);
  }
}
