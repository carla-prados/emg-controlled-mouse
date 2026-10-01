"""MCP3008: 8-channel, 10-bit SPI ADC.

The Pico has three usable ADC inputs and the mouse needs five, so the channels
are read through an MCP3008 instead. Its 10 bits match the Leonardo's ADC.
"""


class MCP3008:
    def __init__(self, spi, cs):
        self._spi = spi
        self._cs = cs
        self._cs.value(1)
        self._tx = bytearray(3)
        self._rx = bytearray(3)

    def read(self, channel):
        """Raw reading, 0-1023, of single-ended input `channel` (0-7)."""
        self._tx[0] = 0x01                      # start bit
        self._tx[1] = (0x08 | channel) << 4     # single-ended + channel number
        self._tx[2] = 0x00
        self._cs.value(0)
        self._spi.write_readinto(self._tx, self._rx)
        self._cs.value(1)
        return ((self._rx[1] & 0x03) << 8) | self._rx[2]
