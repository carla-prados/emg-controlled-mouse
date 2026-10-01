"""EMG-controlled mouse — MicroPython port of the original Arduino sketch.

Five surface-EMG channels drive a USB mouse: one clicks, two move the cursor
horizontally, two vertically. Cursor control is live only while ENABLE_PIN is
high. The decision logic mirrors the original sketch line for line.
"""

import time

import usb.device
from machine import SPI, Pin
from usb.device.mouse import MouseInterface

import config as cfg
from adc import MCP3008
from emg import Channel


def burst(mouse, steps, dx, dy):
    """Move in eased steps along (dx, dy), each of -1, 0 or 1, as the sketch did."""
    last = len(steps) - 1
    for i, px in enumerate(steps):
        mouse.move_by(dx * px, dy * px)
        time.sleep_ms(cfg.SETTLE_MS if i == last else cfg.STEP_MS)


def click(mouse):
    mouse.click_left(True)
    mouse.click_left(False)
    time.sleep_ms(cfg.CLICK_MS)


def main():
    mouse = MouseInterface()
    # builtin_driver keeps the USB serial REPL alongside the mouse,
    # so the plotter output and mpremote still work.
    usb.device.get().init(mouse, builtin_driver=True)

    spi = SPI(cfg.SPI_ID, baudrate=cfg.SPI_BAUD, polarity=0, phase=0,
              sck=Pin(cfg.SPI_SCK), mosi=Pin(cfg.SPI_MOSI), miso=Pin(cfg.SPI_MISO))
    adc = MCP3008(spi, Pin(cfg.SPI_CS, Pin.OUT))
    ch = {
        name: Channel(adc, n, gain, threshold,
                      cfg.VREF, cfg.DIVIDER, cfg.ADC_COUNTS, cfg.ALPHA)
        for name, (n, gain, threshold) in cfg.CHANNELS.items()
    }
    enable = Pin(cfg.ENABLE_PIN, Pin.IN, Pin.PULL_DOWN)

    while not mouse.is_open():      # wait for the host to enumerate the mouse
        time.sleep_ms(100)

    while True:
        for c in ch.values():
            c.update()

        if cfg.PLOT:
            print(",".join("{:.3f}".format(c.value) for c in ch.values()))

        if not enable.value():
            continue

        # Click and horizontal movement exclude each other, click first;
        # vertical movement is decided independently, up before down.
        if ch["click"].active:
            click(mouse)
        elif ch["left"].active:
            burst(mouse, cfg.BURST_X, -1, 0)
        elif ch["right"].active:
            burst(mouse, cfg.BURST_X, 1, 0)

        if ch["up"].active:
            burst(mouse, cfg.BURST_Y, 0, -1)
        elif ch["down"].active:
            burst(mouse, cfg.BURST_Y, 0, 1)


main()
