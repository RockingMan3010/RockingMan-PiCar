#!/usr/bin/env python3

import sys
import time
from pathlib import Path

if len(sys.argv) != 2:
    print("Usage: python3 car/servo_probe.py <channel>")
    print("Example: python3 car/servo_probe.py 1")
    raise SystemExit(2)

channel = int(sys.argv[1])

if channel not in (1, 2, 3, 4):
    raise SystemExit("Only channels 1, 2, 3, 4 are allowed.")

ADEEPT_SERVER = Path.home() / "Adeept_PiCar-Pro" / "Server"
sys.path.insert(0, str(ADEEPT_SERVER))

import RPIservo

servo = RPIservo.ServoCtrl()

try:
    print(f"CH{channel}: NEUTRAL")
    servo.moveAngle(channel, 0)
    time.sleep(3)

    print(f"CH{channel}: -5")
    servo.moveAngle(channel, -5)
    time.sleep(3)

    print(f"CH{channel}: NEUTRAL")
    servo.moveAngle(channel, 0)
    time.sleep(2)

    print(f"CH{channel}: +5")
    servo.moveAngle(channel, 5)
    time.sleep(3)

finally:
    print(f"CH{channel}: RETURNING TO NEUTRAL")
    servo.moveAngle(channel, 0)

print("DONE")
