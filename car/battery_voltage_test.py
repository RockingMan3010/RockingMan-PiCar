#!/usr/bin/env python3

import time
import statistics
import smbus

I2C_BUS = 1
ADS7830_ADDRESS = 0x48

ADC_VREF = 4.93
CHANNEL = 0

R15 = 3000
R17 = 1000
DIVISION_RATIO = R17 / (R15 + R17)

CMD = 0x84

SAMPLE_COUNT = 20
SAMPLE_DELAY = 0.1


def control_byte(channel):
    return CMD | (((channel << 2 | channel >> 1) & 0x07) << 4)


def battery_voltage_from_adc(adc_value):
    adc_voltage = adc_value / 255.0 * ADC_VREF
    return adc_voltage / DIVISION_RATIO


def main():
    bus = smbus.SMBus(I2C_BUS)

    raw_values = []
    voltages = []

    try:
        print("Reading ADS7830 battery voltage...")
        print()

        for i in range(SAMPLE_COUNT):
            raw = bus.read_byte_data(
                ADS7830_ADDRESS,
                control_byte(CHANNEL),
            )

            voltage = battery_voltage_from_adc(raw)

            raw_values.append(raw)
            voltages.append(voltage)

            print(
                f"[{i+1:02d}/{SAMPLE_COUNT}] "
                f"ADC={raw:3d}  "
                f"Battery={voltage:.3f} V"
            )

            time.sleep(SAMPLE_DELAY)

    finally:
        bus.close()

    median_v = statistics.median(voltages)
    mean_v = statistics.mean(voltages)

    print()
    print("========== RESULT ==========")
    print(f"Median voltage : {median_v:.3f} V")
    print(f"Mean voltage   : {mean_v:.3f} V")
    print(f"Minimum        : {min(voltages):.3f} V")
    print(f"Maximum        : {max(voltages):.3f} V")
    print(f"ADC range      : {min(raw_values)}..{max(raw_values)}")
    print("============================")


if __name__ == "__main__":
    main()
