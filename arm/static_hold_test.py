#!/usr/bin/env python3

import time
import busio
from board import SCL, SDA
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

SERVO_ID = 2

i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c, address=0x5F)
pca.frequency = 50

s = servo.Servo(
    pca.channels[SERVO_ID],
    min_pulse=500,
    max_pulse=2400,
    actuation_range=180
)

try:
    print("90° centre - observe for 10 sec")
    s.angle = 90
    time.sleep(10)

    print("110° - observe for 10 sec")
    s.angle = 110
    time.sleep(10)

    print("90° centre - observe for 10 sec")
    s.angle = 90
    time.sleep(10)

finally:
    pca.deinit()
    i2c.deinit()
