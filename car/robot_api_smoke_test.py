#!/usr/bin/env python3

import time

from robot import Robot


def main():
    print()
    print("RockingMan Unified Robot API")
    print("=" * 50)

    with Robot() as robot:

        print(f"Battery  : {robot.battery_voltage():.3f} V")
        print(f"Distance : {robot.distance_cm():.2f} cm")

        line = robot.line_state()

        print(
            f"Line     : "
            f"L={line.left} "
            f"M={line.middle} "
            f"R={line.right}"
        )

        imu = robot.imu()

        print(
            f"IMU |g|  : "
            f"{imu.acceleration_magnitude:.3f} m/s^2"
        )

        print("Look left")
        robot.look_left()
        time.sleep(0.5)

        print("Look right")
        robot.look_right()
        time.sleep(0.5)

        print("Look center")
        robot.look_center()

        print("Headlights on")
        robot.headlights_on()
        time.sleep(1)

        print("Headlights off")
        robot.headlights_off()

        robot.neutral_pose()

    print("=" * 50)
    print("Unified Robot API test complete.")
    print()


if __name__ == "__main__":
    main()