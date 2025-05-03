import RPi.GPIO as GPIO
import time

# Use BCM numbering
GPIO.setmode(GPIO.BCM)

# Set up pin 25 as input with a pull-up resistor (change if needed)
GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Reading input on GPIO 25. Press Ctrl+C to stop.")

try:
    while True:
        input_state = GPIO.input(25)
        print(f"GPIO 25: {input_state}")
        time.sleep(0.1)  # Slight delay to avoid flooding the output

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    GPIO.cleanup()
