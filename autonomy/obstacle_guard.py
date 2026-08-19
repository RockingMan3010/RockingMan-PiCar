#!/usr/bin/env python3

import time

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
CAR_DIR = ROOT / "car"

sys.path.insert(0, str(CAR_DIR))

from robot import Robot


STOP_DISTANCE_CM = 25.0
DRIVE_SPEED = 12
LOOP_DELAY = 0.12


def main():
    print()
    print("RockingMan Obstacle Guard v1")
    print("=" * 50)
    print(f"Stop distance : {STOP_DISTANCE_CM:.1f} cm")
    print(f"Drive speed   : {DRIVE_SPEED}")
    print()

    with Robot() as robot:
        robot.steering_center()
        robot.look_center()

        print("Starting slow forward motion...")

        try:
            robot.forward(DRIVE_SPEED)

            while True:
                distance = robot.distance_cm(
                samples=5,
                delay=0.04,
                discard_first=0,
            )

                print(
                    f"Distance: {distance:6.2f} cm",
                    end="\r",
                    flush=True,
                )

                if distance <= STOP_DISTANCE_CM:
                    robot.stop()

                    print()
                    print()
                    print(
                        f"OBSTACLE DETECTED: "
                        f"{distance:.2f} cm"
                    )
                    print("ROBOT STOPPED.")
                    break

                time.sleep(LOOP_DELAY)

        except KeyboardInterrupt:
            print()
            print("Manual stop requested.")

        except Exception as exc:
            print()
            print(
                f"Sensor/control error: "
                f"{type(exc).__name__}: {exc}"
            )

        finally:
            robot.stop()
            print("Drive motors safe.")


if __name__ == "__main__":
    main()