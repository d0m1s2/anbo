import time
import sys
import RPi.GPIO as GPIO
from hx711v0_5_1 import HX711
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory

READ_MODE_INTERRUPT_BASED = "--interrupt-based"
READ_MODE_POLLING_BASED = "--polling-based"
READ_MODE = READ_MODE_INTERRUPT_BASED

if len(sys.argv) > 1 and sys.argv[1] == READ_MODE_POLLING_BASED:
    READ_MODE = READ_MODE_POLLING_BASED
    print("[INFO] Read mode is 'polling based'.")
else:
    print("[INFO] Read mode is 'interrupt based'.")
    
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

led_on = False  # Track LED state
weight_above_100_time = None  

def set_servo_position(weight):
    global led_on, weight_above_100_time
    weight = max(0, min(maxPressure, weight))  
    position = 1 - (weight / (maxPressure/2))
    #(weight / (maxPressure/2)) - 1 
    servo.value = position
    
    if weight >= 110:
        if weight_above_100_time is None:
            weight_above_100_time = time.time()
        elif time.time() - weight_above_100_time >= 1:  # Ensure 1-second threshold
            GPIO.output(14, GPIO.HIGH)
            led_on = True
    else:
        weight_above_100_time = None  # Reset timer if weight drops below 100
    
    if weight < minimumWeightForRelease and led_on:
        GPIO.output(14, GPIO.LOW)
        led_on = False

def printWeight(rawBytes):
    weight = round(hx.rawBytesToWeight(rawBytes))
    print(f"[WEIGHT] {weight} gr")
    set_servo_position(weight)

def getWeight():
    rawBytes = hx.getRawBytes()
    weight = round(hx.rawBytesToWeight(rawBytes))
    print(f"[WEIGHT] {weight} gr")
    set_servo_position(weight)

hx = HX711(5, 6)
hx.setReadingFormat("MSB", "MSB")
hx.autosetOffset()
referenceUnit = 9000
hx.setReferenceUnit(referenceUnit)

if READ_MODE == READ_MODE_INTERRUPT_BASED:
    hx.enableReadyCallback(printWeight)

while True:
    try:
        if READ_MODE == READ_MODE_POLLING_BASED:
            getWeight()
    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()
        print("[INFO] Exiting...")
        sys.exit()
