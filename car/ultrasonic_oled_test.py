#!/usr/bin/env python3

import sys
import time
from pathlib import Path
from statistics import median

from PIL import Image, ImageDraw, ImageFont
import board
import busio


# ---------------------------------------------------------
# Adeept vendor dependency
# ---------------------------------------------------------

ADEEPT_SERVER = Path.home() / "Adeept_PiCar-Pro" / "Server"

if not ADEEPT_SERVER.is_dir():
    raise RuntimeError(
        f"Adeept Server directory not found: {ADEEPT_SERVER}"
    )

sys.path.insert(0, str(ADEEPT_SERVER))

import Ultra as ultra


# ---------------------------------------------------------
# OLED detection / backend
# ---------------------------------------------------------

WIDTH = 128


def detect_oled_height():
    oled_source = ADEEPT_SERVER / "OLED.py"

    try:
        text = oled_source.read_text(errors="ignore").lower()

        if "128_64" in text or "height = 64" in text or "height=64" in text:
            return 64

        if "128_32" in text or "height = 32" in text or "height=32" in text:
            return 32

    except Exception:
        pass

    return 32


HEIGHT = detect_oled_height()

i2c = busio.I2C(board.SCL, board.SDA)


def scan_i2c():
    while not i2c.try_lock():
        time.sleep(0.01)

    try:
        return i2c.scan()
    finally:
        i2c.unlock()


devices = scan_i2c()

if 0x3C in devices:
    OLED_ADDR = 0x3C
elif 0x3D in devices:
    OLED_ADDR = 0x3D
else:
    raise RuntimeError(
        "OLED not found at 0x3C or 0x3D. "
        f"I2C devices found: {[hex(x) for x in devices]}"
    )


class OLEDDisplay:
    def __init__(self):
        self.backend = None
        self.device = None

        try:
            import adafruit_ssd1306

            self.device = adafruit_ssd1306.SSD1306_I2C(
                WIDTH,
                HEIGHT,
                i2c,
                addr=OLED_ADDR,
            )

            self.backend = "circuitpython"

        except ImportError:
            import Adafruit_SSD1306

            if HEIGHT == 64:
                self.device = Adafruit_SSD1306.SSD1306_128_64(
                    rst=None,
                    i2c_address=OLED_ADDR,
                )
            else:
                self.device = Adafruit_SSD1306.SSD1306_128_32(
                    rst=None,
                    i2c_address=OLED_ADDR,
                )

            self.device.begin()
            self.backend = "legacy"

        self.clear()

    def show_image(self, image):
        self.device.image(image)

        if self.backend == "circuitpython":
            self.device.show()
        else:
            self.device.display()

    def clear(self):
        image = Image.new("1", (WIDTH, HEIGHT))
        self.show_image(image)


oled = OLEDDisplay()


# ---------------------------------------------------------
# Fonts
# ---------------------------------------------------------

FONT_REGULAR_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


if HEIGHT >= 64:
    FONT_SMALL = load_font(FONT_REGULAR_PATH, 12)
    FONT_TITLE = load_font(FONT_BOLD_PATH, 14)
    FONT_BIG = load_font(FONT_BOLD_PATH, 28)
else:
    FONT_SMALL = load_font(FONT_REGULAR_PATH, 9)
    FONT_TITLE = load_font(FONT_BOLD_PATH, 10)
    FONT_BIG = load_font(FONT_BOLD_PATH, 18)


# ---------------------------------------------------------
# OLED graphics
# ---------------------------------------------------------

def new_canvas():
    image = Image.new("1", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    return image, draw


def show_countdown(target_cm, seconds):
    image, draw = new_canvas()

    draw.text(
        (2, 0),
        f"TARGET: {target_cm} cm",
        font=FONT_TITLE,
        fill=255,
    )

    if HEIGHT >= 64:
        draw.text(
            (30, 24),
            f"{seconds:02d}",
            font=FONT_BIG,
            fill=255,
        )
        draw.text(
            (6, 53),
            "Place object...",
            font=FONT_SMALL,
            fill=255,
        )
    else:
        draw.text(
            (77, 11),
            f"{seconds:02d}",
            font=FONT_BIG,
            fill=255,
        )
        draw.text(
            (2, 17),
            "Place object",
            font=FONT_SMALL,
            fill=255,
        )

    oled.show_image(image)


def show_measuring(target_cm):
    image, draw = new_canvas()

    draw.text(
        (2, 0),
        f"{target_cm} cm",
        font=FONT_TITLE,
        fill=255,
    )

    draw.text(
        (2, HEIGHT // 2),
        "MEASURING...",
        font=FONT_TITLE,
        fill=255,
    )

    oled.show_image(image)


def draw_thumb(draw, x, y):
    # Simple monochrome thumbs-up icon.
    draw.rectangle((x + 8, y + 8, x + 15, y + 20), outline=255, fill=255)
    draw.rectangle((x + 15, y + 5, x + 19, y + 20), outline=255, fill=255)

    draw.polygon(
        [
            (x + 15, y + 7),
            (x + 18, y + 1),
            (x + 21, y + 1),
            (x + 22, y + 4),
            (x + 20, y + 8),
        ],
        fill=255,
    )

    draw.rectangle(
        (x + 20, y + 8, x + 31, y + 20),
        outline=255,
        fill=255,
    )


def show_recorded(target_cm, measured_cm):
    image, draw = new_canvas()

    draw.text(
        (2, 0),
        "RECORDED",
        font=FONT_TITLE,
        fill=255,
    )

    draw.text(
        (2, HEIGHT // 2),
        f"{measured_cm:.1f} cm",
        font=FONT_TITLE,
        fill=255,
    )

    thumb_y = max(1, (HEIGHT - 24) // 2)
    draw_thumb(draw, 92, thumb_y)

    oled.show_image(image)


def show_done():
    image, draw = new_canvas()

    draw.text(
        (2, 0),
        "ULTRA TEST",
        font=FONT_TITLE,
        fill=255,
    )

    draw.text(
        (2, HEIGHT // 2),
        "ALL DONE",
        font=FONT_TITLE,
        fill=255,
    )

    draw_thumb(
        draw,
        92,
        max(1, (HEIGHT - 24) // 2),
    )

    oled.show_image(image)


# ---------------------------------------------------------
# Ultrasonic test
# ---------------------------------------------------------

TARGETS = [20, 50, 100]
PREP_SECONDS = 20
SAMPLE_COUNT = 9
SAMPLE_DELAY = 0.25


def capture_distance(target_cm):
    print()
    print(f"TARGET {target_cm} cm")

    for remaining in range(PREP_SECONDS, 0, -1):
        show_countdown(target_cm, remaining)
        print(f"  countdown: {remaining:02d}s", end="\r", flush=True)
        time.sleep(1)

    print()
    show_measuring(target_cm)

    values = []

    for i in range(SAMPLE_COUNT):
        value = ultra.checkdist()
        values.append(value)

        print(
            f"  sample {i + 1}/{SAMPLE_COUNT}: "
            f"{value:.2f} cm"
        )

        time.sleep(SAMPLE_DELAY)

    result = median(values)

    print(
        f"  MEDIAN = {result:.2f} cm "
        f"(min={min(values):.2f}, max={max(values):.2f})"
    )

    show_recorded(target_cm, result)

    # Gives you time to see the thumbs-up.
    time.sleep(4)

    return result


def main():
    results = {}

    print("OLED ultrasonic test starting.")
    print(f"OLED: {WIDTH}x{HEIGHT} @ {hex(OLED_ADDR)}")
    print()

    try:
        for target in TARGETS:
            results[target] = capture_distance(target)

        show_done()
        time.sleep(6)

        print()
        print("========== RESULTS ==========")

        for target, measured in results.items():
            print(
                f"Target {target:3d} cm -> "
                f"{measured:7.2f} cm"
            )

        print("=============================")

    finally:
        ultra.sensor.close()
        oled.clear()


if __name__ == "__main__":
    main()
