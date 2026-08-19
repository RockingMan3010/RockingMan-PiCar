"""Verified hardware profile for RockingMan PiCar-Pro.

Values in this file come from physical hardware validation performed
on the assembled robot, not merely from vendor documentation.
"""

# ============================================================
# DRIVE
# ============================================================

LEFT_MOTOR = 1
RIGHT_MOTOR = 2

# Adeept Move.py interpretation validated physically:
# move(speed, 1, ...) drives both wheels forward.
FORWARD_DIRECTION = 1
BACKWARD_DIRECTION = -1


# ============================================================
# SERVOS
# ============================================================

STEERING_CHANNEL = 0
ULTRASONIC_PAN_CHANNEL = 1
ARM_CHANNEL = 2
WRIST_CHANNEL = 3
GRIPPER_CHANNEL = 4

# Conservative ranges physically validated so far.
ULTRASONIC_PAN_MAX_SAFE_OFFSET = 5
ARM_MAX_SAFE_OFFSET = 5
WRIST_MAX_SAFE_OFFSET = 5
GRIPPER_MAX_SAFE_OPEN = 5


# Steering calibration
#
# Vendor nominal center = relative 0
# Physical chassis center = relative -5

STEERING_CENTER = -5

# Physically validated steering range around calibrated center.
STEERING_MAX_SAFE_OFFSET = 15

# Verified steering direction:
# negative -> left
# positive -> right
STEERING_LEFT_SIGN = -1
STEERING_RIGHT_SIGN = 1


# Ultrasonic pan:
# negative -> robot right
# positive -> robot left
ULTRASONIC_RIGHT_SIGN = -1
ULTRASONIC_LEFT_SIGN = 1


# Arm:
# negative -> robot rear
# positive -> robot front
ARM_REAR_SIGN = -1
ARM_FRONT_SIGN = 1


# Wrist:
# negative -> toward ground
# positive -> upward
WRIST_DOWN_SIGN = -1
WRIST_UP_SIGN = 1


# Gripper:
#
# relative 0 = comfortably closed
# negative values attempt to close beyond the safe neutral position
# and should therefore be avoided.
#
# positive values open the gripper.
GRIPPER_CLOSED = 0
GRIPPER_OPEN_SIGN = 1
GRIPPER_MIN_SAFE = 0


# ============================================================
# HEADLIGHTS / SWITCH OUTPUTS
# ============================================================

# Adeept Switch ports, physically verified.
SWITCH_PORT_UNIDENTIFIED = 1
LEFT_HEADLIGHT_SWITCH = 2
RIGHT_HEADLIGHT_SWITCH = 3


# ============================================================
# LINE SENSORS
# ============================================================

LINE_SENSOR_LEFT_GPIO = 22
LINE_SENSOR_MIDDLE_GPIO = 27
LINE_SENSOR_RIGHT_GPIO = 17

# Physically validated:
LINE_WHITE_STATE = 1
LINE_BLACK_STATE = 0


# ============================================================
# ULTRASONIC
# ============================================================

ULTRASONIC_TRIGGER_GPIO = 23
ULTRASONIC_ECHO_GPIO = 24
ULTRASONIC_MAX_DISTANCE_M = 2.0


# ============================================================
# BUZZER
# ============================================================

BUZZER_GPIO = 18


# ============================================================
# I2C HARDWARE
# ============================================================

PCA9685_ADDRESS = 0x5F
ADS7830_ADDRESS = 0x48
MPU6050_ADDRESS = 0x68
OLED_ADDRESS = 0x3C


# ============================================================
# AUDIO / VIDEO
# ============================================================

USB_CAMERA_DEVICE = 0

USB_MIC_ALSA_DEVICE = "plughw:CARD=WebCamera,DEV=0"
USB_MIC_SAMPLE_RATE = 16000
USB_MIC_CHANNELS = 1
