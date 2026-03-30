#include <Arduino.h>

// GPS Passthrough Sketch for ESP32-C5
// Connect GPS TX -> ESP IO25 (RX)
// Connect GPS RX -> ESP IO24 (TX)

HardwareSerial GPS_Serial(1);

void setup() {
  // Use Native USB for monitoring
  Serial.begin(115200);
  while (!Serial && millis() < 3000); 

  Serial.println("\n--- ESP32-C5 GPS Test (IO24/IO25) ---");
  Serial.println("Mirroring data between GPS and USB Serial Monitor...");

  // Initialize GPS Serial
  // Pins: TX=24 (Physical 23), RX=25 (Physical 26)
  // Usage: .begin(baud, config, rxPin, txPin)
  GPS_Serial.begin(9600, SERIAL_8N1, 25, 24); 
  
  Serial.println("Started. Waiting for NMEA data...");
}

void loop() {
  // Transfer from GPS to PC
  while (GPS_Serial.available()) {
    Serial.write(GPS_Serial.read());
  }

  // Transfer from PC to GPS (for config commands)
  while (Serial.available()) {
    GPS_Serial.write(Serial.read());
  }
}
