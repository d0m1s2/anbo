import sys
import time
import serial
import pigpio
import threading
import config as cfg

# Initialize pigpio
pi = pigpio.pi()
if not pi.connected:
    print("Failed to connect to pigpio daemon.")
    sys.exit()

# Function to convert oil pressure to servo angle
def calculate_oil_angle(oil_pressure):
    return oil_pressure * cfg.PRESSURE_GOAL_ANGLE

# Function to move servo
def set_oil_servo_angle(angle):
    pulsewidth = int(500 + (1 - (angle / 180.0)) * 2000)
    pi.set_servo_pulsewidth(cfg.OIL_PIN, pulsewidth)

# Shared data
current_val = None
last_val = None
oil_pressure = 0.0
lock = threading.Lock()

# Thread that continuously reads from Arduino
def read_serial_loop():
    global current_val, last_val, oil_pressure
    try:
        with serial.Serial('/dev/ttyUSB0', baudrate=19200, timeout=1) as ser:
            time.sleep(2)
            ser.reset_input_buffer()
            while True:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='replace').strip()
                    if line in {'0', '1', '2'}:
                        with lock:
                            val = int(line)
                            print(f"Raw Arduino Value: {val}")
                            last_val = current_val
                            current_val = val
                            if last_val is not None and current_val < last_val:
                                oil_pressure += cfg.PUMP_STEP
                                oil_pressure = min(oil_pressure, 1.0)
                    else:
                        print(f"Bogus data: {line}")
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        sys.exit()


# Start reader thread
reader_thread = threading.Thread(target=read_serial_loop, daemon=True)
reader_thread.start()

# Main loop for servo control
print("Oil pressure tracking started. Ctrl+C to exit.")
try:
    while True:
        with lock:
            angle = calculate_oil_angle(oil_pressure)
        set_oil_servo_angle(angle)
        #print(f"Oil Pressure: {oil_pressure:.2f}, Servo Angle: {angle:.2f}")

except KeyboardInterrupt:
    print("\nExiting...")

finally:
    pi.set_servo_pulsewidth(cfg.OIL_PIN, 0)
    pi.stop()
