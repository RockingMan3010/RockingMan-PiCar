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

from arm_config import (
    SERVO_BASE,
    SERVO_ARM,
    SERVO_WRIST,
    SERVO_GRIPPER,

    BASE_WORK_MIN,
    BASE_WORK_MAX,
    ARM_WORK_MIN,
    ARM_WORK_MAX,
    WRIST_WORK_MIN,
    WRIST_WORK_MAX,
    GRIPPER_WORK_CLOSED,
    GRIPPER_WORK_OPEN,
)

servo = RPIservo.ServoCtrl()

# --------------------------------------------------
# Current position
# Calibration scripts left joints near centre.
# --------------------------------------------------

current = {
    SERVO_BASE: 0,
    SERVO_ARM: 0,
    SERVO_WRIST: 0,
    SERVO_GRIPPER: GRIPPER_WORK_OPEN,
}

limits = {
    SERVO_BASE: (BASE_WORK_MIN, BASE_WORK_MAX),
    SERVO_ARM: (ARM_WORK_MIN, ARM_WORK_MAX),
    SERVO_WRIST: (WRIST_WORK_MIN, WRIST_WORK_MAX),
    SERVO_GRIPPER: (
        GRIPPER_WORK_CLOSED,
        GRIPPER_WORK_OPEN
    ),
}


def clamp(servo_id, angle):
    minimum, maximum = limits[servo_id]
    return max(minimum, min(maximum, angle))


def move_pose(
    base=None,
    arm=None,
    wrist=None,
    gripper=None,
    duration=1.2
):
    targets = dict(current)

    requested = {
        SERVO_BASE: base,
        SERVO_ARM: arm,
        SERVO_WRIST: wrist,
        SERVO_GRIPPER: gripper,
    }

    for servo_id, angle in requested.items():
        if angle is not None:
            targets[servo_id] = clamp(servo_id, angle)

    starts = dict(current)

    # ~50 Hz smooth interpolation
    steps = max(1, int(duration / 0.02))

    for step in range(1, steps + 1):

        ratio = step / steps

        for servo_id in current:

            start = starts[servo_id]
            target = targets[servo_id]

            angle = start + (target - start) * ratio

            servo.moveAngle(
                servo_id,
                angle
            )

        time.sleep(0.02)

    current.update(targets)


def pause(seconds=0.7):
    time.sleep(seconds)


print()
print("==============================")
print(" ROCKINGMAN FULL ARM TEST")
print("==============================")
print("Ctrl+C = stop")
print()

try:

    # ----------------------------------------------
    # 1. HOME
    # ----------------------------------------------

    print("1/8  HOME")

    move_pose(
        base=0,
        arm=0,
        wrist=0,
        gripper=50,
        duration=1.2
    )

    pause()


    # ----------------------------------------------
    # 2. BASE LEFT
    # ----------------------------------------------

    print("2/8  BASE LEFT")

    move_pose(
        base=-45,
        duration=1.2
    )

    pause()


    # ----------------------------------------------
    # 3. BASE RIGHT
    # ----------------------------------------------

    print("3/8  BASE RIGHT")

    move_pose(
        base=45,
        duration=1.8
    )

    pause()


    # ----------------------------------------------
    # 4. CENTRE + ARM POSE
    # ----------------------------------------------

    print("4/8  ARM UP")

    move_pose(
        base=0,
        arm=-35,
        wrist=20,
        duration=1.5
    )

    pause()


    # ----------------------------------------------
    # 5. SECOND COORDINATED POSE
    # ----------------------------------------------

    print("5/8  REACH POSE")

    move_pose(
        base=-30,
        arm=30,
        wrist=-25,
        duration=1.6
    )

    pause()


    # ----------------------------------------------
    # 6. OPEN GRIPPER
    # ----------------------------------------------

    print("6/8  GRIPPER OPEN")

    move_pose(
        gripper=GRIPPER_WORK_OPEN,
        duration=0.8
    )

    pause()


    # ----------------------------------------------
    # 7. GENTLE CLOSE + OPEN
    # ----------------------------------------------

    print("7/8  GRIPPER CLOSE")

    move_pose(
        gripper=GRIPPER_WORK_CLOSED,
        duration=1.0
    )

    pause(1)

    print("     GRIPPER REOPEN")

    move_pose(
        gripper=GRIPPER_WORK_OPEN,
        duration=1.0
    )

    pause()


    # ----------------------------------------------
    # 8. HOME
    # ----------------------------------------------

    print("8/8  RETURN HOME")

    move_pose(
        base=0,
        arm=0,
        wrist=0,
        gripper=50,
        duration=2.0
    )

    print()
    print("FULL ARM TEST PASSED ✅")


except KeyboardInterrupt:

    print("\nTest interrupted.")


finally:

    print("Returning arm gently to HOME...")

    move_pose(
        base=0,
        arm=0,
        wrist=0,
        gripper=50,
        duration=1.5
    )

    print("Arm safe.")
