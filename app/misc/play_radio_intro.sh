#!/bin/bash

SCRIPT_DIR=$(dirname "$0")
ffplay "$SCRIPT_DIR/radio_intro.mp3" -autoexit -nodisp  > /dev/null 2>&1 &