#!/usr/bin/env python3

import subprocess
import time

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306


def get_ip():
    try:
        output = subprocess.check_output(
            ["hostname", "-I"],
            text=True
        ).strip()

        for ip in output.split():
            if ip.startswith(("192.", "10.", "172.")):
                return ip

        return output.split()[0] if output else "NO IP"

    except Exception:
        return "IP ERROR"


serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, rotate=0)

ip = get_ip()

with canvas(device) as draw:
    draw.text((0, 0),  "ROCKINGMAN", fill="white")
    draw.text((0, 10), "PiCar-Pro V2", fill="white")
    draw.text((0, 20), "STATUS: ONLINE", fill="white")
    draw.text((0, 30), "Raspberry Pi 5", fill="white")
    draw.text((0, 40), f"IP:{ip}", fill="white")
    draw.text((0, 50), "Robot Ready :)", fill="white")

print("OLED test displayed successfully.")

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    device.clear()
    print("\nOLED cleared.")
