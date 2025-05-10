import RPi.GPIO as GPIO
import time

class distSensor:
    def __init__(self, trig_pin=17, echo_pin=27, timeout=0.02):
        self.TRIG = trig_pin
        self.ECHO = echo_pin
        self.TIMEOUT = timeout  # seconds

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.TRIG, GPIO.OUT)
        GPIO.setup(self.ECHO, GPIO.IN)
        GPIO.output(self.TRIG, False)
        time.sleep(0.1)  # Let the sensor settle

    def measure_distance(self):
        try:
            # Send 10µs pulse to TRIG
            GPIO.output(self.TRIG, True)
            time.sleep(0.00001)
            GPIO.output(self.TRIG, False)

            # Wait for echo start with timeout
            start_time = time.time()
            timeout_start = time.time()
            while GPIO.input(self.ECHO) == 0:
                start_time = time.time()
                if time.time() - timeout_start > self.TIMEOUT:
                    raise TimeoutError("Timeout waiting for ECHO to go high")

            # Wait for echo end with timeout
            end_time = time.time()
            timeout_start = time.time()
            while GPIO.input(self.ECHO) == 1:
                end_time = time.time()
                if time.time() - timeout_start > self.TIMEOUT:
                    raise TimeoutError("Timeout waiting for ECHO to go low")

            # Calculate distance
            duration = end_time - start_time
            distance = (duration * 34300) / 2

            return distance

        except TimeoutError as e:
            print(f"[Distance Sensor Error] {e}")
            return None

        except Exception as e:
            print(f"[Distance Sensor Unexpected Error] {e}")
            return None

    def cleanup(self):
        # Optionally only clean up this sensor's pins
        GPIO.cleanup([self.TRIG, self.ECHO])
