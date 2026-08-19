#!/usr/bin/env python3

from robot_sensors import RobotSensors


def main():
    print()
    print("RockingMan Sensor API Smoke Test")
    print("=" * 50)

    with RobotSensors() as sensors:

        voltage = sensors.battery_voltage()
        print(f"Battery    : {voltage:.3f} V")

        distance = sensors.distance_cm()
        print(f"Distance   : {distance:.2f} cm")

        line = sensors.line_state()
        print(
            f"Line       : "
            f"L={line.left} "
            f"M={line.middle} "
            f"R={line.right}"
        )

        print(
            f"All white  : {line.all_white}"
        )

        print(
            f"All black  : {line.all_black}"
        )

        imu = sensors.imu()

        print(
            f"Accel      : "
            f"X={imu.accel_x:.3f} "
            f"Y={imu.accel_y:.3f} "
            f"Z={imu.accel_z:.3f}"
        )

        print(
            f"Accel |g|  : "
            f"{imu.acceleration_magnitude:.3f} m/s^2"
        )

        print(
            f"Gyro       : "
            f"X={imu.gyro_x:.2f} "
            f"Y={imu.gyro_y:.2f} "
            f"Z={imu.gyro_z:.2f}"
        )

        width, height = sensors.camera_resolution()

        print(
            f"Camera     : {width}x{height}"
        )

    print("=" * 50)
    print("Sensor API smoke test complete.")
    print()


if __name__ == "__main__":
    main()