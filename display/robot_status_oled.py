#!/usr/bin/env python3

import socket
import subprocess
import time
import statistics
from collections import deque

import smbus
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306


# =========================================================
# OLED
# =========================================================

OLED_ADDRESS = 0x3C

serial = i2c(port=1, address=OLED_ADDRESS)
device = ssd1306(serial, rotate=0)


# =========================================================
# ADEEPT BATTERY MONITOR HARDWARE
# Based on Adeept Voltage.py
# =========================================================

ADC_ADDRESS = 0x48
ADC_CHANNEL = 0
ADC_CMD = 0x84

ADC_VREF = 4.93

R15 = 3000.0
R17 = 1000.0

DIVISION_RATIO = R17 / (R15 + R17)

bus = smbus.SMBus(1)


# =========================================================
# SETTINGS
# =========================================================

LOW_BATTERY_PERCENT = 10

# Prevent warning from flashing ON/OFF around exactly 10%
LOW_BATTERY_CLEAR_PERCENT = 12

READY_DISPLAY_TIME = 5.0
BATTERY_CHECK_INTERVAL = 3.0

samples = deque(maxlen=15)


# =========================================================
# OLED FUNCTIONS
# =========================================================

def clear_display():
    device.clear()


def draw_centered(draw, text, y):
    """
    Automatically center text horizontally
    on the 128 px wide OLED.
    """
    bbox = draw.textbbox((0, 0), text)
    text_width = bbox[2] - bbox[0]

    x = (device.width - text_width) // 2

    draw.text(
        (x, y),
        text,
        fill="white"
    )


def show_booting(voltage=None, percent=None):
    with canvas(device) as draw:

        draw_centered(draw, "ROCKINGMAN3010", 7)
        draw_centered(draw, "BOOTING...", 25)

        if percent is not None:
            draw_centered(
                draw,
                f"BATTERY: {percent}%",
                45
            )


def show_ready(ip_address, voltage, percent):
    with canvas(device) as draw:

        draw_centered(draw, "ROBOT READY", 3)
        draw_centered(draw, "SSH READY", 17)

        draw_centered(
            draw,
            f"IP: {ip_address}",
            32
        )

        draw_centered(
            draw,
            f"BATTERY: {percent}%",
            48
        )


def show_low_battery(percent, voltage):
    with canvas(device) as draw:

        # Sad face circle
        draw.ellipse(
            (5, 6, 55, 56),
            outline="white"
        )

        # Eyes
        draw.ellipse(
            (17, 21, 22, 26),
            fill="white"
        )

        draw.ellipse(
            (38, 21, 43, 26),
            fill="white"
        )

        # Sad mouth
        draw.arc(
            (17, 34, 44, 52),
            200,
            340,
            fill="white"
        )

        # Right side warning
        draw.text(
            (67, 10),
            "LOW",
            fill="white"
        )

        draw.text(
            (67, 22),
            "BATTERY",
            fill="white"
        )

        draw.text(
            (73, 38),
            f"{percent}%",
            fill="white"
        )

        draw.text(
            (67, 51),
            f"{voltage:.1f}V",
            fill="white"
        )


# =========================================================
# BATTERY FUNCTIONS
# =========================================================

def read_adc(channel=ADC_CHANNEL):
    command = ADC_CMD | (
        (((channel << 2 | channel >> 1) & 0x07) << 4)
    )

    return bus.read_byte_data(
        ADC_ADDRESS,
        command
    )


def read_battery_voltage():

    readings = []

    for _ in range(12):

        adc_value = read_adc()

        adc_voltage = (
            adc_value / 255.0
        ) * ADC_VREF

        battery_voltage = (
            adc_voltage / DIVISION_RATIO
        )

        readings.append(battery_voltage)

        time.sleep(0.03)

    # Median reduces noise/spikes
    voltage = statistics.median(readings)

    return voltage


def voltage_to_percent(voltage):
    """
    Approximate state-of-charge curve for the
    two-cell 18650 battery pack.

    This is NOT a precision fuel gauge.
    """

    curve = [
        (6.30,   0),
        (6.50,   5),
        (6.65,  10),
        (6.80,  15),
        (7.00,  25),
        (7.20,  40),
        (7.40,  50),
        (7.60,  60),
        (7.80,  70),
        (8.00,  80),
        (8.20,  90),
        (8.40, 100),
    ]

    if voltage <= curve[0][0]:
        return 0

    if voltage >= curve[-1][0]:
        return 100

    for index in range(len(curve) - 1):

        voltage_low, percent_low = curve[index]
        voltage_high, percent_high = curve[index + 1]

        if voltage_low <= voltage <= voltage_high:

            ratio = (
                (voltage - voltage_low)
                /
                (voltage_high - voltage_low)
            )

            percent = (
                percent_low
                +
                ratio * (percent_high - percent_low)
            )

            return round(percent)

    return 0


# =========================================================
# NETWORK / SSH FUNCTIONS
# =========================================================

def get_wifi_ip():

    try:
        result = subprocess.check_output(
            [
                "ip",
                "-4",
                "-o",
                "addr",
                "show",
                "wlan0"
            ],
            text=True
        )

        for line in result.splitlines():

            parts = line.split()

            if "inet" in parts:
                index = parts.index("inet")

                return (
                    parts[index + 1]
                    .split("/")[0]
                )

    except Exception:
        pass

    return None


def ssh_is_ready():

    # First check systemd
    result = subprocess.run(
        [
            "systemctl",
            "is-active",
            "--quiet",
            "ssh"
        ]
    )

    if result.returncode != 0:
        return False

    # Then verify port 22 really accepts connections
    try:

        with socket.create_connection(
            ("127.0.0.1", 22),
            timeout=0.5
        ):
            return True

    except OSError:
        return False


# =========================================================
# MAIN
# =========================================================

def main():

    print("Robot OLED status monitor started.")

    # -----------------------------------------------------
    # BOOT PHASE
    # -----------------------------------------------------

    last_boot_update = 0

    while True:

        now = time.monotonic()

        if now - last_boot_update >= 1:

            voltage = read_battery_voltage()
            percent = voltage_to_percent(voltage)

            show_booting(
                voltage,
                percent
            )

            print(
                f"Waiting for network/SSH | "
                f"{voltage:.2f} V | "
                f"{percent}%"
            )

            last_boot_update = now

        ip_address = get_wifi_ip()

        if ip_address and ssh_is_ready():
            break

        time.sleep(0.25)

    # -----------------------------------------------------
    # READY SCREEN
    # -----------------------------------------------------

    voltage = read_battery_voltage()
    percent = voltage_to_percent(voltage)

    print(
        f"SSH READY: {ip_address} | "
        f"Battery: {percent}% "
        f"({voltage:.2f} V)"
    )

    show_ready(
        ip_address,
        voltage,
        percent
    )

    time.sleep(READY_DISPLAY_TIME)

    clear_display()

    # -----------------------------------------------------
    # CONTINUOUS BATTERY MONITOR
    # -----------------------------------------------------

    low_battery_active = False

    while True:

        voltage = read_battery_voltage()
        percent = voltage_to_percent(voltage)

        print(
            f"Battery: {percent}% "
            f"({voltage:.2f} V)"
        )

        # Enter low-battery mode
        if percent <= LOW_BATTERY_PERCENT:

            low_battery_active = True

            show_low_battery(
                percent,
                voltage
            )

        # Leave warning only after battery recovers enough
        elif (
            low_battery_active
            and
            percent >= LOW_BATTERY_CLEAR_PERCENT
        ):

            low_battery_active = False

            clear_display()

        # Normal state = OLED stays blank
        elif not low_battery_active:

            clear_display()

        time.sleep(
            BATTERY_CHECK_INTERVAL
        )


if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:
        clear_display()
        print("\nOLED monitor stopped.")

    except Exception as error:
        clear_display()
        print(
            f"OLED monitor error: {error}"
        )
        raise