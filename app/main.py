import gpiod
from gpiod.line import Direction, Value, Bias
from gpiod import LineSettings
import time

CHIP_NAME = "/dev/gpiochip0"
chip = gpiod.Chip(CHIP_NAME)

gpio_pins = [9, 10, 24, 23, 22, 27, 17]
# grün blau lila grau gelb rot orange

settings = LineSettings(
    direction=Direction.INPUT,
    bias=Bias.PULL_UP
    )

config = {pin: settings for pin in gpio_pins}

lines = gpiod.request_lines(
    CHIP_NAME,
    consumer="rossis-roehren-radio",
    config=config
)

try:
    while True:
        print(lines.get_values(gpio_pins))
        time.sleep(0.1)

except KeyboardInterrupt:
    lines.release()
    print("GPIO cleaned up")
