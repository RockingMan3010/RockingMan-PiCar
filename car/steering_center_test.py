#!/usr/bin/env python3

import sys
from pathlib import Path

ADEEPT_SERVER = Path.home() / "Adeept_PiCar-Pro" / "Server"

if not ADEEPT_SERVER.is_dir():
    raise RuntimeError(
        f"Adeept Server directory not found: {ADEEPT_SERVER}"
    )

sys.path.insert(0, str(ADEEPT_SERVER))

import RPIservo

from chassis_config import (
    STEERING_SERVO_CHANNEL,
    STEERING_CENTER_OFFSET,
)


def main():
    steering = RPIservo.ServoCtrl()

    print(
        f"Centering steering channel {STEERING_SERVO_CHANNEL} "
        f"with calibrated offset {STEERING_CENTER_OFFSET}°"
    )

    steering.moveAngle(
        STEERING_SERVO_CHANNEL,
        STEERING_CENTER_OFFSET,
    )

    print("Steering centered.")


if __name__ == "__main__":
    main()
