import smbus
import time

# Get I2C bus
bus = smbus.SMBus(1)

# Full-scale range of ±2.048V = 4.096V span, 16-bit ADC = 32768 LSB
FSR = 2.048  # Full-scale range in volts

# Allowed deviation threshold in ADC counts
TOLERANCE = 20

# Debounce duration in seconds
DEBOUNCE_TIME = 0.2  # 200 milliseconds

def read_channel(config_high):
    config = [config_high, 0x83]  # Continuous mode, 128SPS
    bus.write_i2c_block_data(0x48, 0x01, config)
    time.sleep(0.001)

    data = bus.read_i2c_block_data(0x48, 0x00, 2)
    raw_adc = data[0] * 256 + data[1]
    if raw_adc > 32767:
        raw_adc -= 65536

    return raw_adc

# Capture baseline values
print("Reading baseline values...")
expected = [
    read_channel(0xC4),  # Channel 0
    read_channel(0xD4),  # Channel 1
    read_channel(0xE4)   # Channel 2
]
print(f"Baseline - Ch0: {expected[0]}, Ch1: {expected[1]}, Ch2: {expected[2]}")
time.sleep(0.5)

# Last time deviation started (None = no current deviation)
deviation_start = [None, None, None]

try:
    while True:
        readings = [
            read_channel(0xC4),
            read_channel(0xD4),
            read_channel(0xE4)
        ]

        current_time = time.time()

        for i in range(3):  # Loop through channels 0–2
            if abs(readings[i] - expected[i]) > TOLERANCE:
                # If deviation just started, mark the time
                if deviation_start[i] is None:
                    deviation_start[i] = current_time
                # If deviation has persisted long enough, print and reset timer
                elif current_time - deviation_start[i] >= DEBOUNCE_TIME:
                    print(f"Channel {i} - Raw: {readings[i]} (Expected: {expected[i]})")
                    deviation_start[i] = None  # Prevent repeated printing
            else:
                # Value returned to normal, reset timer
                deviation_start[i] = None

        time.sleep(0.0001)  # 10 ms sampling interval

except KeyboardInterrupt:
    print("\nExiting loop. Goodbye!")
