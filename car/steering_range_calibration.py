#!/usr/bin/env python3

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAR_DIR = ROOT / "car"

sys.path.insert(0, str(CAR_DIR))

from hardware_profile import (
    STEERING_CHANNEL,
    STEERING_CENTER,
)

ADEEPT_SERVER = Path.home() / "Adeept_PiCar-Pro" / "Server"
sys.path.insert(0, str(ADEEPT_SERVER))

import RPIservo


TEST_OFFSETS = [
    ("LEFT", -5),
    ("LEFT", -10),
    ("LEFT", -15),
    ("RIGHT", 5),
    ("RIGHT", 10),
    ("RIGHT", 15),
]


def move_servo(servo, offset):
    target = STEERING_CENTER + offset

    print()
    print(
        f"Command: center {STEERING_CENTER:+d}° "
        f"+ offset {offset:+d}° "
        f"= target {target:+d}°"
    )

    servo.moveAngle(
        STEERING_CHANNEL,
        target,
    )


def main():
    servo = RPIservo.ServoCtrl()

    print()
    print("RockingMan Steering Range Calibration")
    print("=" * 55)
    print("DRIVE MOTORS WILL NOT MOVE.")
    print()
    print("At every step inspect:")
    print("- wheel steering angle")
    print("- servo buzzing")
    print("- mechanical binding")
    print("- linkage contact")
    print()
    print("Press Ctrl+C immediately if anything looks wrong.")

    try:
        print()
        input("Press ENTER to move to calibrated CENTER...")

        move_servo(
            servo,
            0,
        )

        time.sleep(1)

        for direction, offset in TEST_OFFSETS:
            print()
            print("-" * 55)
            print(
                f"NEXT TEST: {direction} {abs(offset)}°"
            )

            input(
                "Press ENTER to execute this steering position..."
            )

            move_servo(
                servo,
                offset,
            )

            time.sleep(2)

            input(
                "Inspect the wheels. Press ENTER to return CENTER..."
            )

            move_servo(
                servo,
                0,
            )

            time.sleep(1)

        print()
        print("=" * 55)
        print("Calibration sequence completed.")

    except KeyboardInterrupt:
        print()
        print("Calibration interrupted.")

    finally:
        print("Returning steering to calibrated center.")
        move_servo(
            servo,
            0,
        )


if __name__ == "__main__":
    main()