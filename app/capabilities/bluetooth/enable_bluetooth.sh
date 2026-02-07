#!/bin/bash
SCRIPT_DIR=$(dirname "$0")
ffplay "$SCRIPT_DIR/bluetooth.mp3" -autoexit -nodisp  > /dev/null 2>&1 &

bluetoothctl << EOF
system-alias "Rossis Röhren Radio"
power on
discoverable-timeout 300
discoverable on
pairable on
EOF

sudo bt-agent -c DisplayYesNo -p $(dirname $0)/pins.txt > /dev/null 2>&1 &


