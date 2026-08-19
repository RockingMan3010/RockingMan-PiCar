#!/usr/bin/env python3

import time
import subprocess
import busio

from board import SCL, SDA
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo, motor

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306


# =========================================================
# SETTINGS
# =========================================================

DRIVE_SPEED = 28
SPIN_SPEED = 22

# Calibrated arm working limits
BASE_MIN, BASE_MAX = -65, 65
ARM_MIN, ARM_MAX = -75, 75
WRIST_MIN, WRIST_MAX = -50, 85

GRIPPER_CLOSED = 5
GRIPPER_OPEN = 65

SERVO_BASE = 1
SERVO_ARM = 2
SERVO_WRIST = 3
SERVO_GRIPPER = 4

MOTOR_M1_IN1 = 15
MOTOR_M1_IN2 = 14
MOTOR_M2_IN1 = 12
MOTOR_M2_IN2 = 13

M1_DIRECTION = -1
M2_DIRECTION = -1


# =========================================================
# HARDWARE
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

for sid in range(5):

    servo_hw[sid] = servo.Servo(
        pca.channels[sid],
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


def show_oled(*lines):

    with canvas(oled) as draw:

        positions = [3, 19, 35, 51]

        for text, y in zip(lines, positions):

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
        ["sudo", "systemctl", "stop", name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False
    )


def start_service(name):

    subprocess.run(
        ["sudo", "systemctl", "start", name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False
    )


# =========================================================
# ARM MOTION
# =========================================================

limits = {

    SERVO_BASE:
        (BASE_MIN, BASE_MAX),

    SERVO_ARM:
        (ARM_MIN, ARM_MAX),

    SERVO_WRIST:
        (WRIST_MIN, WRIST_MAX),

    SERVO_GRIPPER:
        (GRIPPER_CLOSED, GRIPPER_OPEN),
}


current = {

    SERVO_BASE: 0.0,

    SERVO_ARM: 0.0,

    SERVO_WRIST: 0.0,

    SERVO_GRIPPER: 50.0,
}


FPS = 30.0


def clamp(sid, value):

    low, high = limits[sid]

    return max(
        low,
        min(high, value)
    )


def set_arm(sid, offset):

    offset = clamp(
        sid,
        offset
    )

    absolute = 90 + offset

    servo_hw[sid].angle = max(
        0,
        min(180, absolute)
    )


def smooth(t):

    return (
        6*t**5
        - 15*t**4
        + 10*t**3
    )


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

    for sid, value in requested.items():

        if value is not None:

            targets[sid] = clamp(
                sid,
                float(value)
            )

    starts = dict(current)

    frames = max(
        1,
        int(duration * FPS)
    )

    last_sent = {

        sid:
            round(starts[sid])

        for sid in current
    }

    next_frame = time.monotonic()

    for frame in range(
        1,
        frames + 1
    ):

        t = frame / frames

        eased = smooth(t)

        for sid in current:

            position = (
                starts[sid]
                +
                (
                    targets[sid]
                    - starts[sid]
                )
                * eased
            )

            command = round(
                position
            )

            if (
                command
                != last_sent[sid]
            ):

                set_arm(
                    sid,
                    command
                )

                last_sent[sid] = command

        next_frame += 1 / FPS

        delay = (
            next_frame
            - time.monotonic()
        )

        if delay > 0:

            time.sleep(delay)

    current.update(
        targets
    )


def home(duration=1.5):

    move_pose(
        base=0,
        arm=0,
        wrist=0,
        gripper=45,
        duration=duration
    )


# =========================================================
# DRIVE
# =========================================================

def motor_value(speed, direction):

    speed = max(
        0,
        min(100, speed)
    )

    return (
        speed
        / 100.0
        * direction
    )


def stop():

    motor1.throttle = 0
    motor2.throttle = 0


def forward(seconds):

    motor1.throttle = motor_value(
        DRIVE_SPEED,
        M1_DIRECTION
    )

    motor2.throttle = motor_value(
        DRIVE_SPEED,
        M2_DIRECTION
    )

    time.sleep(seconds)

    stop()


def backward(seconds):

    motor1.throttle = motor_value(
        DRIVE_SPEED,
        -M1_DIRECTION
    )

    motor2.throttle = motor_value(
        DRIVE_SPEED,
        -M2_DIRECTION
    )

    time.sleep(seconds)

    stop()


def spin_left(seconds):

    motor1.throttle = motor_value(
        SPIN_SPEED,
        -M1_DIRECTION
    )

    motor2.throttle = motor_value(
        SPIN_SPEED,
        M2_DIRECTION
    )

    time.sleep(seconds)

    stop()


def spin_right(seconds):

    motor1.throttle = motor_value(
        SPIN_SPEED,
        M1_DIRECTION
    )

    motor2.throttle = motor_value(
        SPIN_SPEED,
        -M2_DIRECTION
    )

    time.sleep(seconds)

    stop()


# =========================================================
# PERFORMANCE MOVES
# =========================================================

def wave():

    move_pose(
        base=-15,
        arm=-28,
        wrist=20,
        gripper=50,
        duration=1.3
    )

    for _ in range(4):

        move_pose(
            wrist=45,
            duration=0.45
        )

        move_pose(
            wrist=5,
            duration=0.45
        )


def gripper_clap():

    for _ in range(3):

        move_pose(
            gripper=GRIPPER_OPEN,
            duration=0.5
        )

        move_pose(
            gripper=GRIPPER_CLOSED,
            duration=0.5
        )

    move_pose(
        gripper=50,
        duration=0.5
    )


def arm_showoff():

    move_pose(
        base=-40,
        arm=-25,
        wrist=20,
        duration=1.3
    )

    move_pose(
        base=40,
        arm=-10,
        wrist=-20,
        duration=1.7
    )

    move_pose(
        base=-25,
        arm=25,
        wrist=30,
        duration=1.5
    )

    move_pose(
        base=25,
        arm=-30,
        wrist=15,
        duration=1.5
    )


def bow():

    move_pose(
        base=0,
        arm=35,
        wrist=-25,
        gripper=45,
        duration=1.4
    )

    time.sleep(0.8)

    move_pose(
        arm=0,
        wrist=0,
        duration=1.2
    )


# =========================================================
# MAIN SHOW
# =========================================================

def papa_demo():

    print("PAPA DEMO STARTING 😎")

    stop_service(
        "Adeept_Robot.service"
    )

    stop_service(
        "robot-oled.service"
    )

    stop()

    home()

    # -----------------------------------------
    # INTRO
    # -----------------------------------------

    show_oled(
        "HELLO PAPA!",
        "I AM",
        "ROCKINGMAN3010",
        ":)"
    )

    time.sleep(2.5)

    oled.clear()

    # -----------------------------------------
    # ROBOT ENTRY
    # -----------------------------------------

    forward(0.7)

    time.sleep(0.4)

    # -----------------------------------------
    # BIG HELLO WAVE
    # -----------------------------------------

    wave()

    time.sleep(0.5)

    # -----------------------------------------
    # BODY WIGGLE
    # -----------------------------------------

    spin_left(0.28)

    spin_right(0.28)

    spin_left(0.28)

    spin_right(0.28)

    time.sleep(0.5)

    # -----------------------------------------
    # ARM FLEX / SHOWOFF
    # -----------------------------------------

    arm_showoff()

    time.sleep(0.4)

    # -----------------------------------------
    # GRIPPER PARTY
    # -----------------------------------------

    gripper_clap()

    time.sleep(0.5)

    # -----------------------------------------
    # ROBOT MOVEMENT
    # -----------------------------------------

    backward(0.35)

    time.sleep(0.2)

    forward(0.35)

    time.sleep(0.5)

    # -----------------------------------------
    # FINAL BOW
    # -----------------------------------------

    bow()

    time.sleep(0.6)

    # -----------------------------------------
    # FINAL POSE
    # -----------------------------------------

    move_pose(
        base=-15,
        arm=-25,
        wrist=25,
        gripper=55,
        duration=1.2
    )

    show_oled(
        "DEMO COMPLETE",
        "THANK YOU",
        "PAPA!",
        "<3"
    )

    time.sleep(4)

    oled.clear()

    home()

    stop()

    start_service(
        "robot-oled.service"
    )

    print("PAPA DEMO COMPLETE ✅")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    try:

        papa_demo()

    except KeyboardInterrupt:

        print("\nDemo interrupted")

        stop()

        try:
            home()
        except:
            pass

        oled.clear()

        start_service(
            "robot-oled.service"
        )

    finally:

        try:
            stop()
        except:
            pass

        time.sleep(0.2)

        try:
            pca.deinit()
        except:
            pass

        try:
            i2c_bus.deinit()
        except:
            pass
