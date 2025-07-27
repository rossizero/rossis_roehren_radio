#!/bin/bash
# radio-on - Tunes the radio and routes its audio through the Pi's sound system.

# The hardware identifier for your USB sound card's input. Find with 'arecord -l'.
USB_DEVICE="hw:1,0" 
DEFAULT_FREQ=98.5
PID_FILE="/tmp/radio.pid"

# Stop any existing radio process first
if [ -f "$PID_FILE" ]; then
    sudo kill $(cat $PID_FILE) > /dev/null 2>&1
    rm -f $PID_FILE
fi

# Determine frequency
if [ -z "$1" ]; then
    FREQ=$DEFAULT_FREQ
else
    FREQ=$1
fi

echo "Tuning radio to ${FREQ} MHz..."
python3 /home/pi/radio.py $FREQ

echo "Starting audio bridge from USB input to default output..."
# Start the audio bridge in the background
arecord -D $USB_DEVICE -f S16_LE -r 44100 -c 2 | aplay > /dev/null 2>&1 &

# Save the Process ID of the last background command (the arecord pipe)
echo $! > $PID_FILE

echo "Radio is ON."