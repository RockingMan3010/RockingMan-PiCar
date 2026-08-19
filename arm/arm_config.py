# RockingMan PiCar-Pro V2
# Arm calibration values

SERVO_BASE = 1
SERVO_ARM = 2
SERVO_WRIST = 3
SERVO_GRIPPER = 4

# Physically tested safe limits
BASE_MIN = -70
BASE_MAX = 70

ARM_MIN = -80
ARM_MAX = 80

WRIST_MIN = -56
WRIST_MAX = 90

GRIPPER_CLOSED = 2
GRIPPER_OPEN = 70


# Recommended everyday operating limits
# Slight margin from physical limits to reduce strain.

BASE_WORK_MIN = -65
BASE_WORK_MAX = 65

ARM_WORK_MIN = -75
ARM_WORK_MAX = 75

WRIST_WORK_MIN = -50
WRIST_WORK_MAX = 85

GRIPPER_WORK_CLOSED = 5
GRIPPER_WORK_OPEN = 65
