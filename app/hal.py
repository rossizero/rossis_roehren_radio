import gpiod
import time
from gpiod.line import Direction, Bias, Value, Edge
from gpiod import LineSettings

CHIP_NAME = "/dev/gpiochip0"
chip = gpiod.Chip(CHIP_NAME)

settings = LineSettings(
    direction=Direction.INPUT,
    bias=Bias.PULL_UP,
    edge_detection=Edge.FALLING
    )

line = gpiod.request_lines(
    path=CHIP_NAME,
    consumer="hal",
    config={2: settings, 3: settings}
)
print("Warte auf Magnet... (CTRL+C zum Beenden)")

try:
    while True:
        event = line.read_edge_events()
        print(event[0].line_offset)
except KeyboardInterrupt:
    print("Beendet.")

finally:
    line.release()
    chip.close()
