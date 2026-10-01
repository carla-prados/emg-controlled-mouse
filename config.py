"""Everything you would tune lives here.

Gains, thresholds, smoothing and the cursor bursts are the values of the
original Arduino sketch, unchanged.
"""

# --- Analogue front end -------------------------------------------------------
# The EMG chain outputs 0-5 V: it was built for the Arduino Leonardo's 5 V ADC.
# The Pico and the MCP3008 run at 3.3 V, so every channel goes through a
# resistor divider first. Readings are scaled back to front-end volts, which
# keeps every threshold below in the same units as the original sketch.
VREF = 3.3                              # MCP3008 reference, wired to the Pico's 3V3
DIVIDER = 10_000 / (5_100 + 10_000)     # 5.1 kΩ over 10 kΩ: 5 V in → 3.31 V out
ADC_COUNTS = 1024                       # 10-bit; the sketch divided by 2^10 as well

# --- Signal processing --------------------------------------------------------
ALPHA = 0.2     # exponential moving average: weight of the newest sample

# name: (MCP3008 channel, gain, threshold in gained volts)
CHANNELS = {
    "click": (0, 1, 4.565),
    "left":  (1, 3, 9.6155),
    "right": (2, 5, 15.842),
    "up":    (3, 1, 3.0686),
    "down":  (4, 1, 3.1255),
}

# --- Pins (Raspberry Pi Pico) -------------------------------------------------
ENABLE_PIN = 15     # cursor control only while this reads high (the sketch's "jump pin")
SPI_ID = 0
SPI_SCK = 18
SPI_MOSI = 19
SPI_MISO = 16
SPI_CS = 17
SPI_BAUD = 1_000_000    # the MCP3008 is rated to 1.35 MHz at 2.7 V

# --- Cursor -------------------------------------------------------------------
# Each detection moves the cursor in an eased burst: big steps, then smaller.
BURST_X = (5, 5, 5, 5, 4, 4, 4, 4)     # pixels per step, horizontal
BURST_Y = (4, 4, 4, 4, 3, 3, 3, 3)     # pixels per step, vertical
STEP_MS = 5         # pause between steps
SETTLE_MS = 10      # pause after the last step
CLICK_MS = 50       # pause after a click

# --- Output -------------------------------------------------------------------
# Print the five gained values as one CSV line per loop, for Thonny's plotter
# while calibrating. Printing slows the loop; turn it off once tuned.
PLOT = True
