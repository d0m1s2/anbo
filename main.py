import pressure
import RPi.GPIO as GPIO
import sys
import time

# gpio pinouts:
# 22 - mag
# 25 - starter
# 27 - valve 

while True:
    try:
        print(pressure.getPressure())
        time.sleep(0.3)
    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()
        print("[INFO] Exiting...")
        sys.exit()
