#!/usr/bin/env python3

import time
import statistics
from mpu6050 import mpu6050

ADDRESS = 0x68
SAMPLES = 20
DELAY = 0.1

sensor = mpu6050(ADDRESS)


def countdown(message, seconds=8):
    print()
    print(message)
    for n in range(seconds, 0, -1):
        print(f"Starting in {n:02d}s...", end="\r", flush=True)
        time.sleep(1)
    print()


def accel_sample(label):
    xs, ys, zs = [], [], []

    print(f"\n=== {label} ===")

    for i in range(SAMPLES):
        a = sensor.get_accel_data()

        xs.append(a["x"])
        ys.append(a["y"])
        zs.append(a["z"])

        print(
            f"[{i+1:02d}/{SAMPLES}] "
            f"X={a['x']:7.3f}  "
            f"Y={a['y']:7.3f}  "
            f"Z={a['z']:7.3f}"
        )

        time.sleep(DELAY)

    result = (
        statistics.mean(xs),
        statistics.mean(ys),
        statistics.mean(zs),
    )

    print(
        f"MEAN: X={result[0]:.3f}, "
        f"Y={result[1]:.3f}, "
        f"Z={result[2]:.3f}"
    )

    return result


def gyro_motion_test():
    print()
    print("=== GYRO MOTION TEST ===")
    print("Rotate the robot LEFT and RIGHT continuously for 5 seconds.")

    maxima = {"x": 0.0, "y": 0.0, "z": 0.0}

    start = time.time()

    while time.time() - start < 5:
        try:
            g = sensor.get_gyro_data()
        except AttributeError:
            print("This mpu6050 library has no get_gyro_data() method.")
            return None

        for axis in maxima:
            maxima[axis] = max(
                maxima[axis],
                abs(g[axis]),
            )

        print(
            f"GX={g['x']:8.2f} "
            f"GY={g['y']:8.2f} "
            f"GZ={g['z']:8.2f}",
            end="\r",
            flush=True,
        )

        time.sleep(0.05)

    print()
    print(
        f"MAX ABS GYRO: "
        f"X={maxima['x']:.2f}, "
        f"Y={maxima['y']:.2f}, "
        f"Z={maxima['z']:.2f}"
    )

    return maxima


def main():
    countdown(
        "Keep robot completely STILL on a flat surface."
    )
    flat = accel_sample("FLAT")

    countdown(
        "Now tilt and HOLD the robot noticeably forward or sideways."
    )
    tilted = accel_sample("TILTED")

    countdown(
        "Get ready to rotate the robot left/right during the next test.",
        5,
    )
    gyro = gyro_motion_test()

    delta = sum(
        abs(a - b)
        for a, b in zip(flat, tilted)
    )

    print()
    print("========== RESULT ==========")
    print(f"Accel orientation delta: {delta:.3f}")

    if gyro is not None:
        print(f"Gyro max values: {gyro}")

    print("============================")


if __name__ == "__main__":
    main()
