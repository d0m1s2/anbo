from ADS1x15 import ADS1115  # Save your class code as ADS1x15.py
import time
import os
import sys

# Initialize ADS1115 on I2C bus 1
adc = ADS1115(busId=1)

# Set gain to ±4.096V (PGA_4_096V), you can adjust if needed
adc.setGain(adc.PGA_4_096V)

# Use single-shot mode for consistent readings
adc.setMode(adc.MODE_SINGLE)

def clear_console():
    # Works on Linux/macOS/Windows terminals
    os.system('clear' if os.name == 'posix' else 'cls')

try:
    while True:
        clear_console()
        print("📟 ADS1115 Voltage Readings")
        print("=" * 32)
        for channel in range(3):
            raw = adc.readADC(channel)
            volts = adc.toVoltage(raw)
            print(f"Channel {channel}: {volts:>7.4f} V | Raw: {raw:>6}")
        print("=" * 32)
        print("Press Ctrl+C to stop.")
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nStopped.")
