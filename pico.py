from machine import Pin, ADC, UART, PWM
from time import sleep
import json
import struct

# === CONFIGURATION ===
pot1_pin_val = 26
pot2_pin_val = 27
pot3_pin_val = 28
tacho_servo_pin = 16
anemometre_servo_pin = 15
uart0_tx_pin = 0
uart1_tx_pin = 8

prop_enable_tx_pin = 9
prop_enable_rx_pin = 4

baud_rate = 19200
sleep_time = 0.01

throttle_min = 0.5
throttle_max = 0.92
angle_change_threshold = 1.5
angle_smoothing_factor = 0.9
input_smoothing_factor = 0.9
max_pulsedelay = 2000
min_pulsedelay = 1000

ramp_up_speed = 0.005  # slower ramp up
ramp_down_speed = 0.01

# === INITIALIZATION ===
tacho_servo = PWM(Pin(tacho_servo_pin))
tacho_servo.freq(50)

anemometre_servo = PWM(Pin(anemometre_servo_pin))
anemometre_servo.freq(50)

prop_enable_tx = Pin(prop_enable_tx_pin, Pin.OUT)
prop_enable_rx = Pin(prop_enable_rx_pin, Pin.PULL_UP)

pot1 = ADC(Pin(pot1_pin_val))
pot2 = ADC(Pin(pot2_pin_val))
pot3 = ADC(Pin(pot3_pin_val))

uart0 = UART(0, baudrate=baud_rate, tx=Pin(uart0_tx_pin))
uart1 = UART(1, baudrate=baud_rate, tx=Pin(uart1_tx_pin))

# === FUNCTIONS ===
def set_tacho_angle(angle):
    min_duty = 1638
    max_duty = 8192
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    tacho_servo.duty_u16(duty)

def set_anemometre_angle(angle):
    min_duty = 1638
    max_duty = 8192
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    anemometre_servo.duty_u16(duty)

def clamp(val, min_val, max_val):
    return max(min(val, max_val), min_val)

def compute_smoothed_angle(input_value, prev_angle, min_val, max_val, smoothing, invert=False):
    clamped = clamp(input_value, min_val, max_val)
    normalized = (clamped - min_val) / (max_val - min_val)
    angle = normalized * 180
    if invert:
        angle = 180 - angle
    if prev_angle is None:
        return angle
    return smoothing * prev_angle + (1 - smoothing) * angle

# === MAIN LOOP ===
current_throttle = 0.0
smoothed_throttle_val = 0.0
prop_enable_state = False
just_enabled = False

prev_tacho_angle = None
prev_anem_angle = None

while True:
    # Read sensors
    pot1_value = pot1.read_u16()
    pot2_value = pot2.read_u16()
    pot3_value = pot3.read_u16()

    raw_throttle_val = round(pot1_value / 65535, 2)
    valve_val = round(pot2_value / 65535, 2)
    photoresist_val = round(pot3_value / 65535, 2)

    # Smooth throttle input
    smoothed_throttle_val = (
        input_smoothing_factor * smoothed_throttle_val +
        (1 - input_smoothing_factor) * raw_throttle_val
    )

    # Send sensor data over UART0
    data = {
        'throttle': smoothed_throttle_val,
        'valve': valve_val,
        'photoresistor': photoresist_val
    }
    uart0.write(json.dumps(data).encode('utf-8'))
    uart0.write(b'\n')

    # Read enable input
    if prop_enable_rx.value() == 1:
        if not prop_enable_state:
            just_enabled = True
        prop_enable_state = True

        # Ramp up throttle gradually
        if current_throttle < smoothed_throttle_val:
            current_throttle = min(current_throttle + ramp_up_speed, smoothed_throttle_val)
        else:
            current_throttle = smoothed_throttle_val

        if just_enabled:
            set_tacho_angle(20)
            prev_tacho_angle = 20
            just_enabled = False

    else:
        prop_enable_state = False
        # Ramp down throttle
        current_throttle = max(current_throttle - ramp_down_speed, 0.0)

    # Compute normalized value for output logic
    clamped_value = clamp(current_throttle, throttle_min, throttle_max)
    normalized = (clamped_value - throttle_min) / (throttle_max - throttle_min)
    normalized = clamp(normalized, 0.0, 1.0)

    # --- Servo logic ---
    # Tacho
    tacho_angle = compute_smoothed_angle(
        current_throttle, prev_tacho_angle, throttle_min, throttle_max,
        angle_smoothing_factor, invert=False
    )
    if prev_tacho_angle is None or abs(tacho_angle - prev_tacho_angle) > angle_change_threshold:
        set_tacho_angle(tacho_angle + 30)
        prev_tacho_angle = tacho_angle

    # Anemometer
    raw_anem_angle = 180 - (normalized * 50)  # 180 to 130
    anem_angle = angle_smoothing_factor * prev_anem_angle + (1 - angle_smoothing_factor) * raw_anem_angle if prev_anem_angle is not None else raw_anem_angle
    if prev_anem_angle is None or abs(anem_angle - prev_anem_angle) > angle_change_threshold:
        set_anemometre_angle(anem_angle)
        prev_anem_angle = anem_angle

    # Pulse delay out (to UART1)
    pulse_delay = int(max_pulsedelay - (normalized * min_pulsedelay))
    uart1.write(struct.pack("<H", pulse_delay))

    # --- Prop TX Logic ---
    prop_enable_tx.value(True)  # Keep ON during ramp down

    if not prop_enable_state and current_throttle <= 0.01:
        # Fully off – now disable visuals and TX
        set_anemometre_angle(180)
        set_tacho_angle(0)
        prop_enable_tx.value(False)

    sleep(sleep_time)

