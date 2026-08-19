#!/usr/bin/env python3

import sys
import time
from pathlib import Path

ADEEPT_SERVER = Path.home() / "Adeept_PiCar-Pro" / "Server"

if not ADEEPT_SERVER.is_dir():
    raise RuntimeError(
        f"Adeept Server directory not found: {ADEEPT_SERVER}"
    )

sys.path.insert(0, str(ADEEPT_SERVER))

import RPIservo

ARM = 2
HAND = 3

servo = RPIservo.ServoCtrl()

def move(joint, angle, pause=0.5):
    print(f"Servo {joint} -> {angle:+} deg")
    servo.moveAngle(joint, angle)
    time.sleep(pause)

try:
    print("Small shutdown-emote test")

    # Tiny movements only
    move(ARM, -5)
    move(ARM, 0)

    move(HAND, 5)
    move(HAND, -5)
    move(HAND, 0)

    print("Test complete")

except KeyboardInterrupt:
    print("Stopped")

finally:
    servo.moveAngle(ARM, 0)
    servo.moveAngle(HAND, 0)
