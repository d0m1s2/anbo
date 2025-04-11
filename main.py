import pressure
import RPi.GPIO as GPIO
import sys
import time
import pygame
import threading
from stateMachine import gameStates
from enum import Enum


class Inputs(Enum):
    VALVE_POT = 27
    MAG = 22
    STARTER = 25

# Define events globally
stop_cranking = threading.Event()
crank_completed = threading.Event()  # Make sure this is defined globally

GPIO.setmode(GPIO.BCM)
for pin in Inputs:
    GPIO.setup(pin.value, GPIO.IN, pull_up_down=GPIO.PUD_UP)

input_states = {pin: GPIO.input(pin.value) for pin in Inputs}
current_state = gameStates.WAIT_FOR_MAGNETO

pygame.mixer.init()
CRANK_SOUND = "/home/anbo/anbo_main/engine_crank.mp3"
START_SOUND = "/home/anbo/anbo_main/engine_start.mp3"
crank_sound = pygame.mixer.Sound(CRANK_SOUND)
running_sound = pygame.mixer.Sound(START_SOUND)

crank_thread = None

def print_state():
    print(f"Current State: {current_state.name}")

def crank_engine():
    global stop_cranking, crank_completed
    stop_cranking.clear()
    crank_completed.clear()  # Reset event before starting

    print("Starter held: playing cranking sound...")
    
    crank_sound.play(-1)  # Loop indefinitely

    start_time = time.time()
    while time.time() - start_time < 5:
        if stop_cranking.is_set():
            crank_sound.stop()
            print("Starter released early: cranking aborted.")
            return  # Don't set crank_completed in case of early release

        time.sleep(0.1)

    crank_sound.stop()
    print("Starter held long enough: engine running!")
    running_sound.play()

    # Only set crank_completed if cranking was successful
    crank_completed.set()  # Signal that cranking finished successfully

print("Starting game. Press buttons in correct order.")
print_state()

try:
    while current_state != gameStates.END:
        # MAGNETO
        if current_state == gameStates.WAIT_FOR_MAGNETO:
            if GPIO.input(Inputs.MAG.value) == GPIO.LOW:
                current_state = gameStates.WAIT_FOR_VALVE
                print_state()
        # VALVE
        elif current_state == gameStates.WAIT_FOR_VALVE:
            if GPIO.input(Inputs.VALVE_POT.value) == GPIO.LOW:
                current_state = gameStates.WAIT_FOR_STARTER
                print_state()
        # STARTER
        elif current_state == gameStates.WAIT_FOR_STARTER:
            starter_input = GPIO.input(Inputs.STARTER.value)
            if starter_input == GPIO.LOW:
                if crank_thread is None or not crank_thread.is_alive():
                    crank_thread = threading.Thread(target=crank_engine)
                    crank_thread.start()
            else:
                # Starter button released
                stop_cranking.set()

            # Only transition to END if cranking was successful (completed after 5 seconds)
            if crank_completed.is_set():
                current_state = gameStates.END
                print_state()

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    GPIO.cleanup()
    pygame.mixer.quit()
