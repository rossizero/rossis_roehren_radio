# KI - wird schon tun was es soll
 
import gpiod
import threading
import time
from datetime import timedelta
from gpiod.line import Direction, Bias, Edge
from gpiod import LineSettings

class WheelControl:
    """
    A class to monitor a two-sensor rotary encoder (like Hall effect sensors)
    to determine direction of rotation and speed.
    
    It uses gpiod's edge detection and runs in a background thread, triggering a 
    callback function upon detecting a full sequence.
    """
    
    def __init__(self, pin_a, pin_b, callback, distance_m=0.02, timeout_s=2.0, 
                 chip_name="/dev/gpiochip0", consumer="rotary_encoder"):
        """
        Initializes the Rotary Encoder monitor.

        Args:
            pin_a (int): The GPIO pin number for the first sensor (e.g., "left").
            pin_b (int): The GPIO pin number for the second sensor (e.g., "right").
            callback (function): A function to call when a full rotation is detected.
                                 It will be called with: 
                                 callback(direction: str, speed_kmh: float)
                                 - direction: "clockwise" or "counter-clockwise"
                                 - speed_kmh: Calculated speed in km/h.
            distance_m (float): The distance between the two sensors in meters.
            timeout_s (float): Time in seconds to wait for the second sensor before
                               resetting the measurement.
            chip_name (str): The GPIO chip device path.
            consumer (str): A name for the consumer of the GPIO lines.
        """
        if not callable(callback):
            raise TypeError("The provided callback must be a callable function.")
            
        self.pin_a = pin_a
        self.pin_b = pin_b
        self.callback = callback
        self.distance_m = distance_m
        self.timeout_td = timedelta(seconds=timeout_s)
        self.chip_name = chip_name
        self.consumer = consumer
        
        # Internal state
        self.lines = None
        self.chip = None
        self.first_event_pin = None
        self.first_event_time_ns = 0
        
        # Threading control
        self._monitor_thread = None
        self._running = False
        
        self._setup_gpio()

    def _setup_gpio(self):
        """Configures and requests the GPIO lines using gpiod."""
        try:
            self.chip = gpiod.Chip(self.chip_name)
            
            settings = LineSettings(
                direction=Direction.INPUT,
                bias=Bias.PULL_UP,
                edge_detection=Edge.FALLING
            )
            
            self.lines = gpiod.request_lines(
                path=self.chip_name,
                consumer=self.consumer,
                config={
                    self.pin_a: settings,
                    self.pin_b: settings
                }
            )
            print("Encoder GPIO setup successful.")
        except Exception as e:
            print(f"Error setting up GPIO: {e}")
            if self.chip: self.chip.close()
            raise

    def start(self):
        """Starts the background monitoring thread."""
        if self._running:
            print("Monitoring is already active.")
            return
            
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        print("Encoder monitoring started.")

    def stop(self):
        """Stops the monitoring thread and releases GPIO resources."""
        if not self._running:
            return
            
        self._running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            # The thread might be waiting on an edge, but we can just let it exit
            # as the _running flag will be false on the next loop.
            # joining with a small timeout is fine.
            self._monitor_thread.join(timeout=0.1)
            
        if self.lines:
            self.lines.release()
            self.lines = None
        if self.chip:
            self.chip.close()
            self.chip = None
        print("Encoder monitoring stopped and resources released.")

    def _monitor_loop(self):
        """The core loop that runs in a thread to watch for edge events."""
        while self._running:
            # Wait for an edge event with a timeout
            if self.lines.wait_edge_events(self.timeout_td):
                events = self.lines.read_edge_events()
                
                for event in events:
                    current_pin = event.line_offset
                    current_time_ns = event.timestamp_ns
                    
                    # This is the FIRST event in a new measurement
                    if self.first_event_pin is None:
                        self.first_event_pin = current_pin
                        self.first_event_time_ns = current_time_ns
                    
                    # This is the SECOND event from the OTHER sensor
                    elif current_pin != self.first_event_pin:
                        time_delta_ns = current_time_ns - self.first_event_time_ns
                        
                        if time_delta_ns > 0:
                            time_delta_s = time_delta_ns / 1_000_000_000.0
                            speed_mps = self.distance_m / time_delta_s
                            speed_kmh = speed_mps * 3.6

                            direction = "unknown"
                            # Assuming A is "left" and B is "right"
                            if self.first_event_pin == self.pin_a and current_pin == self.pin_b:
                                direction = 1 # Or "forward", "right", etc.
                            elif self.first_event_pin == self.pin_b and current_pin == self.pin_a:
                                direction = -1 # Or "backward", "left", etc.
                            
                            # Trigger the user's callback function
                            try:
                                self.callback(direction, speed_kmh)
                            except Exception as e:
                                print(f"Error in user callback: {e}")
                        
                        # Reset for the next measurement
                        self.first_event_pin = None
            else:
                # wait_edge_events timed out. If we were waiting for a second
                # event, reset the measurement.
                if self.first_event_pin is not None:
                    # print("Measurement timed out, resetting.")
                    self.first_event_pin = None

    # --- Context Manager Support for easy and safe usage ---
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

# --- Example Usage ---
if __name__ == "__main__":
    # Configuration
    SENSOR_A_PIN = 2  # Sensor for "left" or "A"
    SENSOR_B_PIN = 3  # Sensor for "right" or "B"
    SENSOR_DISTANCE_M = 0.02  # 5 cm distance

    # Define the callback function that the class will call
    def handle_rotation(direction, speed_kmh):
        """This function gets called by the RotaryEncoder class."""
        print("-" * 30)
        print(f"Direction Detected: {direction}")
        print(f"Calculated Speed: {speed_kmh:.2f} km/h")
        print("-" * 30)

    print("Starting Rotary Encoder Demo. Move a magnet past the sensors.")
    print("Press Ctrl+C to exit.")

    try:
        # Using the class as a context manager is the recommended way.
        # It automatically handles starting and stopping.
        with WheelControl(SENSOR_A_PIN, SENSOR_B_PIN, handle_rotation, SENSOR_DISTANCE_M):
            # The main thread can now do other things, or just wait.
            # The encoder monitoring happens in the background.
            while True:
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"\nAn unhandled error occurred: {e}")
    finally:
        print("Cleanup complete.")