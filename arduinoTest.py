import serial

# Set up serial connection
ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate=9600,
    timeout=1  # 1 second timeout
)

print("Listening on /dev/ttyUSB1 at 9600 baud...")

try:
    while True:
        if ser.in_waiting > 0:
            data = ser.readline().decode('utf-8', errors='replace').strip()
            print(f"Received: {data}")

except KeyboardInterrupt:
    print("Stopped by user")

finally:
    ser.close()
