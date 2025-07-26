import time
import signal
from volume import VolumeControl
from buttons import ButtonControl
from flywheel import WheelControl

CHIP_NAME = "/dev/gpiochip0"
BUTTON_PINS = [9, 10, 24, 23, 22, 27, 17]
# grün blau lila grau gelb rot orange
FLYWHEEL_PINS = [2, 3]

class MainController:
    def __init__(self):
        """
        Initializes all hardware-controlling sub-components.
        """
        print("Initializing main controller...")
        consumer_name = "Rossis Röhren Radio" 

        self.vc = VolumeControl(control_name="Master") # Assumes this class needs no manual cleanup
        print("Current volume:", self.vc.get_volume())

        self.wc = WheelControl(
            FLYWHEEL_PINS[0], 
            FLYWHEEL_PINS[1], 
            self.rotation_callback, 
            chip_name=CHIP_NAME, 
            consumer=consumer_name
        )
        
        self.bc = ButtonControl(
            BUTTON_PINS, 
            self.button_callback,
            chip_name=CHIP_NAME,
            consumer=consumer_name
        )
        
        self._running = True
        print("Controller initialized.")

    def button_callback(self, pin, state):
        """Callback for button state changes."""
        status = "Released" if state == 1 else "Pressed"
        print(f"Button on GPIO {pin} was {status}")
        
        # Example: A specific button press (e.g., pin 17) stops the application
        if pin == 17 and state == 0: # Assuming pin 17 is the 'exit' button
            print("Exit button pressed. Shutting down...")
            self.stop()

    def rotation_callback(self, direction, speed_kmh):
        """Callback for wheel rotation events."""
        print(f"Wheel rotation in '{direction}' with speed: {speed_kmh:.2f} km/h")
        self.vc.change_volume(5 * direction)
        print(self.vc.get_volume())

    def stop(self):
        """
        A dedicated method to stop the main loop and trigger cleanup.
        This is much better than relying on __del__.
        """
        print("Stopping main loop...")
        self._running = False

    def cleanup(self):
        """
        A dedicated method to release all hardware resources.
        This is our reliable "destructor".
        """
        print("Cleaning up resources...")
        self.wc.stop()  # This stops its internal thread and releases GPIO
        self.bc.close() # This stops its thread and releases GPIO
        print("Cleanup complete.")

    def run(self):
        """
        The main execution loop for the application.
        This method will block until the application is told to stop.
        """
        print("Starting main controller execution...")
        self.wc.start() # Start monitoring the wheel
        self.bc.start_monitoring() # Start monitoring the buttons
        
        while self._running:
            time.sleep(0.5)


if __name__ == "__main__":
    controller = None
    try:
        controller = MainController()
        def signal_handler(sig, frame):
            print(f"\nCaught signal {sig}. Initiating shutdown...")
            if controller:
                controller.stop()

        # Register the signal handler for graceful shutdown on Ctrl+C (SIGINT)
        # and on `kill` (SIGTERM)
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        controller.run()

    except Exception as e:
        print(f"\nAn unhandled error occurred in the main application: {e}")
    
    finally:
        if controller:
            controller.cleanup()
        print("Application has been shut down.")