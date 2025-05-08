import RPi.GPIO as GPIO
import time

class distSensor:
    def __init__(self, trig_pin=17, echo_pin=27):
        self.TRIG = trig_pin
        self.ECHO = echo_pin

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.TRIG, GPIO.OUT)
        GPIO.setup(self.ECHO, GPIO.IN)
        GPIO.output(self.TRIG, False)
        time.sleep(0.1)  # Let the sensor settle

    def measure_distance(self):
        # Send 10µs pulse to TRIG
        GPIO.output(self.TRIG, True)
        time.sleep(0.00001)
        GPIO.output(self.TRIG, False)

        # Wait for echo start
        start_time = time.time()
        while GPIO.input(self.ECHO) == 0:
            start_time = time.time()

        # Wait for echo end
        end_time = time.time()
        while GPIO.input(self.ECHO) == 1:
            end_time = time.time()

        # Calculate distance
        duration = end_time - start_time
        distance = (duration * 34300) / 2

        return distance

    def cleanup(self):
        GPIO.cleanup()
