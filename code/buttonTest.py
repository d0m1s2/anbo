import RPi.GPIO as GPIO
import time
import config as cfg


# Use BCM numbering
GPIO.setmode(GPIO.BCM)
pinas = cfg.HELP_BUTTON_PIN
# Set up pin 25 as input with a pull-up resistor (change if needed)
GPIO.setup(pinas, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Reading input on GPIO. Press Ctrl+C to stop.")

try:
    while True:
        input_state = GPIO.input(pinas)
        print(f"GPIO pinas: {input_state}")
        time.sleep(0.1)  # Slight delay to avoid flooding the output



#what
except KeyboardInterrupt:
    print("\nExiting...")

finally:
    GPIO.cleanup()
