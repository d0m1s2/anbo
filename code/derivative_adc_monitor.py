from ADS1x15 import ADS1115
import time

class ADS1115Monitor:
    def __init__(self, derivative_threshold=1000, i2c_bus=1, address=0x48):
        self.adc = ADS1115(busId=i2c_bus, address=address)
        self.adc.setGain(self.adc.PGA_2_048V)
        self.adc.setMode(self.adc.MODE_SINGLE)

        self.derivative_threshold = derivative_threshold
        self.channels = [0, 1, 2]
        self.channel_map = [1, 2, 0]

        now = time.time()
        self.last_values = [self.adc.readADC(ch) for ch in self.channels]
        self.last_times = [now for _ in self.channels]

        print("Initial values:", [f"Ch{i}: {v}" for i, v in enumerate(self.last_values)])

    def read_all(self):
        return [self.adc.readADC(ch) for ch in self.channels]

    def get_triggered_channel(self):
        current_time = time.time()
        current_values = self.read_all()

        for i, (curr_val, last_val, last_time) in enumerate(zip(current_values, self.last_values, self.last_times)):
            dt = current_time - last_time
            if dt == 0:
                continue  # avoid division by zero
            derivative = abs((curr_val - last_val) / dt)

            if derivative > self.derivative_threshold:
                # Update stored values after triggering
                self.last_values[i] = curr_val
                self.last_times[i] = current_time
                return self.channel_map[i]

            # Update values if not triggered
            self.last_values[i] = curr_val
            self.last_times[i] = current_time

        return None

# Example usage
if __name__ == "__main__":
    monitor = ADS1115Monitor(derivative_threshold=1000)  # Adjust as needed
    try:
        while True:
            ch = monitor.get_triggered_channel()
            if ch is not None:
                print(f"Channel {ch} triggered due to high rate of change!")
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("Stopped.")
