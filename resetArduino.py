import RPi.GPIO as GPIO
import time

ARDUINO_RESET_GPIO = 10  # Use the GPIO you connected

GPIO.setmode(GPIO.BCM)
GPIO.setup(ARDUINO_RESET_GPIO, GPIO.OUT)

# Pull RESET low for 100ms
GPIO.output(ARDUINO_RESET_GPIO, GPIO.LOW)
time.sleep(1)
GPIO.output(ARDUINO_RESET_GPIO, GPIO.HIGH)

print("Arduino reset triggered.")

GPIO.cleanup()
