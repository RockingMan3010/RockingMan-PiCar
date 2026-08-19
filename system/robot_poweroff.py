#!/usr/bin/env python3

import sys
import time
import subprocess
from pathlib import Path

# ---------------------------------------------------------
# Adeept modules
# ---------------------------------------------------------

SERVER = Path.home() / "Adeept_PiCar-Pro" / "Server"

if not SERVER.is_dir():
    raise RuntimeError(
        f"Adeept Server directory not found: {SERVER}"
    )

sys.path.insert(0, str(SERVER))

import RPIservo
import Move as move

# ---------------------------------------------------------
# OLED
# ---------------------------------------------------------

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306


ARM = 2
HAND = 3

OLED_ADDRESS = 0x3C


def run(command):
    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False
    )


def centered(draw, text, y):
    bbox = draw.textbbox((0, 0), text)
    width = bbox[2] - bbox[0]
    x = (128 - width) // 2
    draw.text((x, y), text, fill="white")


def stop_service(name):
    result = subprocess.run(
        ["systemctl", "is-active", "--quiet", name]
    )

    if result.returncode == 0:
        print(f"Stopping {name}")
        run(["systemctl", "stop", name])


def sweep(servo, servo_id, start, end, delay=0.025):
    step = 1 if end >= start else -1

    for angle in range(start, end + step, step):
        servo.moveAngle(servo_id, angle)
        time.sleep(delay)


print("RockingMan shutdown sequence started.")

# ---------------------------------------------------------
# 1. Stop OLED daemon so this script gets exclusive display
# ---------------------------------------------------------

stop_service("robot-oled.service")

serial = i2c(port=1, address=OLED_ADDRESS)
oled = ssd1306(serial, rotate=0)

with canvas(oled) as draw:
    centered(draw, "ROCKINGMAN3010", 5)
    centered(draw, "GOODBYE :)", 24)
    centered(draw, "POWERING OFF...", 44)

# ---------------------------------------------------------
# 2. Stop motors immediately
# ---------------------------------------------------------

try:
    move.setup()
    move.motorStop()
except Exception as exc:
    print("Motor stop warning:", exc)

# ---------------------------------------------------------
# 3. Stop non-essential services
# ---------------------------------------------------------

services = [
    "Adeept_Robot.service",
    "xrdp.service",
    "xrdp-sesman.service",
    "lightdm.service",
    "bluetooth.service",
    "avahi-daemon.service",
    "cups.service",
    "cups-browsed.service",
    "ModemManager.service",
    "tailscaled.service",
]

for service in services:
    stop_service(service)

# ---------------------------------------------------------
# 4. Goodbye arm emote
# ---------------------------------------------------------

servo = RPIservo.ServoCtrl()

try:
    # Small arm lift
    sweep(servo, ARM, 0, -10)
    time.sleep(0.20)

    # Wrist wave
    current = 0

    for target in (14, -14, 14, -14, 0):
        sweep(
            servo,
            HAND,
            current,
            target,
            delay=0.020
        )
        current = target
        time.sleep(0.12)

    # Small bow/nod
    sweep(servo, ARM, -10, -5)
    time.sleep(0.25)
    sweep(servo, ARM, -5, -10)
    time.sleep(0.25)

    # Return home
    sweep(servo, ARM, -10, 0)

finally:
    servo.moveAngle(HAND, 0)
    servo.moveAngle(ARM, 0)

# ---------------------------------------------------------
# 5. Final OLED message
# ---------------------------------------------------------

with canvas(oled) as draw:
    centered(draw, "GOOD NIGHT", 13)
    centered(draw, "ROCKINGMAN3010", 31)

time.sleep(1.5)

# ---------------------------------------------------------
# 6. Flush disk writes
# ---------------------------------------------------------

run(["sync"])

# ---------------------------------------------------------
# 7. Actual shutdown
# ---------------------------------------------------------

print("Powering off now.")

run(["systemctl", "poweroff"])
