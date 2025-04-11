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

# Main crank engine function that will be triggered when the starter is pressed
def crank_engine():
    global stop_cranking, crank_completed
    stop_cranking.clear()
    crank_completed.clear()  # Reset event before starting

    print("Starter held: playing cranking sound...")
    
    crank_sound.play(-1)  # Loop indefinitely

    start_time = time.time()
    # Keep cranking sound playing for 5 seconds or until released early
    while time.time() - start_time < 5:
        if stop_cranking.is_set():  # Button released early
            crank_sound.stop()
            print("Starter released early: cranking aborted.")
            crank_completed.set()  # Mark cranking as aborted
            return
        time.sleep(0.1)

    # If 5 seconds passed, mark the cranking as completed
    crank_sound.stop()
    print("Starter held long enough: engine running!")
    running_sound.play()
    crank_completed.set()  # Signal that cranking finished successfully

print("Starting game. Press buttons in correct order.")
print_state()

try:
    while current_state != gameStates.END:
        # Wait for MAGNETO
        if current_state == gameStates.WAIT_FOR_MAGNETO:
            if GPIO.input(Inputs.MAG.value) == GPIO.LOW:
                current_state = gameStates.WAIT_FOR_VALVE
                print_state()

        # Wait for VALVE
        elif current_state == gameStates.WAIT_FOR_VALVE:
            if GPIO.input(Inputs.VALVE_POT.value) == GPIO.LOW:
                current_state = gameStates.WAIT_FOR_STARTER
                print_state()

        # Wait for STARTER (to trigger the engine cranking)
        elif current_state == gameStates.WAIT_FOR_STARTER:
            starter_input = GPIO.input(Inputs.STARTER.value)

            # Starter button is pressed, start cranking if not already cranking
            if starter_input == GPIO.LOW:
                if crank_thread is None or not crank_thread.is_alive():
                    crank_thread = threading.Thread(target=crank_engine)
                    crank_thread.start()

            # Starter button released early, signal cranking stopped
            elif starter_input == GPIO.HIGH:
                stop_cranking.set()

            # Transition to END if cranking was completed successfully
            if crank_completed.is_set():
                # If cranking was successful, move to END
                if not stop_cranking.is_set():  # Ensure it wasn't aborted
                    current_state = gameStates.END
                    print_state()

        # Final state
        elif current_state == gameStates.END:
            print("Game has ended.")
            time.sleep(10)

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    GPIO.cleanup()
    pygame.mixer.quit()
