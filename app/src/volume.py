# KI

import subprocess
import re

class VolumeControl:
    """
    A class to control the system volume on a Raspberry Pi (or any Linux system
    using ALSA) by calling the 'amixer' command-line tool.
    """
    def __init__(self, control_name='Master'):
        """
        Initializes the VolumeControl object.

        Args:
            control_name (str): The name of the ALSA mixer control to use.
                                Common names are 'Master', 'PCM', 'Headphone',
                                or 'Speaker'. You can find available control
                                names by running `amixer scontrols` in the terminal.
        """
        self.control_name = control_name
        # Verify that amixer is installed and the control exists
        try:
            subprocess.run(['amixer', 'sget', self.control_name], 
                           check=True, 
                           capture_output=True)
        except FileNotFoundError:
            raise RuntimeError("The 'amixer' command was not found. Please ensure ALSA utils are installed ('sudo apt-get install alsa-utils').")
        except subprocess.CalledProcessError:
            raise ValueError(f"The specified mixer control '{self.control_name}' was not found. Check available controls with 'amixer scontrols'.")

    def get_volume(self) -> int:
        """
        Gets the current volume level as a percentage.

        Returns:
            int: The current volume level (0-100).
        """
        try:
            # Run the command to get the control's status
            result = subprocess.run(['amixer', 'sget', self.control_name],
                                    capture_output=True,
                                    text=True,
                                    check=True)
            
            # Use regex to find the percentage value in the output
            # This looks for a string like '[80%]'
            match = re.search(r'\[(\d{1,3})%\]', result.stdout)
            if match:
                return int(match.group(1))
            else:
                raise RuntimeError("Could not parse volume from amixer output.")
        except (subprocess.CalledProcessError, RuntimeError) as e:
            print(f"Error getting volume: {e}")
            return -1 # Return an error value

    def change_volume(self, step: int):
        if step < 0:
            self.decrease_volume(-step)
        else:
            self.increase_volume(step)

    def set_volume(self, level: int):
        """
        Sets the volume to a specific level.

        Args:
            level (int): The desired volume level (0-100).
        """
        if not 0 <= level <= 100:
            raise ValueError("Volume level must be between 0 and 100.")
        
        command = f"amixer sset '{self.control_name}' {level}%"
        self._run_command(command)
        print(f"Volume set to {level}%")

    def increase_volume(self, amount: int):
        """
        Increases the volume by a given percentage amount.

        Args:
            amount (int): The percentage by which to increase the volume.
        """
        if amount < 0:
            raise ValueError("Amount to increase must be positive.")

        command = f"amixer sset '{self.control_name}' {amount}%+"
        self._run_command(command)
        print(f"Volume increased by {amount}%")

    def decrease_volume(self, amount: int):
        """
        Decreases the volume by a given percentage amount.

        Args:
            amount (int): The percentage by which to decrease the volume.
        """
        if amount < 0:
            raise ValueError("Amount to decrease must be positive.")

        command = f"amixer sset '{self.control_name}' {amount}%-"
        self._run_command(command)
        print(f"Volume decreased by {amount}%")

    def _run_command(self, command: str):
        """A helper method to run a shell command."""
        try:
            subprocess.run(command, shell=True, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            # Provide more helpful error info if possible
            print(f"Error executing command: {command}")
            print(f"Stderr: {e.stderr.decode()}")
            raise

    def __repr__(self):
        """Provides a developer-friendly representation of the object."""
        return f"VolumeControl(control_name='{self.control_name}')"

# --- Example Usage ---
if __name__ == "__main__":
    import time

    try:
        # Create an instance of the VolumeControl.
        # It will use the 'Master' control by default.
        # If your control is named 'PCM', you would use:
        # volume = VolumeControl('PCM')
        print("Initializing volume control...")
        volume = VolumeControl()
        print("Initialization successful.")

        # 1. Get and display the current volume
        current_level = volume.get_volume()
        print(f"\nCurrent volume is: {current_level}%")
        time.sleep(1)

        # 2. Set volume to a loud level
        print("\nSetting volume to a loud 90%...")
        volume.set_volume(70)
        print(f"Volume is now: {volume.get_volume()}%")
        time.sleep(2)
        
        # 3. Decrease the volume
        print("\nDecreasing volume by 20%...")
        volume.decrease_volume(20)
        print(f"Volume is now: {volume.get_volume()}%")
        time.sleep(2)

        # 4. Increase the volume
        print("\nIncreasing volume by 5%...")
        volume.increase_volume(5)
        print(f"Volume is now: {volume.get_volume()}%")

    except (ValueError, RuntimeError) as e:
        print(f"\nAn error occurred: {e}")
        print("Please check your audio configuration.")