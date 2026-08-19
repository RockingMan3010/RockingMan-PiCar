#!/usr/bin/env python3

"""RockingMan PiCar-Pro integrated hardware self-test."""

import argparse
import json
import math
import statistics
import struct
import subprocess
import sys
import time
import wave
from datetime import datetime
from pathlib import Path

import cv2
import smbus
from gpiozero import InputDevice, TonalBuzzer
from mpu6050 import mpu6050

from hardware_profile import (
    ADS7830_ADDRESS,
    MPU6050_ADDRESS,
    OLED_ADDRESS,
    LINE_SENSOR_LEFT_GPIO,
    LINE_SENSOR_MIDDLE_GPIO,
    LINE_SENSOR_RIGHT_GPIO,
    USB_CAMERA_DEVICE,
    USB_MIC_ALSA_DEVICE,
    USB_MIC_SAMPLE_RATE,
    USB_MIC_CHANNELS,
    BUZZER_GPIO,
)

from robot_hardware import RockingManRobot


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".jarvis" / "self_test"
STATE_DIR.mkdir(parents=True, exist_ok=True)

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"
CMD_OK = "CMD_OK"


class SelfTest:
    def __init__(self, full=False):
        self.full = full
        self.results = []

    def record(self, name, status, detail=""):
        self.results.append(
            {
                "name": name,
                "status": status,
                "detail": detail,
            }
        )

        label = {
            PASS: "PASS",
            FAIL: "FAIL",
            WARN: "WARN",
            CMD_OK: "CMD ",
        }[status]

        print(f"[{label}] {name}: {detail}")

    def run_test(self, name, function):
        try:
            status, detail = function()
            self.record(name, status, detail)
        except Exception as exc:
            self.record(
                name,
                FAIL,
                f"{type(exc).__name__}: {exc}",
            )

    # ========================================================
    # OLED
    # ========================================================

    def oled_message(self, line1, line2="", line3=""):
        import board
        import busio
        import adafruit_ssd1306
        from PIL import Image, ImageDraw, ImageFont

        i2c = busio.I2C(board.SCL, board.SDA)

        try:
            oled = adafruit_ssd1306.SSD1306_I2C(
                128,
                32,
                i2c,
                addr=OLED_ADDRESS,
            )

            image = Image.new("1", (128, 32))
            draw = ImageDraw.Draw(image)
            font = ImageFont.load_default()

            draw.text((0, 0), line1[:21], font=font, fill=255)
            draw.text((0, 11), line2[:21], font=font, fill=255)
            draw.text((0, 22), line3[:21], font=font, fill=255)

            oled.image(image)
            oled.show()

        finally:
            try:
                i2c.deinit()
            except Exception:
                pass

    def test_oled(self):
        self.oled_message(
            "JARVIS SELF TEST",
            "OLED ONLINE",
            "Running...",
        )
        return PASS, "128x32 OLED responded at 0x3C"

    # ========================================================
    # BATTERY ADC
    # ========================================================

    def test_battery(self):
        adc_vref = 4.93
        division_ratio = 1000 / (3000 + 1000)
        cmd = 0x84
        channel = 0

        control = cmd | (
            ((channel << 2 | channel >> 1) & 0x07) << 4
        )

        bus = smbus.SMBus(1)
        voltages = []

        try:
            for _ in range(10):
                raw = bus.read_byte_data(
                    ADS7830_ADDRESS,
                    control,
                )

                adc_voltage = raw / 255.0 * adc_vref
                battery_voltage = (
                    adc_voltage / division_ratio
                )

                voltages.append(battery_voltage)
                time.sleep(0.05)

        finally:
            bus.close()

        median_v = statistics.median(voltages)

        if not 5.0 <= median_v <= 9.5:
            return (
                FAIL,
                f"implausible battery reading {median_v:.2f} V",
            )

        return PASS, f"{median_v:.2f} V"

    # ========================================================
    # ULTRASONIC
    # ========================================================

    def test_ultrasonic(self):
        vendor = Path.home() / "Adeept_PiCar-Pro" / "Server"
        sys.path.insert(0, str(vendor))

        import Ultra

        values = []

        try:
            time.sleep(0.5)

            for _ in range(7):
                values.append(Ultra.checkdist())
                time.sleep(0.12)

        finally:
            try:
                Ultra.sensor.close()
            except Exception:
                pass

        distance = statistics.median(values)

        if not 1.0 <= distance <= 200.0:
            return FAIL, f"out-of-range reading {distance:.2f} cm"

        return (
            PASS,
            f"{distance:.2f} cm "
            f"(range {min(values):.2f}-{max(values):.2f})",
        )

    # ========================================================
    # LINE SENSORS
    # ========================================================

    def test_line_sensors(self):
        left = InputDevice(LINE_SENSOR_LEFT_GPIO)
        middle = InputDevice(LINE_SENSOR_MIDDLE_GPIO)
        right = InputDevice(LINE_SENSOR_RIGHT_GPIO)

        try:
            samples = []

            for _ in range(10):
                state = (
                    int(left.value),
                    int(middle.value),
                    int(right.value),
                )
                samples.append(state)
                time.sleep(0.05)

        finally:
            left.close()
            middle.close()
            right.close()

        common = statistics.mode(samples)

        if any(value not in (0, 1) for value in common):
            return FAIL, f"invalid digital state {common}"

        return (
            PASS,
            f"GPIO readable; current L/M/R = {common}",
        )

    # ========================================================
    # MPU6050
    # ========================================================

    def test_mpu6050(self):
        sensor = mpu6050(MPU6050_ADDRESS)

        accel = sensor.get_accel_data()
        gyro = sensor.get_gyro_data()

        magnitude = math.sqrt(
            accel["x"] ** 2
            + accel["y"] ** 2
            + accel["z"] ** 2
        )

        if not all(
            math.isfinite(value)
            for value in (
                accel["x"],
                accel["y"],
                accel["z"],
                gyro["x"],
                gyro["y"],
                gyro["z"],
            )
        ):
            return FAIL, "non-finite MPU6050 data"

        if not 5.0 <= magnitude <= 15.0:
            return (
                WARN,
                f"accel magnitude unusual: {magnitude:.2f} m/s^2",
            )

        return (
            PASS,
            f"accel |g|={magnitude:.2f} m/s^2; gyro readable",
        )

    # ========================================================
    # USB CAMERA
    # ========================================================

    def test_camera(self):
        cap = cv2.VideoCapture(
            USB_CAMERA_DEVICE,
            cv2.CAP_V4L2,
        )

        if not cap.isOpened():
            return FAIL, "/dev/video0 could not be opened"

        valid = 0
        last_frame = None

        try:
            for _ in range(8):
                ok, frame = cap.read()

                if ok and frame is not None:
                    valid += 1
                    last_frame = frame

                time.sleep(0.05)

        finally:
            cap.release()

        if last_frame is None:
            return FAIL, "camera opened but returned no frames"

        height, width = last_frame.shape[:2]

        return (
            PASS,
            f"{valid}/8 frames valid at {width}x{height}",
        )

    # ========================================================
    # MICROPHONE
    # ========================================================

    def test_microphone(self):
        wav_path = STATE_DIR / "mic_self_test.wav"

        command = [
            "arecord",
            "-q",
            "-D",
            USB_MIC_ALSA_DEVICE,
            "-f",
            "S16_LE",
            "-r",
            str(USB_MIC_SAMPLE_RATE),
            "-c",
            str(USB_MIC_CHANNELS),
            "-d",
            "2",
            str(wav_path),
        ]

        subprocess.run(
            command,
            check=True,
            timeout=6,
        )

        with wave.open(str(wav_path), "rb") as wav:
            frame_count = wav.getnframes()
            frames = wav.readframes(frame_count)

        if not frames:
            return FAIL, "recording contained no audio frames"

        samples = struct.unpack(
            "<" + "h" * (len(frames) // 2),
            frames,
        )

        peak = max(abs(sample) for sample in samples)

        rms = math.sqrt(
            sum(sample * sample for sample in samples)
            / len(samples)
        )

        if peak == 0:
            return FAIL, "audio stream is digital silence"

        peak_percent = peak / 32767 * 100

        detail = (
            f"{frame_count} samples; "
            f"RMS={rms:.0f}; peak={peak_percent:.1f}%"
        )

        if peak_percent >= 99.5:
            return WARN, detail + " (clipping detected)"

        return PASS, detail

    # ========================================================
    # ACTUATOR COMMAND PATH
    # ========================================================

    def test_actuators(self):
        robot = RockingManRobot()

        try:
            robot.steering_center()
            time.sleep(0.3)

            robot.steering_left(5)
            time.sleep(0.4)

            robot.steering_right(5)
            time.sleep(0.4)

            robot.steering_center()
            self.record(
                "Steering command path",
                CMD_OK,
                "left/right/center issued",
            )

            robot.ultrasonic_left(5)
            time.sleep(0.4)

            robot.ultrasonic_right(5)
            time.sleep(0.4)

            robot.ultrasonic_center()
            self.record(
                "Ultrasonic pan command path",
                CMD_OK,
                "left/right/center issued",
            )

            robot.arm_front(5)
            time.sleep(0.4)

            robot.arm_rear(5)
            time.sleep(0.4)

            robot.arm_neutral()
            self.record(
                "Arm command path",
                CMD_OK,
                "front/rear/neutral issued",
            )

            robot.wrist_up(5)
            time.sleep(0.4)

            robot.wrist_down(5)
            time.sleep(0.4)

            robot.wrist_neutral()
            self.record(
                "Wrist command path",
                CMD_OK,
                "up/down/neutral issued",
            )

            robot.gripper_open(5)
            time.sleep(0.5)

            robot.gripper_close()
            self.record(
                "Gripper command path",
                CMD_OK,
                "open/safe-close issued",
            )

            robot.headlights_on()
            time.sleep(0.7)

            robot.headlights_off()
            self.record(
                "Headlight command path",
                CMD_OK,
                "left + right ON/OFF issued",
            )

            robot.neutral_pose()

        finally:
            robot.shutdown()

    # ========================================================
    # RGB
    # ========================================================

    def test_rgb(self):
        vendor = Path.home() / "Adeept_PiCar-Pro" / "Server"
        sys.path.insert(0, str(vendor))

        import RobotLight

        led = RobotLight.Adeept_SPI_LedPixel(
            count=8,
            bright=20,
            bus=0,
            device=0,
        )

        try:
            if led.check_spi_state() == 0:
                return FAIL, "SPI LED controller unavailable"

            led.set_all_led_color(0, 80, 0)
            time.sleep(0.5)

            led.set_all_led_color(0, 0, 80)
            time.sleep(0.5)

            led.set_all_led_color(0, 0, 0)

        finally:
            try:
                led.led_close()
            except Exception:
                pass

        return CMD_OK, "green/blue/off commands issued"

    # ========================================================
    # BUZZER
    # ========================================================

    def test_buzzer(self):
        buzzer = TonalBuzzer(BUZZER_GPIO)

        try:
            buzzer.play("C4")
            time.sleep(0.18)
            buzzer.stop()

            time.sleep(0.1)

            buzzer.play("G4")
            time.sleep(0.18)
            buzzer.stop()

        finally:
            buzzer.close()

        return CMD_OK, "C4/G4 tone commands issued"

    # ========================================================
    # REPORTING
    # ========================================================

    def save_report(self):
        timestamp = datetime.now().astimezone()

        report = {
            "timestamp": timestamp.isoformat(),
            "mode": "full" if self.full else "quick",
            "results": self.results,
        }

        filename = (
            "self_test_"
            + timestamp.strftime("%Y%m%d_%H%M%S")
            + ".json"
        )

        path = STATE_DIR / filename

        path.write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )

        return path

    def final_summary(self):
        failures = [
            result
            for result in self.results
            if result["status"] == FAIL
        ]

        warnings = [
            result
            for result in self.results
            if result["status"] == WARN
        ]

        total = len(self.results)
        healthy = total - len(failures)

        print()
        print("=" * 60)
        print("JARVIS HARDWARE SELF TEST")
        print("=" * 60)

        for result in self.results:
            print(
                f"{result['status']:6s} | "
                f"{result['name']:<30s} | "
                f"{result['detail']}"
            )

        print("=" * 60)
        print(
            f"Healthy checks : {healthy}/{total}"
        )
        print(
            f"Warnings       : {len(warnings)}"
        )
        print(
            f"Failures       : {len(failures)}"
        )

        if failures:
            status_text = "FAULT"
        elif warnings:
            status_text = "HEALTHY/WARN"
        else:
            status_text = "HEALTHY"

        print(f"SYSTEM STATUS  : {status_text}")
        print("=" * 60)

        try:
            self.oled_message(
                "JARVIS SELF TEST",
                f"{healthy}/{total} CHECKS OK",
                status_text,
            )
        except Exception:
            pass

        return not failures

    # ========================================================
    # RUN
    # ========================================================

    def run(self):
        print()
        print("RockingMan PiCar-Pro")
        print("JARVIS Hardware Self-Test")
        print(
            f"Mode: {'FULL' if self.full else 'QUICK'}"
        )
        print()

        self.run_test(
            "OLED",
            self.test_oled,
        )

        self.run_test(
            "Battery ADC",
            self.test_battery,
        )

        self.run_test(
            "Ultrasonic distance",
            self.test_ultrasonic,
        )

        self.run_test(
            "Line sensor GPIO",
            self.test_line_sensors,
        )

        self.run_test(
            "MPU6050",
            self.test_mpu6050,
        )

        self.run_test(
            "USB camera",
            self.test_camera,
        )

        self.run_test(
            "USB microphone",
            self.test_microphone,
        )

        if self.full:
            print()
            print("Running safe actuator command tests...")
            print()

            try:
                self.test_actuators()
            except Exception as exc:
                self.record(
                    "Actuator command suite",
                    FAIL,
                    f"{type(exc).__name__}: {exc}",
                )

            self.run_test(
                "WS2812 RGB",
                self.test_rgb,
            )

            self.run_test(
                "Buzzer",
                self.test_buzzer,
            )

        report_path = self.save_report()
        healthy = self.final_summary()

        print()
        print(f"Report: {report_path}")

        return 0 if healthy else 1


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--full",
        action="store_true",
        help=(
            "also perform physically safe actuator, "
            "headlight, RGB and buzzer command tests"
        ),
    )

    args = parser.parse_args()

    suite = SelfTest(full=args.full)
    raise SystemExit(suite.run())


if __name__ == "__main__":
    main()
