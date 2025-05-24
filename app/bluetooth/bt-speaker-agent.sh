#!/bin/bash

bluetoothctl << EOF
power on
agent NoInputNoOutput
default-agent
discoverable on
pairable on
discoverable-timeout 0
pairable-timeout 0
EOF
