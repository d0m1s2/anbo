import servoTest
import RPi.GPIO as GPIO
import sys
import time

while True:
    try:
        print(servoTest.getPressure())
        time.sleep(0.1)
    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()
        print("[INFO] Exiting...")
        sys.exit()
