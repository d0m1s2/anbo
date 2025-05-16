import RPi.GPIO as GPIO
import time
import config as cfg  # Assumes PROP_ENABLE_PIN is defined here

def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(cfg.PROP_ENABLE_PIN, GPIO.OUT)

    try:
        print("Enabling propeller...")
        GPIO.output(cfg.PROP_ENABLE_PIN, GPIO.HIGH)

        test_duration = 100  # seconds
        time.sleep(test_duration)

        print("Disabling propeller...")
        GPIO.output(cfg.PROP_ENABLE_PIN, GPIO.LOW)

    except KeyboardInterrupt:
        print("\nTest interrupted.")

    finally:
        GPIO.cleanup()
        print("GPIO cleaned up.")

if __name__ == "__main__":
    main()
