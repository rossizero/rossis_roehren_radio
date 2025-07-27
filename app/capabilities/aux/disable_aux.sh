#!/bin/bash

# This script finds and stops the audio passthrough processes.

echo "Stopping audio passthrough..."

# Use pkill to send a termination signal to any process named 'arecord'
pkill arecord

# Also kill the aplay process
pkill aplay

echo "Passthrough stopped."