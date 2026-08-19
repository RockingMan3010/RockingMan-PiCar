#!/usr/bin/env python3

"""Sensor abstraction layer for RockingMan PiCar-Pro."""

from dataclasses import dataclass
import math
import statistics
import time

import cv2
import smbus
from gpiozero import DistanceSensor, InputDevice
from mpu6050 import mpu6050

from hardware_profile import (
    ADS7830_ADDRESS,
    MPU6050_ADDRESS,
    LINE_SENSOR_LEFT_GPIO,
    LINE_SENSOR_MIDDLE_GPIO,
    LINE_SENSOR_RIGHT_GPIO,
    LINE_WHITE_STATE,
    LINE_BLACK_STATE,
    ULTRASONIC_TRIGGER_GPIO,
    ULTRASONIC_ECHO_GPIO,
    ULTRASONIC_MAX_DISTANCE_M,
    USB_CAMERA_DEVICE,
)


@dataclass(frozen=True)
class LineState:
    left: int
    middle: int
    right: int

    @property
    def tuple(self):
        return self.left, self.middle, self.right

    @property
    def all_white(self):
        return self.tuple == (
            LINE_WHITE_STATE,
            LINE_WHITE_STATE,
            LINE_WHITE_STATE,
        )

    @property
    def all_black(self):
        return self.tuple == (
            LINE_BLACK_STATE,
            LINE_BLACK_STATE,
            LINE_BLACK_STATE,
        )


@dataclass(frozen=True)
class IMUReading:
    accel_x: float
    accel_y: float
    accel_z: float

    gyro_x: float
    gyro_y: float
    gyro_z: float

    @property
    def acceleration_magnitude(self):
        return math.sqrt(
            self.accel_x**2
            + self.accel_y**2
            + self.accel_z**2
        )


class RobotSensors:
    """Clean access to the PiCar-Pro sensor stack."""

    ADC_VREF = 4.93

    R15 = 3000
    R17 = 1000

    DIVISION_RATIO = R17 / (R15 + R17)

    ADS7830_CMD = 0x84
    ADS7830_CHANNEL = 0

    def __init__(self):
        self._closed = False

        # Battery ADC
        self._i2c_bus = smbus.SMBus(1)

        # Ultrasonic
        self._ultrasonic = DistanceSensor(
            echo=ULTRASONIC_ECHO_GPIO,
            trigger=ULTRASONIC_TRIGGER_GPIO,
            max_distance=ULTRASONIC_MAX_DISTANCE_M,
        )

        # Line tracking sensors
        self._line_left = InputDevice(
            LINE_SENSOR_LEFT_GPIO
        )

        self._line_middle = InputDevice(
            LINE_SENSOR_MIDDLE_GPIO
        )

        self._line_right = InputDevice(
            LINE_SENSOR_RIGHT_GPIO
        )

        # IMU
        self._imu = mpu6050(
            MPU6050_ADDRESS
        )

        # Camera is opened lazily only when requested.
        self._camera = None

    # ========================================================
    # BATTERY
    # ========================================================

    def _battery_control_byte(self):
        channel = self.ADS7830_CHANNEL

        return self.ADS7830_CMD | (
            (
                (
                    channel << 2
                    | channel >> 1
                )
                & 0x07
            )
            << 4
        )

    def battery_voltage(
        self,
        samples=10,
        delay=0.05,
    ):
        """Return filtered battery voltage in volts."""

        values = []

        for _ in range(samples):
            raw = self._i2c_bus.read_byte_data(
                ADS7830_ADDRESS,
                self._battery_control_byte(),
            )

            adc_voltage = (
                raw
                / 255.0
                * self.ADC_VREF
            )

            actual_voltage = (
                adc_voltage
                / self.DIVISION_RATIO
            )

            values.append(actual_voltage)

            if delay:
                time.sleep(delay)

        return round(
            statistics.median(values),
            3,
        )

    # ========================================================
    # ULTRASONIC
    # ========================================================

    def distance_cm(
        self,
        samples=7,
        delay=0.08,
        discard_first=2,
    ):
        """Return median ultrasonic distance in centimeters."""

        # Allow a couple of initial readings to settle.
        for _ in range(discard_first):
            _ = self._ultrasonic.distance
            time.sleep(delay)

        values = []

        for _ in range(samples):
            distance = (
                self._ultrasonic.distance
                * 100.0
            )

            values.append(distance)

            if delay:
                time.sleep(delay)

        return round(
            statistics.median(values),
            2,
        )

    # ========================================================
    # LINE SENSORS
    # ========================================================

    def line_state(self):
        """Return current left/middle/right digital line state."""

        return LineState(
            left=int(self._line_left.value),
            middle=int(self._line_middle.value),
            right=int(self._line_right.value),
        )

    def line_left_is_black(self):
        return (
            int(self._line_left.value)
            == LINE_BLACK_STATE
        )

    def line_middle_is_black(self):
        return (
            int(self._line_middle.value)
            == LINE_BLACK_STATE
        )

    def line_right_is_black(self):
        return (
            int(self._line_right.value)
            == LINE_BLACK_STATE
        )

    # ========================================================
    # MPU6050
    # ========================================================

    def imu(self):
        """Return accelerometer and gyroscope data."""

        accel = self._imu.get_accel_data()
        gyro = self._imu.get_gyro_data()

        return IMUReading(
            accel_x=accel["x"],
            accel_y=accel["y"],
            accel_z=accel["z"],

            gyro_x=gyro["x"],
            gyro_y=gyro["y"],
            gyro_z=gyro["z"],
        )

    def acceleration(self):
        reading = self.imu()

        return (
            reading.accel_x,
            reading.accel_y,
            reading.accel_z,
        )

    def gyroscope(self):
        reading = self.imu()

        return (
            reading.gyro_x,
            reading.gyro_y,
            reading.gyro_z,
        )

    # ========================================================
    # CAMERA
    # ========================================================

    def _ensure_camera(
        self,
        width=640,
        height=480,
    ):
        if (
            self._camera is not None
            and self._camera.isOpened()
        ):
            return

        self._camera = cv2.VideoCapture(
            USB_CAMERA_DEVICE,
            cv2.CAP_V4L2,
        )

        if not self._camera.isOpened():
            raise RuntimeError(
                f"Could not open camera device "
                f"/dev/video{USB_CAMERA_DEVICE}"
            )

        self._camera.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            width,
        )

        self._camera.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            height,
        )

        # Camera warm-up.
        for _ in range(5):
            self._camera.read()
            time.sleep(0.04)

    def camera_frame(
        self,
        width=640,
        height=480,
    ):
        """Return one OpenCV BGR frame."""

        self._ensure_camera(
            width=width,
            height=height,
        )

        ok, frame = self._camera.read()

        if not ok or frame is None:
            raise RuntimeError(
                "Camera failed to return a valid frame."
            )

        return frame

    def camera_resolution(self):
        frame = self.camera_frame()

        height, width = frame.shape[:2]

        return width, height

    # ========================================================
    # RESOURCE MANAGEMENT
    # ========================================================

    def close(self):
        if self._closed:
            return

        self._closed = True

        try:
            self._ultrasonic.close()
        except Exception:
            pass

        for sensor in (
            self._line_left,
            self._line_middle,
            self._line_right,
        ):
            try:
                sensor.close()
            except Exception:
                pass

        try:
            self._i2c_bus.close()
        except Exception:
            pass

        if self._camera is not None:
            try:
                self._camera.release()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        self.close()