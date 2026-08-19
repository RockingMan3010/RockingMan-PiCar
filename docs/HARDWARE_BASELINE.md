# RockingMan PiCar-Pro Hardware Baseline

Verified on the physically assembled Adeept PiCar-Pro V2.0 running on a
Raspberry Pi 5.

This document records observed hardware behaviour rather than relying only
on vendor documentation.

## Baseline status

Integrated JARVIS self-test results:

- Quick self-test: 7/7 healthy
- Full self-test: 15/15 healthy
- Repeated full runs completed with:
  - 0 failures
  - 0 warnings
  - SYSTEM STATUS: HEALTHY

Runtime self-test reports are stored under:

`.jarvis/self_test/`

These reports are intentionally not committed to Git.

## Drive

- M1 = left drive motor
- M2 = right drive motor
- Adeept forward command drives both wheels physically forward

## Steering

Servo channel:

`CH0`

Observed direction:

- negative offset = left
- positive offset = right

Physical straight-ahead calibration:

`-5 degrees relative to Adeept nominal center`

## Servo mapping

### CH1 - Ultrasonic pan

- -5 degrees = robot right
- +5 degrees = robot left
- 0 = center

### CH2 - Arm tilt

- -5 degrees = toward robot rear
- +5 degrees = toward robot front
- 0 = neutral

### CH3 - Wrist

- -5 degrees = toward ground
- +5 degrees = upward
- 0 = neutral

### CH4 - Gripper / camera mount

- 0 = comfortably closed
- +5 degrees = slightly open
- negative movement from neutral attempts to close beyond the comfortable
  mechanical position

Safety rule:

Do not command CH4 below the verified neutral position until a safe
mechanical range has been calibrated.

## Ultrasonic sensor

- Trigger GPIO: 23
- Echo GPIO: 24
- Maximum configured range: 2 m
- Distance response validated at approximately 20 cm, 50 cm and 100 cm

Representative measurements:

- target 20 cm -> 18.27 cm
- target 50 cm -> 47.93 cm
- target 100 cm -> 97.08 cm

Integrated self-test readings were approximately 31.8-33.1 cm for the
test scene used during repeated runs.

## Line sensors

GPIO mapping:

- Left: GPIO22
- Middle: GPIO27
- Right: GPIO17

Physical validation:

- white surface = 1
- black surface = 0

All three sensors produced stable 20/20 readings during white/black testing.

## MPU6050

I2C address:

`0x68`

Validated:

- accelerometer responds to physical tilt
- gyroscope responds to physical rotation
- stationary acceleration magnitude remains close to gravity

Repeated integrated self-test values were approximately:

`9.72-9.80 m/s^2`

## OLED

- Resolution: 128x32
- I2C address: 0x3C
- Display output validated

## Battery monitoring

ADC:

- ADS7830
- I2C address: 0x48

Initial finite validation:

- median: 7.501 V
- mean: 7.532 V

Later integrated self-test:

- approximately 7.27 V

## USB camera

Device:

`/dev/video0`

Validated OpenCV capture:

- 640x480
- repeated self-tests: 8/8 frames valid

## USB microphone

ALSA device:

`plughw:CARD=WebCamera,DEV=0`

Configuration:

- mono
- 16-bit PCM
- 16000 Hz

Integrated self-test successfully records and analyzes the microphone signal.

## Headlights

Adeept switch mapping:

- Switch 1: no visible physical output identified
- Switch 2: left headlight
- Switch 3: right headlight

Switch 1 remains intentionally undocumented beyond this observation.

## WS2812 RGB

SPI-controlled RGB LEDs successfully validated with multiple colors and
off-state commands.

## Buzzer

GPIO:

`18`

Multiple tone commands successfully validated.

## Self-test semantics

`PASS`

Means software received objective sensor/data feedback sufficient to verify
that subsystem's basic operation.

`CMD_OK`

Means the software successfully issued a validated, physically safe command
to an open-loop actuator. It does not imply independent positional feedback.

This distinction must be preserved in future diagnostics.

## Known baseline constraints

- Non-steering servo motion has only been intentionally validated within
  conservative small offsets so far.
- CH4 must not be commanded further closed than its safe neutral position.
- Switch port 1 currently has no identified visible output.
- Ultrasonic gpiozero currently reports PWMSoftwareFallback during testing.
  This is tracked as a non-fatal runtime warning for future optimization.