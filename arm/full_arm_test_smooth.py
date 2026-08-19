#!/usr/bin/env python3

import time
import busio
from board import SCL, SDA
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

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

# =========================================================
# HARDWARE - INITIALIZE ONCE
# =========================================================

i2c = busio.I2C(SCL, SDA)

pca = PCA9685(
    i2c,
    address=0x5F
)

pca.frequency = 50

hw = {
    SERVO_BASE: servo.Servo(
        pca.channels[SERVO_BASE],
        min_pulse=500,
        max_pulse=2400,
        actuation_range=180
    ),

    SERVO_ARM: servo.Servo(
        pca.channels[SERVO_ARM],
        min_pulse=500,
        max_pulse=2400,
        actuation_range=180
    ),

    SERVO_WRIST: servo.Servo(
        pca.channels[SERVO_WRIST],
        min_pulse=500,
        max_pulse=2400,
        actuation_range=180
    ),

    SERVO_GRIPPER: servo.Servo(
        pca.channels[SERVO_GRIPPER],
        min_pulse=500,
        max_pulse=2400,
        actuation_range=180
    ),
}


# =========================================================
# CALIBRATED LIMITS
# =========================================================

limits = {
    SERVO_BASE: (
        BASE_WORK_MIN,
        BASE_WORK_MAX
    ),

    SERVO_ARM: (
        ARM_WORK_MIN,
        ARM_WORK_MAX
    ),

    SERVO_WRIST: (
        WRIST_WORK_MIN,
        WRIST_WORK_MAX
    ),

    SERVO_GRIPPER: (
        GRIPPER_WORK_CLOSED,
        GRIPPER_WORK_OPEN
    ),
}


# Current offsets from 90-degree servo centre
current = {
    SERVO_BASE: 0.0,
    SERVO_ARM: 0.0,
    SERVO_WRIST: 0.0,
    SERVO_GRIPPER: 50.0,
}


FPS = 50.0
FRAME_TIME = 1.0 / FPS


def clamp(servo_id, value):
    low, high = limits[servo_id]
    return max(low, min(high, value))


def write_offset(servo_id, offset):
    """
    Our calibration values are offsets around
    Adeept's 90-degree centre.
    """

    offset = clamp(
        servo_id,
        offset
    )

    absolute_angle = 90.0 + offset

    absolute_angle = max(
        0.0,
        min(180.0, absolute_angle)
    )

    hw[servo_id].angle = absolute_angle


def smootherstep(t):
    """
    Smooth acceleration AND deceleration.

    Velocity and acceleration approach zero
    at the beginning and end of each motion.
    """

    return (
        6 * t**5
        - 15 * t**4
        + 10 * t**3
    )


def move_pose(
    base=None,
    arm=None,
    wrist=None,
    gripper=None,
    duration=1.5
):

    targets = dict(current)

    requested = {
        SERVO_BASE: base,
        SERVO_ARM: arm,
        SERVO_WRIST: wrist,
        SERVO_GRIPPER: gripper,
    }

    for servo_id, value in requested.items():
        if value is not None:
            targets[servo_id] = clamp(
                servo_id,
                float(value)
            )

    starts = dict(current)

    frames = max(
        1,
        int(duration * FPS)
    )

    next_frame = time.monotonic()

    for frame in range(1, frames + 1):

        t = frame / frames

        eased = smootherstep(t)

        for servo_id in current:

            start = starts[servo_id]
            target = targets[servo_id]

            position = (
                start
                + (target - start) * eased
            )

            write_offset(
                servo_id,
                position
            )

        # Keep frame timing stable instead of
        # accumulating I2C execution delay.
        next_frame += FRAME_TIME

        sleep_time = (
            next_frame
            - time.monotonic()
        )

        if sleep_time > 0:
            time.sleep(sleep_time)

    current.update(targets)


def pause(seconds=0.7):
    time.sleep(seconds)


def home(duration=2.0):
    move_pose(
        base=0,
        arm=0,
        wrist=0,
        gripper=50,
        duration=duration
    )


print()
print("==============================")
print(" ROCKINGMAN SMOOTH ARM TEST")
print("==============================")
print()
print("Persistent PCA9685 connection")
print("50 Hz motion updates")
print("Smootherstep trajectory")
print("Ctrl+C = safe return home")
print()


try:

    print("1/8  HOME")
    home(2.0)
    pause()

    print("2/8  BASE LEFT")
    move_pose(
        base=-45,
        duration=2.0
    )
    pause()

    print("3/8  BASE RIGHT")
    move_pose(
        base=45,
        duration=3.0
    )
    pause()

    print("4/8  CENTRE")
    move_pose(
        base=0,
        duration=1.5
    )
    pause()

    print("5/8  COORDINATED POSE A")
    move_pose(
        base=-25,
        arm=-30,
        wrist=20,
        duration=2.5
    )
    pause()

    print("6/8  COORDINATED POSE B")
    move_pose(
        base=25,
        arm=25,
        wrist=-20,
        duration=3.0
    )
    pause()

    print("7/8  GRIPPER")

    move_pose(
        gripper=GRIPPER_WORK_OPEN,
        duration=1.2
    )

    pause(0.7)

    move_pose(
        gripper=GRIPPER_WORK_CLOSED,
        duration=1.5
    )

    pause(0.7)

    move_pose(
        gripper=GRIPPER_WORK_OPEN,
        duration=1.5
    )

    pause()

    print("8/8  RETURN HOME")
    home(3.0)

    print()
    print("SMOOTH ARM TEST COMPLETE ✅")


except KeyboardInterrupt:

    print(
        "\nInterrupted - returning home..."
    )

    home(2.0)


finally:

    time.sleep(0.3)

    pca.deinit()
    i2c.deinit()

    print("Servo controller released.")
