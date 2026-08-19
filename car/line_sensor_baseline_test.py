#!/usr/bin/env python3

import time
from collections import Counter
from gpiozero import InputDevice

LEFT_PIN = 22
MIDDLE_PIN = 27
RIGHT_PIN = 17

left = InputDevice(LEFT_PIN)
middle = InputDevice(MIDDLE_PIN)
right = InputDevice(RIGHT_PIN)

SAMPLES = 20


def countdown(message, seconds=10):
    print()
    print(message)

    for n in range(seconds, 0, -1):
        print(f"Reading in {n:02d}s...", end="\r", flush=True)
        time.sleep(1)

    print()


def capture(label):
    readings = []

    print(f"\n=== {label} ===")

    for i in range(SAMPLES):
        state = (
            left.value,
            middle.value,
            right.value,
        )

        readings.append(state)

        print(
            f"[{i+1:02d}/{SAMPLES}] "
            f"L={state[0]}  "
            f"M={state[1]}  "
            f"R={state[2]}"
        )

        time.sleep(0.1)

    common = Counter(readings).most_common(1)[0]

    print(
        f"Most common state: "
        f"L={common[0][0]} "
        f"M={common[0][1]} "
        f"R={common[0][2]} "
        f"({common[1]}/{SAMPLES} samples)"
    )

    return common[0]


try:
    countdown(
        "Place ALL THREE line sensors over a WHITE surface."
    )
    white = capture("WHITE")

    countdown(
        "Now place ALL THREE sensors over BLACK tape / dark surface."
    )
    black = capture("BLACK")

    print()
    print("========== RESULT ==========")
    print(f"WHITE = {white}")
    print(f"BLACK = {black}")
    print(f"Different states = {white != black}")
    print("============================")

finally:
    left.close()
    middle.close()
    right.close()
