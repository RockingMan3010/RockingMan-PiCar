#!/usr/bin/env python3

"""Safe hardware abstraction layer for RockingMan PiCar-Pro."""

import sys
from pathlib import Path

ADEEPT_SERVER = Path.home() / "Adeept_PiCar-Pro" / "Server"

if not ADEEPT_SERVER.is_dir():
    raise RuntimeError(
        f"Adeept Server directory not found: {ADEEPT_SERVER}"
    )

sys.path.insert(0, str(ADEEPT_SERVER))

import Move as move
import RPIservo
import Switch

from hardware_profile import (
    STEERING_CHANNEL,
    ULTRASONIC_PAN_CHANNEL,
    ARM_CHANNEL,
    WRIST_CHANNEL,
    GRIPPER_CHANNEL,

    STEERING_CENTER,
    STEERING_LEFT_SIGN,
    STEERING_RIGHT_SIGN,

    ULTRASONIC_LEFT_SIGN,
    ULTRASONIC_RIGHT_SIGN,

    ARM_FRONT_SIGN,
    ARM_REAR_SIGN,

    WRIST_UP_SIGN,
    WRIST_DOWN_SIGN,

    GRIPPER_CLOSED,
    GRIPPER_OPEN_SIGN,
    GRIPPER_MIN_SAFE,

    LEFT_HEADLIGHT_SWITCH,
    RIGHT_HEADLIGHT_SWITCH,
)


# Only this small range has been physically validated so far.
VALIDATED_SERVO_STEP_MAX = 5


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


class RockingManRobot:
    def __init__(self):
        self.servo = RPIservo.ServoCtrl()

        move.setup()

        Switch.switchSetup()
        Switch.set_all_switch_off()

        self.stop()
        self.steering_center()

    # ========================================================
    # DRIVE
    # ========================================================

    def stop(self):
        move.motorStop()

    def forward(self, speed=15):
        speed = clamp(speed, 0, 100)
        move.move(speed, 1, "no")

    def backward(self, speed=15):
        speed = clamp(speed, 0, 100)
        move.move(speed, -1, "no")

    # ========================================================
    # STEERING
    # ========================================================

    def steering_center(self):
        self.servo.moveAngle(
            STEERING_CHANNEL,
            STEERING_CENTER,
        )

    def steering_left(self, degrees=5):
        degrees = clamp(
            abs(degrees),
            0,
            VALIDATED_SERVO_STEP_MAX,
        )

        target = (
            STEERING_CENTER
            + STEERING_LEFT_SIGN * degrees
        )

        self.servo.moveAngle(
            STEERING_CHANNEL,
            target,
        )

    def steering_right(self, degrees=5):
        degrees = clamp(
            abs(degrees),
            0,
            VALIDATED_SERVO_STEP_MAX,
        )

        target = (
            STEERING_CENTER
            + STEERING_RIGHT_SIGN * degrees
        )

        self.servo.moveAngle(
            STEERING_CHANNEL,
            target,
        )

    # ========================================================
    # ULTRASONIC PAN
    # ========================================================

    def ultrasonic_center(self):
        self.servo.moveAngle(
            ULTRASONIC_PAN_CHANNEL,
            0,
        )

    def ultrasonic_left(self, degrees=5):
        degrees = clamp(
            abs(degrees),
            0,
            VALIDATED_SERVO_STEP_MAX,
        )

        self.servo.moveAngle(
            ULTRASONIC_PAN_CHANNEL,
            ULTRASONIC_LEFT_SIGN * degrees,
        )

    def ultrasonic_right(self, degrees=5):
        degrees = clamp(
            abs(degrees),
            0,
            VALIDATED_SERVO_STEP_MAX,
        )

        self.servo.moveAngle(
            ULTRASONIC_PAN_CHANNEL,
            ULTRASONIC_RIGHT_SIGN * degrees,
        )

    # ========================================================
    # ARM
    # ========================================================

    def arm_neutral(self):
        self.servo.moveAngle(
            ARM_CHANNEL,
            0,
        )

    def arm_front(self, degrees=5):
        degrees = clamp(
            abs(degrees),
            0,
            VALIDATED_SERVO_STEP_MAX,
        )

        self.servo.moveAngle(
            ARM_CHANNEL,
            ARM_FRONT_SIGN * degrees,
        )

    def arm_rear(self, degrees=5):
        degrees = clamp(
            abs(degrees),
            0,
            VALIDATED_SERVO_STEP_MAX,
        )

        self.servo.moveAngle(
            ARM_CHANNEL,
            ARM_REAR_SIGN * degrees,
        )

    # ========================================================
    # WRIST
    # ========================================================

    def wrist_neutral(self):
        self.servo.moveAngle(
            WRIST_CHANNEL,
            0,
        )

    def wrist_up(self, degrees=5):
        degrees = clamp(
            abs(degrees),
            0,
            VALIDATED_SERVO_STEP_MAX,
        )

        self.servo.moveAngle(
            WRIST_CHANNEL,
            WRIST_UP_SIGN * degrees,
        )

    def wrist_down(self, degrees=5):
        degrees = clamp(
            abs(degrees),
            0,
            VALIDATED_SERVO_STEP_MAX,
        )

        self.servo.moveAngle(
            WRIST_CHANNEL,
            WRIST_DOWN_SIGN * degrees,
        )

    # ========================================================
    # GRIPPER
    # ========================================================

    def gripper_close(self):
        self.servo.moveAngle(
            GRIPPER_CHANNEL,
            GRIPPER_CLOSED,
        )

    def gripper_open(self, degrees=5):
        degrees = clamp(
            abs(degrees),
            GRIPPER_MIN_SAFE,
            VALIDATED_SERVO_STEP_MAX,
        )

        self.servo.moveAngle(
            GRIPPER_CHANNEL,
            GRIPPER_OPEN_SIGN * degrees,
        )

    # ========================================================
    # HEADLIGHTS
    # ========================================================

    def left_headlight(self, on=True):
        Switch.switch(
            LEFT_HEADLIGHT_SWITCH,
            1 if on else 0,
        )

    def right_headlight(self, on=True):
        Switch.switch(
            RIGHT_HEADLIGHT_SWITCH,
            1 if on else 0,
        )

    def headlights_on(self):
        self.left_headlight(True)
        self.right_headlight(True)

    def headlights_off(self):
        self.left_headlight(False)
        self.right_headlight(False)

    # ========================================================
    # SAFE STATE
    # ========================================================

    def neutral_pose(self):
        self.stop()
        self.steering_center()
        self.ultrasonic_center()
        self.arm_neutral()
        self.wrist_neutral()
        self.gripper_close()
        self.headlights_off()

    def shutdown(self):
        self.stop()
        self.headlights_off()

        try:
            move.destroy()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()
