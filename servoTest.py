import sys
import RPi.GPIO as GPIO
from hx711v0_5_1 import HX711
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
import time

factory = PiGPIOFactory()
servo = Servo(17, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory=factory)
maxPressure = 300
oneBarEquivalentPressure = 100
oneBarServoValue = 0.38
minimumWeightForRelease = 5
#servo value 0.38 yra 1 bar
GPIO.setmode(GPIO.BCM)
GPIO.setup(14, GPIO.OUT)
GPIO.output(14, GPIO.LOW)


def getPressure():
    rawBytes = hx.getRawBytes()
    pressure = round(hx.rawBytesToWeight(rawBytes))
    return pressure
    

hx = HX711(5, 6)
hx.setReadingFormat("MSB", "MSB")
hx.autosetOffset()
referenceUnit = 9000
hx.setReferenceUnit(referenceUnit)

if __name__ == "__main__":
    try:
        while True:
            print(getPressure())
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()
        print("[INFO] Exiting...")
        sys.exit()
