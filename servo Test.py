import pigpio
import time

SERVO_GPIO = 12  # Use GPIO 18 (or change to your pin)

# Create pigpio instance
pi = pigpio.pi()
if not pi.connected:
    exit("Could not connect to pigpio daemon!")

def set_servo_angle(angle):
    # Convert angle to pulsewidth: 0° = 500µs, 180° = 2500µs
    pulsewidth = int(500 + (1-(angle / 180.0))* 2000)
    pi.set_servo_pulsewidth(SERVO_GPIO, pulsewidth)

try:
    while True:
        print("Moving to 0°")
        set_servo_angle(0)
        time.sleep(2)
        
        
    
        print("Moving to 60°")
        set_servo_angle(60)
        time.sleep(2)
        print("Moving to 73°")
        set_servo_angle(73)
        time.sleep(2)


except KeyboardInterrupt:
    print("Stopping...")

finally:
    pi.set_servo_pulsewidth(SERVO_GPIO, 0)  # Turn off PWM
    pi.stop()
