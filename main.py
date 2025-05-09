import RPi.GPIO as GPIO
import sys
import time
import pygame
import serial
from stateMachine import gameStates
from enum import Enum
import config as cfg
from get_pico_data import SensorReader
from gpiozero import Servo
import pigpio
import threading
from distSensor import distSensor


class Inputs(Enum):
    MAG = cfg.MAG_PIN
    STARTER = cfg.STARTER_PIN

dSensor = distSensor(trig_pin=cfg.DSENSOR_TRIG_PIN, echo_pin=cfg.DSENSOR_ECHO_PIN)


reader = SensorReader()
reader.start()



# Initialize pigpio
pi = pigpio.pi()
if not pi.connected:
    print("Failed to connect to pigpio daemon.")
    sys.exit()

def set_oil_servo_angle(angle):
    # Convert angle to pulsewidth: 0° = 500µs, 180° = 2500µs
    pulsewidth = int(500 + (1-(angle / 180.0)) * 2000)
    pi.set_servo_pulsewidth(cfg.OIL_PIN, pulsewidth)


def calculate_oil_angle(oil_pressure):
    oil_angle = oil_pressure * cfg.PRESSURE_GOAL_ANGLE
    return oil_angle

def read_serial_loop():
    global current_val, last_val, oil_pressure
    try:
        with serial.Serial('/dev/ttyUSB1', baudrate=9600, timeout=1) as ser:
            while True:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if line in {'0', '1', '2'}:
                    with lock:
                        val = int(line)
                        last_val = current_val
                        current_val = val
                        if last_val is not None and current_val < last_val:
                            oil_pressure += cfg.PUMP_STEP
                            oil_pressure = min(oil_pressure, 1.0)
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        sys.exit()



# Define GPIO setup and events globally
GPIO.setmode(GPIO.BCM)

PROP_ENABLE_PIN = cfg.PROP_ENABLE_PIN
GPIO.setup(PROP_ENABLE_PIN, GPIO.OUT)
prop_enable = False
for pin in Inputs:
    GPIO.setup(pin.value, GPIO.IN, pull_up_down=GPIO.PUD_UP)


mag_start = GPIO.input(Inputs.MAG.value)
valve_start = False



input_states = {pin: GPIO.input(pin.value) for pin in Inputs}






pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
sounds = {
    'crank': pygame.mixer.Sound(cfg.CRANK_SOUND),
    'running': pygame.mixer.Sound(cfg.RUNNING_SOUND),
    'valve': pygame.mixer.Sound(cfg.VALVE_SOUND),
    'throttle': pygame.mixer.Sound(cfg.THROTTLE_SOUND),
    'pump': pygame.mixer.Sound(cfg.PUMP_SOUND),
    'magneto': pygame.mixer.Sound(cfg.MAGNETO_SOUND),
    'end': pygame.mixer.Sound(cfg.END_SOUND),
    'game_begin' : pygame.mixer.Sound(cfg.GAME_BEGIN_SOUND),
    'starter' : pygame.mixer.Sound(cfg.STARTER_SOUND)
}


sounds_played = {key: False for key in sounds}



# Variables to track the cranking process
cranking_start_time = None
is_cranking = False
stop_cranking = False  # To track if cranking should stop early
crank_completed = False  # To track if cranking has completed successfully


def get_start_values():
    global valve_start
    mag_start = GPIO.input(Inputs.MAG.value)
    pico_data = reader.get_data()
    valve_value = None
    valve_value = None
    while valve_value is None:
        pico_data = reader.get_data()
        valve_value = pico_data.get('valve')
        if valve_value is None:
            time.sleep(0.01) 
    if valve_value >= cfg.VALVE_THRESHOLD:
        valve_start = True
        
    else:
        valve_start = False
    print(f"valve value is: {valve_value}")




def print_state():
    print(f"Current State: {current_state.name}")


current_state = gameStates.IDLE
oil_pressure = 0.0
current_val = None
last_val = None
lock = threading.Lock()

# Main loop
try:
    reader_thread = threading.Thread(target=read_serial_loop, daemon=True)
    reader_thread.start()
    print("Starting game. Press buttons in correct order.")
    print_state()
    get_start_values()
    pygame.mixer.stop()
    while True:
        pico_data = reader.get_data()


        if current_state == gameStates.IDLE:
            prop_enable = False
            dist = dSensor.measure_distance()
            print(dist) 
            if dist <= cfg.DIST_TRIGGER:
                current_state = gameStates.GAME_BEGIN
                print_state()
            time.sleep(0.05)


        if current_state == gameStates.GAME_BEGIN:
            sounds['game_begin'].play()
            time.sleep(24)
            current_state = gameStates.WAIT_FOR_MAGNETO
            print_state()
        


        if current_state == gameStates.WAIT_FOR_MAGNETO:
            
            if not sounds_played['magneto']:
                pygame.mixer.stop()
                sounds['magneto'].play()
                sounds_played['magneto'] = True
            if GPIO.input(Inputs.MAG.value) != mag_start:
                current_state = gameStates.WAIT_FOR_THROTTLE
                sound_is_playing = False
                print_state()
                
                

        if current_state == gameStates.WAIT_FOR_THROTTLE:
            
            if not sounds_played['throttle']:
                    pygame.mixer.stop()
                    sounds['throttle'].play()
                    sounds_played['throttle'] = True
            throttle_value = pico_data.get('throttle')
            print(throttle_value)
            if abs(throttle_value-cfg.THROTTLE_MIN) <= cfg.THROTTLE_TOLERANCE:
                current_state = gameStates.WAIT_FOR_VALVE
                print_state()
            time.sleep(0.05)
        
        if current_state == gameStates.WAIT_FOR_VALVE:
            if not sounds_played['valve']:
                pygame.mixer.stop()
                sounds['valve'].play()
                sounds_played['valve'] = True
            valve_value = pico_data.get('valve')
            if valve_start == True:
                if valve_value < cfg.VALVE_THRESHOLD:
                    current_state = gameStates.WAIT_FOR_OIL_PUMP
                    print_state()
            elif valve_start == False:
                if valve_value >= cfg.VALVE_THRESHOLD:
                    current_state = gameStates.WAIT_FOR_OIL_PUMP
                    print_state()
            time.sleep(0.05)
                    
        if current_state == gameStates.WAIT_FOR_OIL_PUMP:
            if not sounds_played['pump']:
                pygame.mixer.stop()
                sounds['pump'].play()
                sounds_played['pump'] = True    
            with lock:
                angle = calculate_oil_angle(oil_pressure)
            set_oil_servo_angle(angle)
            with lock:
                if oil_pressure >= 1:
                    current_state = gameStates.WAIT_FOR_STARTER
                    print_state()


        



        # STARTER
        elif current_state == gameStates.WAIT_FOR_STARTER:
            starter_input = GPIO.input(Inputs.STARTER.value)

            if not sounds_played['starter']:
                pygame.mixer.stop()
                sounds['starter'].play()
                sounds_played['starter'] = True

            # When the starter button is pressed
            if starter_input == GPIO.LOW and not is_cranking:
                pygame.mixer.stop()
                is_cranking = True
                crank_completed = False  # Reset completion flag
                cranking_start_time = time.time()
                sounds['crank'].play(-1)  # Play cranking sound indefinitely
                print("Starter held: playing cranking sound...")

            # When the starter button is released early
            elif starter_input == GPIO.HIGH and is_cranking:
                is_cranking = False
                sounds['crank'].stop()  # Stop the cranking sound immediately
                print("Starter released early: cranking aborted.")

            # Check if cranking was held long enough (5 seconds)
            if is_cranking and time.time() - cranking_start_time >= 5 and not crank_completed:
                sounds['crank'].stop()   # Stop the cranking sound after 5 seconds
                print("Starter held long enough: engine running!")
                sounds['running'].play()  # Play the engine running sound
                crank_completed = True  # Mark the cranking as complete

            if crank_completed:
                    current_state = gameStates.END
                    print_state()
            # If the cranking was aborted, just continue
                

        # END state (just wait here for now)
        elif current_state == gameStates.END:
            if not prop_enable:
                prop_enable = True
                prop_start_time = time.time()
                sounds['end'].play()

            elif time.time() - prop_start_time >= 40:
                prop_enable = False
                current_state = gameStates.IDLE
                print_state()

        
        

        if prop_enable:
            GPIO.output(PROP_ENABLE_PIN, GPIO.HIGH)
        else:
            GPIO.output(PROP_ENABLE_PIN, GPIO.LOW)
        




except KeyboardInterrupt:
    print("\nExiting...")
    # pico reader close
    reader.stop()
    reader.join()
    dSensor.cleanup()

finally:
    GPIO.cleanup()
    pygame.mixer.quit()
    pi.set_servo_pulsewidth(cfg.OIL_PIN, 0)
    pi.stop()
