import serial
import time
import json
import config as cfg

ser = serial.Serial(cfg.SERIAL_PIN, cfg.BAUDRATE)
ser.flush()

while True:
	line = ser.readline().decode('utf-8').rstrip()
	try:
		data = json.loads(line)
	except:
		continue
	valve = data['valve']
	throttle = data['throttle']
	photoresistor = data['photoresistor']
	print(json.dumps(data))
	time.sleep(0.1)
