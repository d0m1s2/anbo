import pressure
import RPi.GPIO as GPIO
import sys
import time
import pygame
import threading
from stateMachine import gameStates

# gpio pinouts:
# 22 - mag
# 25 - starter
# 27 - valve 

INPUTS = [
    (27, "valve_pot"),
    (22, "mag"),
    (25, "starter")
]

GPIO.setmode(GPIO.BCM)
for pin, _ in INPUTS:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
input_states = {pin: GPIO.input(pin) for pin, _ in INPUTS}
current_state_index = 0

pygame.mixer.init()
CRANK_SOUND = "/home/anbo/anbo_main/engine_crank.mp3"
START_SOUND = "/home/anbo/anbo_main/engine_start.mp3"
crank_sound = pygame.mixer.Sound(CRANK_SOUND)
running_sound = pygame.mixer.Sound(START_SOUND)

crank_thread = None
stop_cranking = threading.Event()

while True:
    try:
        print(pressure.getPressure())
        time.sleep(0.3)
    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()
        print("[INFO] Exiting...")
        sys.exit()
