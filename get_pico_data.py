# serial_reader.py
import serial
import time
import json
import threading
import config as cfg

class SensorReader(threading.Thread):
    def __init__(self):
        super().__init__()
        self.ser = serial.Serial(cfg.SERIAL_PIN, cfg.BAUDRATE)
        self.ser.flush()
        self.running = True
        self.latest_data = {}

    def run(self):
        while self.running:
            line = self.ser.readline().decode('utf-8').rstrip()
            try:
                data = json.loads(line)
                self.latest_data = data
            except:
                continue
            time.sleep(0.1)

    def stop(self):
        self.running = False
        self.ser.close()

    def get_data(self):
        return self.latest_data
