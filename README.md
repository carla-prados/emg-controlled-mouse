# EMG-controlled mouse

Five channels of surface electromyography — the electrical activity of the arm's muscles — drive a computer cursor: one channel clicks, two move it left and right, two move it up and down. Assistive technology for someone who cannot use a mouse by hand.

It was built in one week, 8–12 December 2025, for **Scenario 4, "Regaining Control"**, of *Design and Professional Skills II* at UCL, by Group 15. I led the team, designed and assembled the acquisition circuitry, chose the electrode placement and wrote the control code. The project was graded **91%**.

**The original ran on an Arduino Leonardo.** That sketch was submitted coursework, so university rules keep it unpublished. This repository is a rewrite of it in **MicroPython**, with the same behaviour.

Project page: [carlaprados.com/projects/emg-controlled-mouse](https://carlaprados.com/projects/emg-controlled-mouse/)

---

## How it works

```
muscle ─► electrodes ─► instrumentation amp ─► Sallen-Key high-pass ─► Sallen-Key low-pass
       ─► non-inverting amp ─► precision rectifier ─► ADC ─► smoothing ─► gain ─► threshold ─► USB mouse
```

### The analogue front end

The chain was specified from the signal, not from a parts list. Surface EMG is tens of microvolts to a couple of millivolts, with its content between 20 and 500 Hz, and the Leonardo's ADC reads 0–5 V. Those three facts set the design: a gain of about 1,500, a 20–500 Hz passband, and rectification so the signal stays positive.

| Stage | Design target | Measured |
| --- | --- | --- |
| Total gain | ≈ 1,500 | **1,705** (instrumentation amp 35.9 × non-inverting 47.6) |
| Passband | 20–500 Hz | **18.5–482.3 Hz** |
| Rectification | full-wave, no diode drop | precision rectifier |

- The gain overshoot comes from **E6-series resistor tolerance (20%)**.
- The **instrumentation amplifier** was chosen for its common-mode rejection, which suppresses 50 Hz mains noise.
- The second-order active filters reach a −50 dB floor where a passive stage manages −25 dB. **Only the two channels that needed maximum crosstalk rejection got active filters**; the three with well-isolated electrode positions got passive ones. That meant fewer components, less power and lower cost, with no loss of signal quality where it mattered.

### The control code

Every loop, each channel goes through the same four steps:

1. **Read** the ADC and convert it to volts.
2. **Smooth** it with an exponential moving average, `smooth = 0.2 · new + 0.8 · smooth`.
3. **Apply a per-channel gain**, so the threshold sits in a usable range.
4. **Compare** against a per-channel threshold, found by calibration.

| Channel | Action | Gain | Threshold (gained volts) |
| --- | --- | --- | --- |
| 0 | Left click | 1 | 4.565 |
| 1 | Move left | 3 | 9.6155 |
| 2 | Move right | 5 | 15.842 |
| 3 | Move up | 1 | 3.0686 |
| 4 | Move down | 1 | 3.1255 |

The rules that turn detections into mouse actions:

- **Nothing happens unless the enable input is high.** It lets the user rest without the cursor drifting.
- **Click, left and right exclude each other**, in that order of priority: a click is never also a move.
- **Up and down are decided separately**, up first, so the cursor can move diagonally.
- **Each detection moves the cursor in an eased burst**: four steps of 5 px then four of 4 px horizontally (4 px then 3 px vertically), 5 ms apart. A burst feels smoother than a single jump.

---

## The MicroPython port

### Why a different board

MicroPython cannot run on the Leonardo: its ATmega32U4 has 2.5 KB of RAM. The port therefore targets a **Raspberry Pi Pico**, the reference MicroPython board, which can act as a USB mouse just as the Leonardo did.

That change has two consequences for the hardware:

- **Five analogue inputs.** The Pico exposes only three, so the channels are read through an **MCP3008**, an 8-channel SPI ADC. It is 10-bit like the Leonardo's, so the thresholds carry over.
- **3.3 V, not 5 V.** The front end outputs up to 5 V, and the Pico and the MCP3008 run at 3.3 V. Each channel goes through a **5.1 kΩ / 10 kΩ divider**, and the code scales the reading back, so the thresholds stay in the original's volts.

**Never connect a 5 V signal straight to a Pico pin.**

### Wiring

| From | To |
| --- | --- |
| Front-end outputs 0–4, each through its divider | MCP3008 CH0–CH4 |
| MCP3008 VDD and VREF | Pico 3V3(OUT) |
| MCP3008 AGND and DGND | Pico GND |
| MCP3008 CLK | GP18 |
| MCP3008 DIN | GP19 |
| MCP3008 DOUT | GP16 |
| MCP3008 CS/SHDN | GP17 |
| Enable switch | between 3V3 and GP15 (internal pull-down) |

The analogue front end is unchanged. Pins, gains and thresholds are all in [`config.py`](config.py).

### Install

1. Flash **MicroPython 1.23 or later** onto the Pico ([download](https://micropython.org/download/RPI_PICO/)). USB device support arrived in 1.23.
2. Install the USB mouse driver from micropython-lib:
   ```sh
   mpremote mip install usb-device-mouse
   ```
3. Copy the code and reset:
   ```sh
   mpremote cp config.py adc.py emg.py main.py :
   mpremote reset
   ```

The Pico then shows up as a USB mouse, and keeps its serial port for the REPL and the plotter output.

### Calibrate

The thresholds suit our electrodes on our arms; anyone else will need their own.

1. Leave `PLOT = True` in `config.py` and open the serial plotter in [Thonny](https://thonny.org/). It prints the five gained values, one line per loop.
2. Contract each muscle in turn, and note the resting level and the contracted level of its channel.
3. Set that channel's threshold between the two, nearer the resting level if the movement feels slow to trigger.
4. Set `PLOT = False` once tuned: printing slows the loop.

### What changed from the original

The decision logic, the gains, the thresholds, the smoothing and the bursts are those of the sketch, unchanged. The differences:

- **The enable input is digital.** The sketch read it as an analogue pin and checked `analogRead(A1) > 3`, which compares the raw ADC count, not volts: about 15 mV already counts as on. A switch on a digital pin with a pull-down does what that check intended.
- **Readings come through the MCP3008 and the divider**, scaled back to front-end volts.
- **The plotter output is one CSV line** of five values, instead of the sketch's label-and-index lines.
- **Configuration lives in one file**, and the five copy-pasted channels are one `Channel` class.

### Status

The port follows the sketch line by line and its logic is straightforward, but **it has not yet been run on hardware**. Treat the wiring above as a starting point, and check the divider outputs with a multimeter before connecting the ADC.

---

## Repository layout

```
main.py          the loop: read, smooth, decide, move
emg.py           one channel: volts → smoothed → gained → compared
adc.py           MCP3008 driver
config.py        pins, gains, thresholds, timings
```

## Licence

[MIT](LICENSE) © 2025 Carla Prados Bodega
