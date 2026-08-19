"""Calibrated chassis configuration for RockingMan PiCar-Pro."""

# Adeept steering servo
STEERING_SERVO_CHANNEL = 0

# Experimentally calibrated on 2026-08-19.
# Adeept's nominal center (0 relative offset) left the wheels slightly right.
STEERING_CENTER_OFFSET = -5

# Official control range is roughly ±30 degrees.
STEERING_MAX_LEFT = -30
STEERING_MAX_RIGHT = 30
