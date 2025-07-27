# KI - wird schon tun was es soll

import gpiod
from gpiod.line import Direction, Bias, Value
import threading
import time

class ButtonControl:
    """
    A class to monitor multiple GPIO buttons using gpiod and trigger a 
    callback function on state changes.

    This class runs a monitoring loop in a separate thread. It is best used
    as a context manager (`with` statement) to ensure proper cleanup of GPIO
    resources and the background thread.
    """
    
    def __init__(self, pins, callback, chip_name="/dev/gpiochip0", consumer="ButtonControl"):
        """
        Initializes the button controller.

        Args:
            pins (list[int]): A list of GPIO pin numbers (BCM numbering) to monitor.
            callback (function): A function to call when a button state changes.
                                 The callback will be called with two arguments:
                                 callback(pin: int, new_state: int)
                                 - pin: The pin number that changed.
                                 - new_state: 0 for pressed (LOW), 1 for released (HIGH).
            chip_name (str): The name of the GPIO chip device.
            consumer (str): A name for the consumer of the GPIO lines.
        """
        if not callable(callback):
            raise TypeError("The provided callback must be a callable function.")
        
        self.pins = pins
        self.callback = callback
        self.chip_name = chip_name
        self.consumer = consumer
        
        self.lines = None
        self._monitor_thread = None
        self._running = False
        
        # Initialize GPIO lines
        self._setup_gpio()

    def _setup_gpio(self):
        """Configures and requests the GPIO lines from the system."""
        try:
            # Define the settings for all input pins
            # PULL_UP means the pin is HIGH (1) by default and goes LOW (0) when pressed.
            settings = gpiod.LineSettings(
                direction=Direction.INPUT,
                bias=Bias.PULL_UP
            )
            config = {pin: settings for pin in self.pins}
            
            # Request the lines from the GPIO chip
            self.lines = gpiod.request_lines(
                self.chip_name,
                consumer=self.consumer,
                config=config
            )
            print(f"Successfully requested GPIO pins: {self.pins}")
        except Exception as e:
            print(f"Error setting up GPIO: {e}")
            raise

    def start_monitoring(self):
        """Starts the background thread that monitors for button presses."""
        if self._running:
            print("Monitoring is already active.")
            return
        
        # default start, so we get if a button is already pressed before start of the pi
        self.last_states = [Value.ACTIVE for _ in self.pins]
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        print("Button monitoring started.")

    def stop_monitoring(self):
        """Stops the background monitoring thread."""
        if not self._running:
            return
            
        self._running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join() # Wait for the thread to finish
        print("Button monitoring stopped.")

    def _monitor_loop(self):
        """The core loop that runs in a thread to check for state changes."""
        while self._running:
            current_states = self.lines.get_values()
            
            for i, pin in enumerate(self.pins):
                last_state = self.last_states[i]
                current_state = current_states[i]
                
                if current_state != last_state:
                    # State has changed, trigger the callback
                    try:
                        self.callback(pin, 1 if current_state is Value.ACTIVE else 0)
                    except Exception as e:
                        print(f"Error in user callback for pin {pin}: {e}")
                
            self.last_states = current_states
            time.sleep(0.1) # Poll ~20 times/sec. Adjust as needed.

    def close(self):
        """Stops monitoring and releases GPIO resources."""
        self.stop_monitoring()
        if self.lines:
            self.lines.release()
            self.lines = None
            print("GPIO lines released.")
            
    # --- Context Manager Support ---
    def __enter__(self):
        """Enter the runtime context and start monitoring."""
        self.start_monitoring()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context and clean up resources."""
        self.close()

# --- Example Usage ---
if __name__ == "__main__":
    # Define which GPIO pins your buttons are connected to
    BUTTON_PINS = [9, 10, 24, 23, 22, 27, 17]
    
    # Define your callback function
    def handle_button_press(pin, state):
        """This function is called whenever a button's state changes."""
        status = "Released" if state == 1 else "Pressed"
        print(f"Button on GPIO {pin} was {status}")

        # You can add specific logic here, e.g.:
        # if pin == 9 and state == 0: # Pin 9 was pressed
        #     print("-> Green button action!")
        # elif pin == 10 and state == 0: # Pin 10 was pressed
        #     print("-> Blue button action!")

    print("Starting button control demo. Press buttons to see events.")
    print("Press Ctrl+C to exit.")

    try:
        # Use the class as a context manager (recommended)
        with ButtonControl(pins=BUTTON_PINS, callback=handle_button_press):
            # The main program can do other things here, or just wait.
            # The button monitoring happens in the background.
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Cleanup complete. Exiting.")

# gpioinfo /dev/gpiochip0