import pressure
import RPi.GPIO as GPIO
import sys
import time
import pygame
from stateMachine import gameStates
from enum import Enum

class Inputs(Enum):
    VALVE_POT = 27
    MAG = 22
    STARTER = 25

# Define GPIO setup and events globally
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

# Variables to track the cranking process
cranking_start_time = None
is_cranking = False
stop_cranking = False  # To track if cranking should stop early
crank_completed = False  # To track if cranking has completed successfully

def print_state():
    print(f"Current State: {current_state.name}")

# Main loop
try:
    print("Starting game. Press buttons in correct order.")
    print_state()

    while True:
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

            # When the starter button is pressed
            if starter_input == GPIO.LOW and not is_cranking:
                is_cranking = True
                crank_completed = False  # Reset completion flag
                cranking_start_time = time.time()
                crank_sound.play(-1)  # Play cranking sound indefinitely
                print("Starter held: playing cranking sound...")

            # When the starter button is released early
            elif starter_input == GPIO.HIGH and is_cranking:
                is_cranking = False
                stop_cranking = True
                crank_sound.stop()  # Stop the cranking sound immediately
                print("Starter released early: cranking aborted.")

            # Check if cranking was held long enough (5 seconds)
            if is_cranking and time.time() - cranking_start_time >= 5 and not crank_completed:
                crank_sound.stop()  # Stop the cranking sound after 5 seconds
                print("Starter held long enough: engine running!")
                running_sound.play()  # Play the engine running sound
                crank_completed = True  # Mark the cranking as complete

            # If the cranking was aborted, just continue
            if stop_cranking:
                stop_cranking = False
                # Don't change the state to END unless cranking is successful
                if crank_completed:
                    current_state = gameStates.END
                    print_state()

        # END state (just wait here for now)
        elif current_state == gameStates.END:
            print("Game has ended.")
            time.sleep(10)

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    GPIO.cleanup()
    pygame.mixer.quit()
