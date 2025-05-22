#include <SoftwareSerial.h>

SoftwareSerial mySerial(0, 3); // RX, TX (TX unused)

volatile uint16_t pulseDelay = 1500;  // Default delay
const int outputPin = 10;
const int enablePin = 9;
const int controlPin = 7; // This pin determines the enable state

void setup() {
  pinMode(outputPin, OUTPUT);
  pinMode(enablePin, OUTPUT);
  pinMode(controlPin, INPUT);  // Pin 7 as input
  digitalWrite(enablePin, LOW);

  mySerial.begin(19200);
  Serial.begin(9600);
  Serial.println("Ready to receive binary pulseDelay values...");
}

void loop() {
  // Update enablePin based on controlPin (pin 7)
  if (digitalRead(controlPin) == HIGH) {
    digitalWrite(enablePin, HIGH);
  } else {
    digitalWrite(enablePin, LOW);
  }

  // Check if 2 bytes are available
  if (mySerial.available() >= 2) {
    uint8_t low = mySerial.read();    // First byte: low
    uint8_t high = mySerial.read();   // Second byte: high
    pulseDelay = (high << 8) | low;   // Combine to uint16
    Serial.print("pulseDelay received: ");
    Serial.println(pulseDelay);
    pulseDelay = 1500;
  }

  // Output high-frequency square wave
  digitalWrite(outputPin, HIGH);
  delayMicroseconds(pulseDelay);
  digitalWrite(outputPin, LOW);
  delayMicroseconds(pulseDelay);
}
