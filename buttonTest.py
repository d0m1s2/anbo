import RPi.GPIO as GPIO
import time
import threading
import pygame

# Define button-to-state mappings
BUTTON_SEQUENCE = [
    (27, "wait for valve"),
    (22, "wait for mag"),
    (25, "wait for starter")
]

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
for pin, _ in BUTTON_SEQUENCE:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

button_states = {pin: GPIO.input(pin) for pin, _ in BUTTON_SEQUENCE}
current_state_index = 0

# Initialize pygame mixer
pygame.mixer.init()

# Load sounds
CRANK_SOUND = "/home/anbo/anbo_main/engine_crank.mp3"
RUNNING_SOUND = "/home/anbo/anbo_main/engine_start.mp3"

crank_sound = pygame.mixer.Sound(CRANK_SOUND)
running_sound = pygame.mixer.Sound(RUNNING_SOUND)

# Track cranking
crank_thread = None
stop_cranking = threading.Event()

def print_state():
    _, state_name = BUTTON_SEQUENCE[current_state_index]
    print(f"Current State: {state_name}")

def crank_engine():
    global stop_cranking
    stop_cranking.clear()
    print("Starter held: playing cranking sound...")
    
    crank_sound.play(-1)  # Loop indefinitely

    start_time = time.time()
    while time.time() - start_time < 5:
        if stop_cranking.is_set():
            crank_sound.stop()
            print("Starter released early: cranking aborted.")
            return
        time.sleep(0.1)

    crank_sound.stop()
    print("Starter held long enough: engine running!")
    running_sound.play()

print("Starting FSM. Press buttons in sequence. Hold starter for 5 seconds to start engine.")
print_state()

try:
    while True:
        if current_state_index >= len(BUTTON_SEQUENCE):
            break

        pin_expected, state_name = BUTTON_SEQUENCE[current_state_index]
        for pin, _ in BUTTON_SEQUENCE:
            current_input = GPIO.input(pin)
            if current_input != button_states[pin]:
                button_states[pin] = current_input

                if current_input == GPIO.LOW:
                    if pin == pin_expected:
                        if state_name == "wait for starter":
                            if crank_thread is None or not crank_thread.is_alive():
                                crank_thread = threading.Thread(target=crank_engine)
                                crank_thread.start()
                        else:
                            current_state_index += 1
                            print_state()
                    else:
                        print(f"Ignored: Button on GPIO {pin} (not in sequence)")
                else:
                    if pin == 25 and state_name == "wait for starter":
                        stop_cranking.set()

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    GPIO.cleanup()
    pygame.mixer.quit()
