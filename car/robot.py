#!/usr/bin/env python3

"""Unified RockingMan PiCar-Pro robot interface."""

from robot_hardware import RockingManRobot
from robot_sensors import RobotSensors


class Robot:
    """Unified actuator and sensor interface."""

    def __init__(self):
        self.hardware = RockingManRobot()
        self.sensors = RobotSensors()
        self._closed = False

    # ========================================================
    # DRIVE
    # ========================================================

    def stop(self):
        self.hardware.stop()

    def forward(self, speed=15):
        self.hardware.forward(speed)

    def backward(self, speed=15):
        self.hardware.backward(speed)

    # ========================================================
    # STEERING
    # ========================================================

    def steering_center(self):
        self.hardware.steering_center()

    def steering_left(self, degrees=5):
        self.hardware.steering_left(degrees)

    def steering_right(self, degrees=5):
        self.hardware.steering_right(degrees)

    # ========================================================
    # ULTRASONIC PAN
    # ========================================================

    def look_center(self):
        self.hardware.ultrasonic_center()

    def look_left(self, degrees=5):
        self.hardware.ultrasonic_left(degrees)

    def look_right(self, degrees=5):
        self.hardware.ultrasonic_right(degrees)

    # ========================================================
    # ARM
    # ========================================================

    def arm_neutral(self):
        self.hardware.arm_neutral()

    def arm_front(self, degrees=5):
        self.hardware.arm_front(degrees)

    def arm_rear(self, degrees=5):
        self.hardware.arm_rear(degrees)

    # ========================================================
    # WRIST
    # ========================================================

    def wrist_neutral(self):
        self.hardware.wrist_neutral()

    def wrist_up(self, degrees=5):
        self.hardware.wrist_up(degrees)

    def wrist_down(self, degrees=5):
        self.hardware.wrist_down(degrees)

    # ========================================================
    # GRIPPER
    # ========================================================

    def gripper_open(self, degrees=5):
        self.hardware.gripper_open(degrees)

    def gripper_close(self):
        self.hardware.gripper_close()

    # ========================================================
    # LIGHTS
    # ========================================================

    def headlights_on(self):
        self.hardware.headlights_on()

    def headlights_off(self):
        self.hardware.headlights_off()

    # ========================================================
    # SENSORS
    # ========================================================

    def battery_voltage(self):
        return self.sensors.battery_voltage()

    def distance_cm(
    self,
    samples=7,
    delay=0.08,
    discard_first=2,
    ):
        return self.sensors.distance_cm(
          samples=samples,
          delay=delay,
         discard_first=discard_first,
        )

    def line_state(self):
        return self.sensors.line_state()

    def imu(self):
        return self.sensors.imu()

    def acceleration(self):
        return self.sensors.acceleration()

    def gyroscope(self):
        return self.sensors.gyroscope()

    def camera_frame(self):
        return self.sensors.camera_frame()

    # ========================================================
    # SAFE STATE / RESOURCE MANAGEMENT
    # ========================================================

    def neutral_pose(self):
        self.hardware.neutral_pose()

    def close(self):
        if self._closed:
            return

        self._closed = True

        try:
            self.hardware.shutdown()
        finally:
            self.sensors.close()

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        self.close()