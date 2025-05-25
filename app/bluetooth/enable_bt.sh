#!/bin/bash

bluetoothctl << EOF
system-alias "Rossis Röhren Radio"
power on
discoverable on
pairable on
discoverable-timeout 300
EOF

sudo bt-agent -c DisplayYesNo -p $(dirname $0)/pins.txt

