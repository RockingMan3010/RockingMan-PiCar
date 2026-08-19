#!/usr/bin/env python3

import os
import struct
import sys
import time
from pathlib import Path

ADEEPT_SERVER = Path.home() / "Adeept_PiCar-Pro" / "Server"

if not ADEEPT_SERVER.is_dir():
    raise RuntimeError(
        f"Adeept Server directory not found: {ADEEPT_SERVER}"
    )

sys.path.insert(0, str(ADEEPT_SERVER))

import Move as move
import RPIservo

DEVICE = "/dev/input/js0"

MAX_SPEED = 35       # 0-100, first test deliberately low
MAX_STEER = 25       # degrees left/right from centre
DEADZONE = 0.12

# Linux joystick event types
JS_EVENT_BUTTON = 0x01
JS_EVENT_AXIS   = 0x02
JS_EVENT_INIT   = 0x80

# Xbox 360 left stick
AXIS_STEER = 0       # left stick X
AXIS_THROTTLE = 1    # left stick Y

axes = {
    AXIS_STEER: 0.0,
    AXIS_THROTTLE: 0.0,
}

def deadzone(v):
    if abs(v) < DEADZONE:
        return 0.0
    return v

def clamp(v, lo=-1.0, hi=1.0):
    return max(lo, min(hi, v))

move.setup()
steering = RPIservo.ServoCtrl()

# Safe initial state
move.motorStop()
steering.moveAngle(0, 0)

print("===================================")
print("   PiCar Direct Xbox RC READY 🎮")
print("===================================")
print("Left stick UP/DOWN : forward/reverse")
print("Left stick LEFT/RIGHT : steering")
print("Ctrl+C : EMERGENCY STOP")
print()

fd = os.open(DEVICE, os.O_RDONLY | os.O_NONBLOCK)

last_speed = None
last_direction = None
last_steer_angle = None

try:
    while True:
        # Read every queued controller event
        while True:
            try:
                data = os.read(fd, 8)
                if len(data) != 8:
                    raise RuntimeError("Controller disconnected")

                _, value, event_type, number = struct.unpack("IhBB", data)

                event_type &= ~JS_EVENT_INIT

                if event_type == JS_EVENT_AXIS and number in axes:
                    axes[number] = value / 32767.0

            except BlockingIOError:
                break

        steer = deadzone(clamp(axes[AXIS_STEER]))

        # Linux Xbox Y axis: UP is negative, so invert it
        throttle = deadzone(clamp(-axes[AXIS_THROTTLE]))

        # ----- Steering -----
        steer_angle = int(steer * MAX_STEER)

        if steer_angle != last_steer_angle:
            steering.moveAngle(0, steer_angle)
            last_steer_angle = steer_angle

        # ----- Motors -----
        speed = int(abs(throttle) * MAX_SPEED)

        if speed == 0:
            if last_speed != 0:
                move.motorStop()
            last_speed = 0
            last_direction = 0

        else:
            direction = 1 if throttle > 0 else -1

            if speed != last_speed or direction != last_direction:
                move.move(speed, direction, "no")

            last_speed = speed
            last_direction = direction

        print(
            f"\rThrottle {throttle:+.2f} | "
            f"Speed {speed:02d}% | "
            f"Steer {steer_angle:+03d}°   ",
            end="",
            flush=True,
        )

        time.sleep(0.02)

except KeyboardInterrupt:
    print("\n\nEmergency stop requested.")

except Exception as e:
    print(f"\n\nController error: {e}")

finally:
    move.motorStop()
    steering.moveAngle(0, 0)

    try:
        move.destroy()
    except Exception:
        pass

    os.close(fd)
    print("MOTORS STOPPED | STEERING CENTERED")
