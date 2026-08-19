#!/usr/bin/env python3

import time
from PIL import ImageFont
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306

TEXT = "I L o v e Y o u M a c h c h h a r"
DELAY = 0.50

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, rotate=0)

font = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    54
)

print("ROCKINGMAN3010 OLED animation started")
print("Ctrl+C to stop")

try:
    while True:
        for char in TEXT:

            with canvas(device) as draw:

                # Measure character
                bbox = draw.textbbox((0, 0), char, font=font)

                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]

                # Center character on 128x64 OLED
                x = (device.width - width) // 2
                y = (device.height - height) // 2 - bbox[1]

                draw.text(
                    (x, y),
                    char,
                    font=font,
                    fill="white"
                )

            time.sleep(DELAY)

        # Small pause after full name
        device.clear()
        time.sleep(1)

except KeyboardInterrupt:
    device.clear()
    print("\nOLED cleared.")
