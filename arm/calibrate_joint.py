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

JOINTS = {
    1: "BASE / LEFT-RIGHT",
    2: "ARM UP-DOWN",
    3: "WRIST / HAND",
    4: "GRIPPER",
}

STEP = 2
SOFT_LIMIT = 70

if len(sys.argv) != 2:
    print("Usage: python3 calibrate_joint.py <servo_id>")
    print("Servo IDs: 1=BASE, 2=ARM, 3=WRIST, 4=GRIPPER")
    raise SystemExit(1)

servo_id = int(sys.argv[1])

if servo_id not in JOINTS:
    raise SystemExit("Servo ID must be 1, 2, 3, or 4.")

servo = RPIservo.ServoCtrl()
angle = 0

print()
print("========================================")
print(f" CALIBRATING SERVO {servo_id}")
print(f" {JOINTS[servo_id]}")
print("========================================")
print()
print("Commands:")
print("  +  = move +2 degrees")
print("  -  = move -2 degrees")
print("  0  = return to center")
print("  p  = print current offset")
print("  q  = center and quit")
print()
print("STOP increasing immediately if:")
print("  - joint reaches mechanical stop")
print("  - servo starts straining/buzzing")
print("  - cable becomes tight")
print()

servo.moveAngle(servo_id, 0)
time.sleep(0.5)

while True:
    command = input(f"[{angle:+d} deg] > ").strip().lower()

    if command == "+":
        new_angle = min(angle + STEP, SOFT_LIMIT)

    elif command == "-":
        new_angle = max(angle - STEP, -SOFT_LIMIT)

    elif command == "0":
        new_angle = 0

    elif command == "p":
        print(f"Current offset: {angle:+d} degrees")
        continue

    elif command == "q":
        print("Returning to center...")
        servo.moveAngle(servo_id, 0)
        time.sleep(0.5)
        break

    else:
        print("Use +, -, 0, p, or q")
        continue

    servo.moveAngle(servo_id, new_angle)
    angle = new_angle

    time.sleep(0.25)

print("Calibration session finished.")
