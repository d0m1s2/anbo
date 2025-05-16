from ADS1x15 import ADS1115
import time

class ADS1115Monitor:
    def __init__(self, tolerance=18, debounce_time=0.15, i2c_bus=1, address=0x48):
        self.adc = ADS1115(busId=i2c_bus, address=address)
        self.adc.setGain(self.adc.PGA_2_048V)
        self.adc.setMode(self.adc.MODE_SINGLE)

        self.tolerance = tolerance
        self.debounce_time = debounce_time
        self.channels = [0, 1, 2]
        self.expected = [self.adc.readADC(ch) for ch in self.channels]
        self.deviation_start = [None for _ in self.channels]

        print("Baseline values:", [f"Ch{i}: {v}" for i, v in enumerate(self.expected)])

    def read_all(self):
        return [self.adc.readADC(ch) for ch in self.channels]

    def get_triggered_channel(self):
        readings = self.read_all()
        now = time.time()

        for i, (reading, expect) in enumerate(zip(readings, self.expected)):
            if abs(reading - expect) > self.tolerance:
                if self.deviation_start[i] is None:
                    self.deviation_start[i] = now
                elif now - self.deviation_start[i] >= self.debounce_time:
                    self.deviation_start[i] = None
                    return i
            else:
                self.deviation_start[i] = None
        return None

    def update_expected(self):
        self.expected = self.read_all()
        print("Updated baseline values:", self.expected)

# Example usage
if __name__ == "__main__":
    monitor = ADS1115Monitor()
    try:
        while True:
            ch = monitor.get_triggered_channel()
            if ch is not None:
                print(f"Channel {ch} deviated!")
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("Stopped.")
