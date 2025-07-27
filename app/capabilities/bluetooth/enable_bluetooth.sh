#!/bin/bash

bluetoothctl << EOF
system-alias "Rossis Röhren Radio"
power on
discoverable-timeout 300
discoverable on
pairable on
EOF

sudo bt-agent -c DisplayYesNo -p $(dirname $0)/pins.txt > /dev/null 2>&1 &


