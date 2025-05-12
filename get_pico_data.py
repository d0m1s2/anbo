import serial
import time
import json
import threading
import config as cfg

class SensorReader(threading.Thread):
    def __init__(self):
        super().__init__()
        self.ser = serial.Serial(cfg.SERIAL_PIN, cfg.BAUDRATE, timeout=1)
        self.lock = threading.Lock()
        self.running = True
        self.latest_data = {}

    def run(self):
        while self.running:
            try:
                if self.ser.in_waiting:
                    
                    line = self.ser.readline().decode('utf-8', errors='replace').strip()
                    if line:
                        data = json.loads(line)
                        with self.lock:
                            self.latest_data = data
            except json.JSONDecodeError:
                continue
            except serial.SerialException as e:
                print(f"[ERROR] Serial exception: {e}")
                break
            except Exception as e:
                print(f"[ERROR] Unexpected pico exception: {e}")
                with open("error_log.txt", "a") as f:
                    import traceback
                    f.write(traceback.format_exc())
            time.sleep(0.01)  # Tiny sleep to yield CPU


    def stop(self):
        self.running = False
        if self.ser.is_open:
            self.ser.cancel_read()  # Try to abort blocking read, if supported
            self.ser.close()
        self.join(timeout=0.5)


    def get_data(self):
        with self.lock:
            return self.latest_data.copy()
