#!/bin/bash
# radio-off - Mutes the radio module and stops the audio bridge.
SCRIPT_DIR=$(dirname "$0")
ffplay "$SCRIPT_DIR/radio.mp3" -autoexit -nodisp  > /dev/null 2>&1 &

PID_FILE="/tmp/radio.pid"

echo "Turning radio module off (mute)..."
python3 /home/pi/radio.py off

if [ -f "$PID_FILE" ]; then
    echo "Stopping audio bridge process..."
    # Kill the process using the saved PID
    sudo kill $(cat $PID_FILE) > /dev/null 2>&1
    # Clean up the PID file
    rm -f $PID_FILE
else
    echo "No active radio process found."
fi

echo "Radio is OFF."