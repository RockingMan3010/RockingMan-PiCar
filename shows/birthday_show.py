#!/usr/bin/env python3

import sys
import time
import subprocess
import busio

from pathlib import Path
from board import SCL, SDA
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo, motor

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306


# =========================================================
# CUSTOM SETTINGS
# =========================================================

FRIEND_NAME = "Vedant"       # <-- YAHAN FRIEND KA NAAM
DRIVE_SPEED = 5             # 0-100
TURN_SPEED = 100

# Starting estimate only.
# 180-degree rotation calibration ke baad isko tune karna.
TURN_180_TIME = 1

STEERING_LEFT = 30
STEERING_RIGHT = -30
STEERING_CENTER = 0


# =========================================================
# ARM CALIBRATION
# =========================================================

SERVO_BASE = 1
SERVO_ARM = 2
SERVO_WRIST = 3
SERVO_GRIPPER = 4

BASE_MIN = -65
BASE_MAX = 65

ARM_MIN = -75
ARM_MAX = 75

WRIST_MIN = -50
WRIST_MAX = 85

GRIPPER_CLOSED = 5
GRIPPER_OPEN = 65


# =========================================================
# MOTOR CHANNELS
#
# From Adeept Move.py
# =========================================================

MOTOR_M1_IN1 = 15
MOTOR_M1_IN2 = 14

MOTOR_M2_IN1 = 12
MOTOR_M2_IN2 = 13

M1_DIRECTION = -1
M2_DIRECTION = -1


# =========================================================
# PCA9685 HARDWARE
# One persistent connection for steering + arm + motors
# =========================================================

i2c_bus = busio.I2C(SCL, SDA)

pca = PCA9685(
    i2c_bus,
    address=0x5F
)

pca.frequency = 50


# =========================================================
# SERVOS
# =========================================================

servo_hw = {}

for servo_id in range(0, 5):

    servo_hw[servo_id] = servo.Servo(
        pca.channels[servo_id],
        min_pulse=500,
        max_pulse=2400,
        actuation_range=180
    )


# =========================================================
# MOTORS
# =========================================================

motor1 = motor.DCMotor(
    pca.channels[MOTOR_M1_IN1],
    pca.channels[MOTOR_M1_IN2]
)

motor2 = motor.DCMotor(
    pca.channels[MOTOR_M2_IN1],
    pca.channels[MOTOR_M2_IN2]
)

motor1.decay_mode = motor.SLOW_DECAY
motor2.decay_mode = motor.SLOW_DECAY


# =========================================================
# OLED
# =========================================================

oled_serial = i2c(
    port=1,
    address=0x3C
)

oled = ssd1306(
    oled_serial,
    rotate=0
)


def centered(draw, text, y):

    bbox = draw.textbbox(
        (0, 0),
        text
    )

    width = bbox[2] - bbox[0]

    x = (
        oled.width
        - width
    ) // 2

    draw.text(
        (x, y),
        text,
        fill="white"
    )


def oled_message(
    line1="",
    line2="",
    line3="",
    line4=""
):

    with canvas(oled) as draw:

        lines = [
            (line1, 2),
            (line2, 18),
            (line3, 34),
            (line4, 50),
        ]

        for text, y in lines:

            if text:
                centered(
                    draw,
                    text,
                    y
                )


# =========================================================
# SERVICE CONTROL
# =========================================================

def stop_service(name):

    subprocess.run(
        [
            "sudo",
            "systemctl",
            "stop",
            name
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False
    )


def start_service(name):

    subprocess.run(
        [
            "sudo",
            "systemctl",
            "start",
            name
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False
    )


# =========================================================
# ARM MOTION ENGINE
# =========================================================

limits = {

    SERVO_BASE: (
        BASE_MIN,
        BASE_MAX
    ),

    SERVO_ARM: (
        ARM_MIN,
        ARM_MAX
    ),

    SERVO_WRIST: (
        WRIST_MIN,
        WRIST_MAX
    ),

    SERVO_GRIPPER: (
        GRIPPER_CLOSED,
        GRIPPER_OPEN
    ),
}


current = {

    SERVO_BASE: 0.0,

    SERVO_ARM: 0.0,

    SERVO_WRIST: 0.0,

    SERVO_GRIPPER: 50.0,
}


FPS = 30.0
FRAME_TIME = 1.0 / FPS


def clamp(
    servo_id,
    value
):

    low, high = limits[servo_id]

    return max(
        low,
        min(
            high,
            value
        )
    )


def write_arm_offset(
    servo_id,
    offset
):

    offset = clamp(
        servo_id,
        offset
    )

    absolute = 90 + offset

    absolute = max(
        0,
        min(
            180,
            absolute
        )
    )

    servo_hw[
        servo_id
    ].angle = absolute


def smootherstep(t):

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

        SERVO_BASE:
            base,

        SERVO_ARM:
            arm,

        SERVO_WRIST:
            wrist,

        SERVO_GRIPPER:
            gripper
    }

    for servo_id, value in requested.items():

        if value is not None:

            targets[
                servo_id
            ] = clamp(
                servo_id,
                float(value)
            )

    starts = dict(current)

    frames = max(
        1,
        int(
            duration * FPS
        )
    )

    last_sent = {

        servo_id:
            round(
                starts[
                    servo_id
                ]
            )

        for servo_id
        in current
    }

    next_frame = time.monotonic()

    for frame in range(
        1,
        frames + 1
    ):

        t = (
            frame
            / frames
        )

        eased = smootherstep(t)

        for servo_id in current:

            start = starts[
                servo_id
            ]

            target = targets[
                servo_id
            ]

            position = (
                start
                + (
                    target
                    - start
                )
                * eased
            )

            command = round(
                position
            )

            if (
                command
                !=
                last_sent[
                    servo_id
                ]
            ):

                write_arm_offset(
                    servo_id,
                    command
                )

                last_sent[
                    servo_id
                ] = command

        next_frame += FRAME_TIME

        sleep_time = (
            next_frame
            - time.monotonic()
        )

        if sleep_time > 0:

            time.sleep(
                sleep_time
            )

    current.update(
        targets
    )


def arm_home(
    duration=1.5
):

    move_pose(
        base=0,
        arm=0,
        wrist=0,
        gripper=50,
        duration=duration
    )


# =========================================================
# STEERING
# =========================================================

def steering(angle):

    absolute = 90 + angle

    absolute = max(
        0,
        min(
            180,
            absolute
        )
    )

    servo_hw[0].angle = absolute


def steering_center():

    steering(
        STEERING_CENTER
    )


# =========================================================
# MOTOR HELPERS
# =========================================================

def motor_value(
    speed,
    direction
):

    speed = max(
        0,
        min(
            100,
            speed
        )
    )

    value = (
        speed
        / 100.0
    )

    return (
        value
        * direction
    )


def drive_forward(
    speed=DRIVE_SPEED
):

    motor1.throttle = motor_value(
        speed,
        M1_DIRECTION
    )

    motor2.throttle = motor_value(
        speed,
        M2_DIRECTION
    )


def drive_backward(
    speed=DRIVE_SPEED
):

    motor1.throttle = motor_value(
        speed,
        -M1_DIRECTION
    )

    motor2.throttle = motor_value(
        speed,
        -M2_DIRECTION
    )


def drive_stop():

    motor1.throttle = 0
    motor2.throttle = 0


def forward_for(
    seconds,
    speed=DRIVE_SPEED
):

    steering_center()

    drive_forward(
        speed
    )

    time.sleep(
        seconds
    )

    drive_stop()


def backward_for(
    seconds,
    speed=DRIVE_SPEED
):

    steering_center()

    drive_backward(
        speed
    )

    time.sleep(
        seconds
    )

    drive_stop()


# =========================================================
# TURN / ROTATION
# =========================================================

def rotate_in_place_180():

    print("Rotating 180 degrees...")

    # Steering wheels straight
    steering_center()

    # Left side forward
    motor1.throttle = motor_value(
        TURN_SPEED,
        M1_DIRECTION
    )

    # Right side backward
    motor2.throttle = motor_value(
        TURN_SPEED,
        -M2_DIRECTION
    )

    time.sleep(TURN_180_TIME)

    drive_stop()

    time.sleep(0.5)


# =========================================================
# DANCE FUNCTIONS
# =========================================================

def body_wiggle():

    print(
        "Body dance..."
    )

    steering(
        STEERING_LEFT
    )

    drive_forward(30)

    time.sleep(
        0.45
    )

    drive_stop()

    steering(
        STEERING_RIGHT
    )

    drive_forward(30)

    time.sleep(
        0.45
    )

    drive_stop()

    steering(
        STEERING_LEFT
    )

    drive_backward(30)

    time.sleep(
        0.4
    )

    drive_stop()

    steering(
        STEERING_RIGHT
    )

    drive_backward(30)

    time.sleep(
        0.4
    )

    drive_stop()

    steering_center()


def arm_wave():

    print(
        "Arm wave..."
    )

    move_pose(
        base=-15,
        arm=-18,
        wrist=20,
        gripper=55,
        duration=1.2
    )

    for _ in range(3):

        move_pose(
            wrist=38,
            duration=0.55
        )

        move_pose(
            wrist=5,
            duration=0.55
        )

    move_pose(
        wrist=20,
        duration=0.6
    )


def gripper_party():

    print(
        "Gripper party..."
    )

    for _ in range(2):

        move_pose(
            gripper=GRIPPER_OPEN,
            duration=0.8
        )

        move_pose(
            gripper=GRIPPER_CLOSED,
            duration=0.8
        )

    move_pose(
        gripper=GRIPPER_OPEN,
        duration=0.8
    )


def arm_dance():

    move_pose(
        base=-30,
        arm=-25,
        wrist=15,
        duration=1.5
    )

    move_pose(
        base=30,
        arm=-15,
        wrist=-15,
        duration=1.8
    )

    move_pose(
        base=-25,
        arm=20,
        wrist=25,
        duration=1.7
    )

    move_pose(
        base=0,
        arm=-10,
        wrist=10,
        duration=1.3
    )


def bow():

    print(
        "Final bow..."
    )

    move_pose(
        base=0,
        arm=30,
        wrist=-20,
        gripper=45,
        duration=1.5
    )

    time.sleep(
        0.8
    )

    move_pose(
        arm=0,
        wrist=0,
        duration=1.3
    )


# =========================================================
# CLEANUP
# =========================================================

def safe_cleanup():

    drive_stop()

    steering_center()

    try:

        arm_home(
            1.5
        )

    except Exception:

        pass


# =========================================================
# BIRTHDAY SHOW
# =========================================================

def birthday_show():

    print()
    print(
        "=============================="
    )
    print(
        " ROCKINGMAN BIRTHDAY SHOW"
    )
    print(
        "=============================="
    )
    print()

    # OLED must be controlled only by this script
    stop_service(
        "robot-oled.service"
    )

    drive_stop()

    steering_center()

    arm_home(
        1.5
    )


    # =====================================================
    # PHASE 1
    #
    # REAR OLED faces birthday person
    # =====================================================

    print(
        "Birthday message..."
    )

    oled_message(
        "HAPPY",
        "BIRTHDAY",
        FRIEND_NAME,
        "FROM ROCKINGMAN"
    )

    time.sleep(
        4.0
    )


    # =====================================================
    # PHASE 2
    #
    # Clear display and turn FRONT toward person
    # =====================================================

    oled.clear()

    rotate_in_place_180()


    # =====================================================
    # PHASE 3
    #
    # Front-facing entrance
    # =====================================================

    forward_for(
        0.65,
        speed=32
    )

    time.sleep(
        0.4
    )

    backward_for(
        0.25,
        speed=28
    )

    time.sleep(
        0.5
    )


    # =====================================================
    # PHASE 4
    #
    # Hello wave
    # =====================================================

    arm_wave()

    time.sleep(
        0.5
    )


    # =====================================================
    # PHASE 5
    #
    # Arm dance
    # =====================================================

    arm_dance()

    time.sleep(
        0.5
    )


    # =====================================================
    # PHASE 6
    #
    # Body dance
    # =====================================================

    body_wiggle()

    time.sleep(
        0.5
    )


    # =====================================================
    # PHASE 7
    #
    # Gripper celebration
    # =====================================================

    gripper_party()

    time.sleep(
        0.5
    )


    # =====================================================
    # PHASE 8
    #
    # Final bow toward friend
    # =====================================================

    bow()

    time.sleep(
        1.0
    )


    # =====================================================
    # PHASE 9
    #
    # Turn rear OLED back toward person
    # =====================================================

    arm_home(
        1.5
    )

    rotate_180_left()


    # =====================================================
    # PHASE 10
    #
    # Final birthday message
    # =====================================================

    oled_message(
        "HAPPY BIRTHDAY",
        FRIEND_NAME,
        "BEST WISHES!",
        "<3"
    )

    time.sleep(
        5.0
    )

    oled.clear()

    drive_stop()

    steering_center()

    arm_home(
        1.5
    )

    start_service(
        "robot-oled.service"
    )

    print()
    print(
        "BIRTHDAY SHOW COMPLETE!"
    )
    print()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    try:

        steering_center()
        rotate_in_place_180()

    except KeyboardInterrupt:

        print(
            "\nShow cancelled."
        )

        safe_cleanup()

        oled.clear()

        start_service(
            "robot-oled.service"
        )


    except Exception as error:

        print(
            f"\nERROR: {error}"
        )

        safe_cleanup()

        try:

            oled_message(
                "SHOW ERROR",
                type(error).__name__,
                "",
                ""
            )

            time.sleep(
                2
            )

            oled.clear()

        except Exception:

            pass

        start_service(
            "robot-oled.service"
        )

        raise


    finally:

        try:
            drive_stop()
        except Exception:
            pass

        try:
            steering_center()
        except Exception:
            pass

        time.sleep(
            0.2
        )

        try:
            pca.deinit()
        except Exception:
            pass

        try:
            i2c_bus.deinit()
        except Exception:
            pass