import os
from pathlib import Path
from playsound import playsound
import subprocess
import time
import signal
from volume import VolumeControl
from buttons import ButtonControl
from flywheel import WheelControl
import math

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

FLYWHEEL_PINS = [7, 8]  # change order to reverse the effect

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
            consumer=consumer_name,
            distance_m=0.08
        )
        
        self.bc = ButtonControl(
            BUTTON_CONFIG.keys(), 
            self.button_callback,
            chip_name=CHIP_NAME,
            consumer=consumer_name
        )
        
        self._running = True
        self.current_mode = 9
        self.volume_speed = math.pi / 2.0
        self.max_volume_step = 13.13
        print("Controller initialized.")

    def button_callback(self, pin, state):
        """Callback for button state changes."""
        print(state, pin, BUTTON_CONFIG[pin])
        if state == 0:
            self._disable_all_capabilities(exception=[pin])  # to be safe
            time.sleep(1)
            self._enable_capability(pin)
        else:
            self._disable_all_capabilities()

    def rotation_callback(self, direction, speed_kmh):
        """Callback for wheel rotation events."""
        change = self.volume_speed * direction * speed_kmh
        change =  max(-self.max_volume_step, min(change, self.max_volume_step))
        print(f"Wheel rotation in '{direction}' with speed: {speed_kmh:.2f} km/h and changing volume {change}")
        self.vc.change_volume(int(change))
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
        self._disable_all_capabilities()
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

    def _disable_all_capabilities(self, exception=[]):
        for pin in BUTTON_CONFIG.keys():
           if pin not in exception:
            self._disable_capability(pin)
            
    def _enable_capability(self, pin):
        self._run_script(self._get_capabiliy_path(pin, "enable"))

    def _disable_capability(self, pin):
        self._run_script(self._get_capabiliy_path(pin, "disable"))

    def play_intro(self):
        file = Path(__file__).resolve().parent
        sound_path = Path(os.path.join(file, "..", "misc", "play_radio_intro.sh"))
        print(sound_path)
        if sound_path.exists():
            print("playing")
            subprocess.run(['/bin/bash', sound_path.resolve()], capture_output=True, text=True)

if __name__ == "__main__":
    controller = None
    try:
        controller = MainController()
        controller._disable_all_capabilities()
        def signal_handler(sig, frame):
            print(f"\nCaught signal {sig}. Initiating shutdown...")
            if controller:
                controller.stop()

        # Register the signal handler for graceful shutdown on Ctrl+C (SIGINT)
        # and on `kill` (SIGTERM)
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        controller.play_intro()
        controller.run()

    except Exception as e:
        print(f"\nAn unhandled error occurred in the main application: {e}")
    
    finally:
        if controller:
            controller.cleanup()
        print("Application has been shut down.")