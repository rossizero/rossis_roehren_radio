SCRIPT_DIR=$(dirname "$0")
ffplay "$SCRIPT_DIR/spotify.mp3" -autoexit -nodisp  > /dev/null 2>&1 &
sudo systemctl start raspotify