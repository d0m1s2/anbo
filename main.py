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
    HELP_BUTTON = cfg.HELP_BUTTON_PIN

print("ola")
dSensor = distSensor(trig_pin=cfg.DSENSOR_TRIG_PIN, echo_pin=cfg.DSENSOR_ECHO_PIN)
print("espanol")

reader = SensorReader()
reader.start()
serial_thread_running = True
print("cliat")

last_state = None
state_enter_time = time.time()
last_voiceline_time = time.time()

print("pries pig")
# Initialize pigpio
pi = pigpio.pi()
print("po pig")
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
    global current_val, last_val, oil_pressure, serial_thread_running
    try:
        with serial.Serial('/dev/ttyUSB0', baudrate=19200, timeout=1) as ser:
            while serial_thread_running:
                try:
                    line_bytes = ser.readline()
                    line = line_bytes.decode('utf-8', errors='replace').strip()
                    if line in {'0', '1', '2'}:
                        with lock:
                            val = int(line)
                            last_val = current_val
                            current_val = val
                            if last_val is not None and current_val < last_val:
                                oil_pressure += cfg.PUMP_STEP
                                oil_pressure = min(oil_pressure, 1.0)
                            print(f"Received: {line}, last_val: {last_val}, current_val: {current_val}")
                except UnicodeDecodeError as ude:
                    print(f"[WARN] Decode error: {ude} — skipping line.")
                except Exception as inner_e:
                    print(f"[WARN] Unexpected error in serial loop: {inner_e}")
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        sys.exit()



def restart_serial_thread():
    global reader_thread, serial_thread_running
    print("Restarting serial thread...")
    serial_thread_running = False
    reader_thread.join()
    serial_thread_running = True
    reader_thread = threading.Thread(target=read_serial_loop, daemon=True)
    reader_thread.start()




# Define GPIO setup and events globally
GPIO.setmode(GPIO.BCM)
print("d")

PROP_ENABLE_PIN = cfg.PROP_ENABLE_PIN
GPIO.setup(PROP_ENABLE_PIN, GPIO.OUT)
ARDUINO_RESET_PIN = 10
GPIO.setup(ARDUINO_RESET_PIN, GPIO.OUT)
GPIO.output(ARDUINO_RESET_PIN, GPIO.HIGH)  # Keep it HIGH initially
prop_enable = False
for pin in Inputs:
    GPIO.setup(pin.value, GPIO.IN, pull_up_down=GPIO.PUD_UP)


mag_start = GPIO.input(Inputs.MAG.value)
valve_start = False



input_states = {pin: GPIO.input(pin.value) for pin in Inputs}

print("c")




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

print("b")

# Variables to track the cranking process
cranking_start_time = None
is_cranking = False
stop_cranking = False  # To track if cranking should stop early
crank_completed = False  # To track if cranking has completed successfully

print("a")
def get_start_values():
    global valve_start, mag_start
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


def has_timed_out(timeout_duration):
    return time.time() - state_enter_time > timeout_duration


def print_state():
    print(f"Current State: {current_state.name}")

print("pries kazkokius random")

current_state = gameStates.IDLE
oil_pressure = 0.0
current_val = None
last_val = None
lock = threading.Lock()



print("pries pat main loopa")

# Main loop
try:
    reader_thread = threading.Thread(target=read_serial_loop, daemon=True)
    reader_thread.start()
    print("Starting game. Press buttons in correct order.")
    print_state()
    get_start_values()
    pygame.mixer.stop()
    while True:
        if current_state != last_state:
            last_state = current_state
            state_enter_time = time.time()
            last_voiceline_time = 0  # Force first play immediately when entering

        pico_data = reader.get_data()
        #print(f"P:{oil_pressure}")

        if current_state == gameStates.IDLE:
            set_oil_servo_angle(0)
            prop_enable = False
            dist = dSensor.measure_distance()
            print(dist) 
            if dist <= cfg.DIST_TRIGGER:
                current_state = gameStates.GAME_BEGIN
                print_state()
            time.sleep(0.05)


        if current_state == gameStates.GAME_BEGIN:
            set_oil_servo_angle(0)
            sounds['game_begin'].play()
            time.sleep(sounds['game_begin'].get_length())
            state_enter_time = time.time() 
            current_state = gameStates.WAIT_FOR_MAGNETO
            prop_enable = False
            pygame.mixer.stop()
            oil_pressure = 0.0
            current_val = None
            last_val = None
            crank_completed = False
            is_cranking = False
            sounds_played = {key: False for key in sounds}
            GPIO.output(PROP_ENABLE_PIN, GPIO.LOW)
            reader.stop()
            reader.join()
            reader = SensorReader()
            reader.start()
            get_start_values()
            print(mag_start)
            print(GPIO.input(Inputs.MAG.value))
            print_state()
        


        if current_state == gameStates.WAIT_FOR_MAGNETO:
            set_oil_servo_angle(0)
            if has_timed_out(cfg.INPUT_TIMEOUT+20):
                print("Input timeout. Returning to IDLE.")
                pygame.mixer.stop()
                prop_enable = False
                pygame.mixer.stop()
                oil_pressure = 0.0
                current_val = None
                last_val = None
                crank_completed = False
                is_cranking = False
                sounds_played = {key: False for key in sounds}
                GPIO.output(PROP_ENABLE_PIN, GPIO.LOW)
                reader.stop()
                reader.join()
                reader = SensorReader()
                reader.start()
                get_start_values()
                print(mag_start)
                print(GPIO.input(Inputs.MAG.value))
                current_state = gameStates.IDLE
                print_state()
                continue
            if time.time() - last_voiceline_time >= (sounds['magneto'].get_length() +cfg.VOICE_REPEAT_TIME):
                pygame.mixer.stop()
                time.sleep(1)
                sounds['magneto'].play()
                last_voiceline_time = time.time()
                sounds_played['magneto'] = True
            if GPIO.input(Inputs.MAG.value) != mag_start:
                current_state = gameStates.WAIT_FOR_THROTTLE
                sound_is_playing = False
                prop_enable = False
                pygame.mixer.stop()
                oil_pressure = 0.0
                current_val = None
                last_val = None
                crank_completed = False
                is_cranking = False
                sounds_played = {key: False for key in sounds}
                GPIO.output(PROP_ENABLE_PIN, GPIO.LOW)
                reader.stop()
                reader.join()
                reader = SensorReader()
                reader.start()
                get_start_values()
                print(mag_start)
                print(GPIO.input(Inputs.MAG.value))
                print_state()
                
                

        if current_state == gameStates.WAIT_FOR_THROTTLE:
            set_oil_servo_angle(0)
            if has_timed_out(cfg.INPUT_TIMEOUT):
                print("Input timeout. Returning to IDLE.")
                pygame.mixer.stop()
                prop_enable = False
                pygame.mixer.stop()
                oil_pressure = 0.0
                current_val = None
                last_val = None
                crank_completed = False
                is_cranking = False
                sounds_played = {key: False for key in sounds}
                GPIO.output(PROP_ENABLE_PIN, GPIO.LOW)
                reader.stop()
                reader.join()
                reader = SensorReader()
                reader.start()
                get_start_values()
                print(mag_start)
                print(GPIO.input(Inputs.MAG.value))
                current_state = gameStates.IDLE
                print_state()
                continue
            if time.time() - last_voiceline_time >= (sounds['throttle'].get_length()+cfg.VOICE_REPEAT_TIME):
                pygame.mixer.stop()
                time.sleep(1)
                sounds['throttle'].play()
                last_voiceline_time = time.time()
                sounds_played['throttle'] = True
            throttle_value = pico_data.get('throttle')
            print(throttle_value)
            if abs(throttle_value-cfg.THROTTLE_MIN) <= cfg.THROTTLE_TOLERANCE:
                current_state = gameStates.WAIT_FOR_VALVE
                prop_enable = False
                pygame.mixer.stop()
                oil_pressure = 0.0
                current_val = None
                last_val = None
                crank_completed = False
                is_cranking = False
                sounds_played = {key: False for key in sounds}
                GPIO.output(PROP_ENABLE_PIN, GPIO.LOW)
                reader.stop()
                reader.join()
                reader = SensorReader()
                reader.start()
                get_start_values()
                print(mag_start)
                print(GPIO.input(Inputs.MAG.value))
                print_state()
                print_state()
            time.sleep(0.05)
        
        if current_state == gameStates.WAIT_FOR_VALVE:
            set_oil_servo_angle(0)
            if has_timed_out(cfg.INPUT_TIMEOUT):
                print("Input timeout. Returning to IDLE.")
                pygame.mixer.stop()
                prop_enable = False
                pygame.mixer.stop()
                oil_pressure = 0.0
                current_val = None
                last_val = None
                crank_completed = False
                is_cranking = False
                sounds_played = {key: False for key in sounds}
                GPIO.output(PROP_ENABLE_PIN, GPIO.LOW)
                reader.stop()
                reader.join()
                reader = SensorReader()
                reader.start()
                get_start_values()
                print(mag_start)
                print(GPIO.input(Inputs.MAG.value))
                current_state = gameStates.IDLE
                print_state()
                continue
            if time.time() - last_voiceline_time >= (sounds['valve'].get_length()+cfg.VOICE_REPEAT_TIME):
                pygame.mixer.stop()
                time.sleep(1)
                sounds['valve'].play()
                last_voiceline_time = time.time()
                sounds_played['valve'] = True

            valve_value = pico_data.get('valve')
            if valve_start == True:
                if valve_value < cfg.VALVE_THRESHOLD:
                    restart_serial_thread()
                    current_state = gameStates.WAIT_FOR_OIL_PUMP
                    print_state()
            elif valve_start == False:
                restart_serial_thread()
                if valve_value >= cfg.VALVE_THRESHOLD:
                    current_state = gameStates.WAIT_FOR_OIL_PUMP
                    print_state()
            time.sleep(0.05)
                    
        if current_state == gameStates.WAIT_FOR_OIL_PUMP:
            if has_timed_out(cfg.INPUT_TIMEOUT):
                print("Input timeout. Returning to IDLE.")
                pygame.mixer.stop()
                prop_enable = False
                pygame.mixer.stop()
                oil_pressure = 0.0
                current_val = None
                last_val = None
                crank_completed = False
                is_cranking = False
                sounds_played = {key: False for key in sounds}
                GPIO.output(PROP_ENABLE_PIN, GPIO.LOW)
                reader.stop()
                reader.join()
                reader = SensorReader()
                reader.start()
                get_start_values()
                print(mag_start)
                print(GPIO.input(Inputs.MAG.value))
                current_state = gameStates.IDLE
                print_state()
                continue
            if time.time() - last_voiceline_time >= (sounds['pump'].get_length()+cfg.VOICE_REPEAT_TIME):
                pygame.mixer.stop()
                time.sleep(1)
                sounds['pump'].play()
                last_voiceline_time = time.time()
                sounds_played['pump'] = True

            with lock:
                angle = calculate_oil_angle(oil_pressure)
            set_oil_servo_angle(angle)
            with lock:
                if oil_pressure >= 1:
                    set_oil_servo_angle(cfg.PRESSURE_GOAL_ANGLE)
                    current_state = gameStates.WAIT_FOR_STARTER
                    print_state()        

        if current_state == gameStates.WAIT_FOR_STARTER:
            if has_timed_out(cfg.INPUT_TIMEOUT+20):
                print("Input timeout. Returning to IDLE.")
                pygame.mixer.stop()
                prop_enable = False
                pygame.mixer.stop()
                oil_pressure = 0.0
                current_val = None
                last_val = None
                crank_completed = False
                is_cranking = False
                sounds_played = {key: False for key in sounds}
                GPIO.output(PROP_ENABLE_PIN, GPIO.LOW)
                reader.stop()
                reader.join()
                reader = SensorReader()
                reader.start()
                get_start_values()
                print(mag_start)
                print(GPIO.input(Inputs.MAG.value))
                current_state = gameStates.IDLE
                print_state()
                continue
            starter_input = GPIO.input(Inputs.STARTER.value)

            if time.time() - last_voiceline_time >= (sounds['starter'].get_length()+cfg.VOICE_REPEAT_TIME):
                pygame.mixer.stop()
                
                sounds['starter'].play()
                last_voiceline_time = time.time()
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
            if is_cranking and time.time() - cranking_start_time >= cfg.CRANK_TIME and not crank_completed and GPIO.input(Inputs.HELP_BUTTON.value) == GPIO.LOW:
                sounds['crank'].stop()   # Stop the cranking sound after 5 seconds
                print("Starter held long enough: engine running!")
                sounds['running'].play()  # Play the engine running sound
                crank_completed = True  # Mark the cranking as complete
                GPIO.output(PROP_ENABLE_PIN, GPIO.LOW)

            if crank_completed:
                    current_state = gameStates.END
                    print_state()

        if current_state == gameStates.END:
            if not prop_enable:
        # Reset Arduino via GPIO10
                print("Resetting Arduino...")
                GPIO.output(ARDUINO_RESET_PIN, GPIO.LOW)
                time.sleep(0.1)
                GPIO.output(ARDUINO_RESET_PIN, GPIO.HIGH)
                print("Arduino reset complete.")

                prop_enable = True
                prop_start_time = time.time()
                sounds['end'].play()

            elif time.time() - prop_start_time >= sounds['end'].get_length():
                #sounds['end'].get_length()
                pygame.mixer.stop()
                prop_enable = False
                pygame.mixer.stop()
                oil_pressure = 0.0
                current_val = None
                last_val = None
                crank_completed = False
                is_cranking = False
                sounds_played = {key: False for key in sounds}
                GPIO.output(PROP_ENABLE_PIN, GPIO.LOW)
                reader.stop()
                reader.join()
                reader = SensorReader()
                reader.start()
                get_start_values()
                print(mag_start)
                print(GPIO.input(Inputs.MAG.value))
                time.sleep(cfg.SCRIPT_RESTING_TIME)
                current_state = gameStates.IDLE
                print_state()


        
        

        if prop_enable:
            GPIO.output(PROP_ENABLE_PIN, GPIO.HIGH)
        else:
            GPIO.output(PROP_ENABLE_PIN, GPIO.LOW)

except Exception as e:
    print(f"[ERROR] Unexpected exception: {e}")
    print("Restarting script in 3 seconds...")
    time.sleep(3)
    os.execv(sys.executable, ['python3'] + sys.argv)
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
