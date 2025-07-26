import smbus2
import sys
import time

# I2C bus (use 1 for most Raspberry Pi models)
I2C_BUS = 1

# TEA5767 I2C address
TEA5767_ADDR = 0x60

def set_frequency(freq):
    """
    Sets the radio to the given frequency in MHz.
    Example: set_frequency(98.5)
    """
    if not 87.5 <= freq <= 108.0:
        print("Error: Frequency must be between 87.5 and 108.0 MHz.")
        return

    # Formula to calculate frequency setting for TEA5767
    freq_b = int(4 * (freq * 1000000 + 225000) / 32768)
    
    # Split into high and low bytes
    high_byte = freq_b >> 8
    low_byte = freq_b & 0xFF

    # Data to send over I2C bus (5 bytes)
    # MUTE=0, SEARCH_MODE=0
    data = [high_byte, low_byte, 0xB0, 0x10, 0x00]

    try:
        bus = smbus2.SMBus(I2C_BUS)
        bus.write_i2c_block_data(TEA5767_ADDR, 0x00, data)
        print(f"Radio tuned to {freq} MHz.")
        bus.close()
    except Exception as e:
        print(f"Error setting frequency: {e}")
        print("Please check I2C connection and address.")

def turn_off():
    """
    Mutes the radio by setting the mute bit.
    """
    try:
        bus = smbus2.SMBus(I2C_BUS)
        # Re-read the current status to avoid changing frequency
        current_status = bus.read_i2c_block_data(TEA5767_ADDR, 0x00, 5)
        
        # Set the mute bit (bit 7 of the first byte)
        high_byte = current_status[0] | 0x80 # Set MUTE bit
        
        data = [high_byte, current_status[1], current_status[2], current_status[3], current_status[4]]
        
        bus.write_i2c_block_data(TEA5767_ADDR, 0x00, data)
        print("Radio muted (off).")
        bus.close()
    except Exception as e:
        print(f"Error turning off radio: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 radio.py <frequency_in_mhz> | off")
        print("Example: python3 radio.py 102.1")
        print("Example: python3 radio.py off")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'off':
        turn_off()
    else:
        try:
            frequency = float(command)
            set_frequency(frequency)
        except ValueError:
            print("Invalid command. Please provide a frequency in MHz or 'off'.")