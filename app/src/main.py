import os
from pathlib import Path
import subprocess
import time
import signal
from volume import VolumeControl
from buttons import ButtonControl
from flywheel import WheelControl

CHIP_NAME = "/dev/gpiochip0"

BUTTON_CONFIG = {
    9: "all",           # grün
    10: "spotifyd",     # blau
    24: "bluetooth",    # lila
    23: "cd",           # grau
    22: "aux",          # gelb
    27: "radio",        # rot
    17: "empty",        # orange
}

FLYWHEEL_PINS = [8, 7]

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
            BUTTON_CONFIG.keys(), 
            self.button_callback,
            chip_name=CHIP_NAME,
            consumer=consumer_name
        )
        
        self._running = True
        self.current_mode = 9
        print("Controller initialized.")

    def button_callback(self, pin, state):
        """Callback for button state changes."""
        self._disable_all_capabilities()
        if state == 0:
            self._enable_capability(pin)
        print(state, pin)

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
        # self._disable_all_capabilities() TODO
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
    
    def _get_capabiliy_path(self, pin, mode="disable"):
        val = BUTTON_CONFIG[pin]
        file = Path(__file__).resolve().parent
        script_path = Path(os.path.join(file, "..", "capabilities", val, f"{mode}_{val}.sh"))
        if script_path.exists():
            print("requested path: ", script_path)
            return script_path.resolve()
        return None
    
    def _run_script(self, script_path):
        if script_path is not None:
            result = subprocess.run(['/bin/bash', script_path.resolve()], capture_output=True, text=True)
            return result
        return None

    def _disable_all_capabilities(self):
        for pin in BUTTON_CONFIG.keys():
           self._disable_capability(pin)
            
    def _enable_capability(self, pin):
        self._run_script(self._get_capabiliy_path(pin, "enable"))

    def _disable_capability(self, pin):
        self._run_script(self._get_capabiliy_path(pin, "disable"))


if __name__ == "__main__":
    controller = None
    try:
        controller = MainController()
        controller._disable_all_capabilities()
        controller._enable_capability(10)
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