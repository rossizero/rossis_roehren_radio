SCRIPT_DIR=$(dirname "$0")
ffplay "$SCRIPT_DIR/aux.mp3" -autoexit -nodisp  > /dev/null 2>&1 &
(arecord -f cd -D plughw:3,0 | aplay -D plughw:2,0) > /dev/null 2>&1 &