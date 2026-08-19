import socket
import json
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

PORT = 5005
MAX_SPEED = 35
MAX_STEER = 25
WATCHDOG = 0.4

move.setup()
steering = RPIservo.ServoCtrl()

move.motorStop()
steering.moveAngle(0, 0)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", PORT))
sock.settimeout(0.05)

last_packet = time.monotonic()

print(f"PiCar RC server READY on UDP port {PORT}")
print("Ctrl+C = emergency stop")

def clamp(v):
    return max(-1.0, min(1.0, v))

try:
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            cmd = json.loads(data.decode())

            throttle = clamp(float(cmd.get("throttle", 0)))
            steer = clamp(float(cmd.get("steering", 0)))

            if abs(throttle) < 0.08:
                throttle = 0

            if abs(steer) < 0.08:
                steer = 0

            last_packet = time.monotonic()

            # Steering: right = positive, left = negative
            steering.moveAngle(0, steer * MAX_STEER)

            speed = int(abs(throttle) * MAX_SPEED)

            if speed == 0:
                move.motorStop()
            elif throttle > 0:
                move.move(speed, 1, "no")
            else:
                move.move(speed, -1, "no")

        except socket.timeout:
            if time.monotonic() - last_packet > WATCHDOG:
                move.motorStop()

except KeyboardInterrupt:
    print("\nEmergency stop")

finally:
    move.motorStop()
    steering.moveAngle(0, 0)
    sock.close()
    print("RC server stopped.")
