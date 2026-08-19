#!/usr/bin/env python3

import time
from pathlib import Path

import cv2


CAMERA_DEVICE = 0
REQUESTED_WIDTH = 640
REQUESTED_HEIGHT = 480

WARMUP_FRAMES = 10
TEST_FRAMES = 20

OUTPUT = (
    Path.home()
    / "RockingMan-PiCar"
    / "artifacts"
    / "camera"
    / "camera_baseline.jpg"
)


def main():
    print("Opening USB camera /dev/video0...")

    cap = cv2.VideoCapture(
        CAMERA_DEVICE,
        cv2.CAP_V4L2,
    )

    if not cap.isOpened():
        raise RuntimeError(
            "Could not open /dev/video0"
        )

    cap.set(
        cv2.CAP_PROP_FRAME_WIDTH,
        REQUESTED_WIDTH,
    )
    cap.set(
        cv2.CAP_PROP_FRAME_HEIGHT,
        REQUESTED_HEIGHT,
    )

    try:
        print("Warming up camera...")

        for _ in range(WARMUP_FRAMES):
            cap.read()
            time.sleep(0.05)

        good_frames = 0
        last_frame = None

        print()
        print("Capturing test frames...")

        for i in range(TEST_FRAMES):
            ok, frame = cap.read()

            if ok and frame is not None:
                good_frames += 1
                last_frame = frame

                h, w = frame.shape[:2]

                print(
                    f"[{i+1:02d}/{TEST_FRAMES}] "
                    f"OK  {w}x{h}"
                )

            else:
                print(
                    f"[{i+1:02d}/{TEST_FRAMES}] FAILED"
                )

            time.sleep(0.05)

        if last_frame is None:
            raise RuntimeError(
                "Camera opened but no valid frame was received."
            )

        OUTPUT.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        saved = cv2.imwrite(
            str(OUTPUT),
            last_frame,
        )

        if not saved:
            raise RuntimeError(
                f"Could not save image: {OUTPUT}"
            )

        h, w = last_frame.shape[:2]
        brightness = float(
            cv2.cvtColor(
                last_frame,
                cv2.COLOR_BGR2GRAY,
            ).mean()
        )

        print()
        print("========== RESULT ==========")
        print(
            f"Valid frames : "
            f"{good_frames}/{TEST_FRAMES}"
        )
        print(f"Resolution   : {w}x{h}")
        print(f"Brightness   : {brightness:.1f}/255")
        print(f"Saved image  : {OUTPUT}")
        print("============================")

    finally:
        cap.release()
        print("Camera released.")


if __name__ == "__main__":
    main()
