import RPi.GPIO as GPIO
import time
from enum import Enum

# Define Inputs enum for pins to test
class Inputs(Enum):
    VALVE_POT = 27
    MAG = 22
    STARTER = 25

# Setup GPIO
GPIO.setmode(GPIO.BCM)
for pin in Inputs:
    GPIO.setup(pin.value, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Monitoring pin states (CTRL+C to exit)...\n")

try:
    while True:
        for pin in Inputs:
            state = GPIO.input(pin.value)
            level = "LOW" if state == GPIO.LOW else "HIGH"
            print(f"{pin.name}: {level}")
        print("-" * 30)
        time.sleep(0.2)

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    GPIO.cleanup()
