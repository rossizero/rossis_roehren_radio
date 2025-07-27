# https://github.com/codazoda/hub-ctrl.c
# sudo apt install uhubctl

# sudo apt install vlc, netcat
# ls /dev/sr*
# cvlc cdda:///dev/sr0
# cvlc --intf rc --rc-unix /tmp/vlc.sock cdda:///dev/sr0  # geht dann in ne console, vlt nicht richtiger command
# echo "next" | nc -U /tmp/vlc.sock