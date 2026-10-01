"""One EMG channel: raw count → front-end volts → smoothed → gained → compared."""


class Channel:
    def __init__(self, adc, channel, gain, threshold, vref, divider, counts, alpha):
        self._adc = adc
        self._channel = channel
        self._volts_per_count = vref / counts / divider
        self._alpha = alpha
        self.gain = gain
        self.threshold = threshold
        # Seeded with a first reading, as the sketch's setup() did, so the
        # average does not have to climb from zero.
        self.smooth = self._volts()
        self.value = self.smooth * gain

    def _volts(self):
        return self._adc.read(self._channel) * self._volts_per_count

    def update(self):
        a = self._alpha
        self.smooth = a * self._volts() + (1 - a) * self.smooth
        self.value = self.smooth * self.gain
        return self.value

    @property
    def active(self):
        return self.value > self.threshold
