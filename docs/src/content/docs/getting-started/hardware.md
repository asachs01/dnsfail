---
title: Hardware Requirements
description: Components needed to build the DNS Incident Timer.
---

# Hardware Requirements

This project requires specific hardware components. Here's what you need:

## Required Components

### Raspberry Pi

Any Raspberry Pi with GPIO headers will work:

| Model | Status | Notes |
|-------|--------|-------|
| Pi 4 Model B | ✅ Recommended | Best performance |
| Pi 3 Model B+ | ✅ Tested | Works well |
| Pi Zero 2 W | ✅ Works | Compact option |
| Pi Zero W | ⚠️ Limited | May struggle with display |

**Requirements:**
- GPIO header (40-pin)
- Network connectivity (for web interface)
- MicroSD card (8GB+)
- Power supply (5V, 3A recommended)

### RGB LED Matrix

The project uses the Adafruit-style HUB75 RGB LED matrix panels:

| Size | Status | Notes |
|------|--------|-------|
| 32x64 | ✅ Recommended | Good size for desk display |
| 32x32 | ✅ Works | Smaller, simpler |
| 64x64 | ✅ Works | Larger display |

**Recommended:**
- [Adafruit 32x64 RGB LED Matrix](https://www.adafruit.com/product/2278)
- Compatible with rpi-rgb-led-matrix library

### Adafruit RGB Matrix HAT/Bonnet

Required to interface the Pi with the LED matrix:

- [RGB Matrix Bonnet](https://www.adafruit.com/product/3211) (recommended)
- [RGB Matrix HAT](https://www.adafruit.com/product/2345) (alternative)

This provides:
- Level shifting for the matrix
- Proper power distribution
- Clean GPIO connection

### Push Button

Any momentary push button works:

- **Recommended:** Large arcade-style button for satisfying presses
- Connects to GPIO pin (default: GPIO 19)
- Needs pull-up resistor (software pull-up used by default)

### Speaker/Audio Output

For the audio feedback:

- 3.5mm audio jack on Pi (headphones jack)
- USB audio adapter (alternative)
- Powered speakers recommended

## Wiring Diagram

```
Raspberry Pi GPIO Header
┌─────────────────────────────────┐
│  3V3  (1) (2)  5V               │
│  SDA  (3) (4)  5V               │
│  SCL  (5) (6)  GND              │
│  GP4  (7) (8)  TXD              │
│  GND  (9) (10) RXD              │
│  GP17 (11)(12) GP18             │
│  GP27 (13)(14) GND              │
│  GP22 (15)(16) GP23             │
│  3V3  (17)(18) GP24             │
│  MOSI (19)(20) GND              │
│  MISO (21)(22) GP25             │
│  SCLK (23)(24) CE0              │
│  GND  (25)(26) CE1              │
│  ID_SD(27)(28) ID_SC            │
│  GP5  (29)(30) GND              │
│  GP6  (31)(32) GP12             │
│  GP13 (33)(34) GND              │
│ *GP19*(35)(36) GP16   ◀── Button
│  GP26 (37)(38) GP20             │
│  GND  (39)(40) GP21             │
└─────────────────────────────────┘
                ▲
                │
        Button wiring:
        GPIO 19 ──┬── Button ── GND
                  │
           (internal pull-up)
```

## Power Requirements

The LED matrix requires significant power:

| Component | Current Draw |
|-----------|-------------|
| Raspberry Pi 4 | 600mA - 1.2A |
| 32x64 Matrix (full white) | Up to 4A |
| **Total** | **5-6A @ 5V** |

**Power Supply Recommendations:**
- Use the matrix bonnet's dedicated power input
- 5V 10A power supply for the matrix
- Separate USB-C power for the Pi (or power through bonnet)

## Bill of Materials

| Item | Quantity | Approx. Cost |
|------|----------|--------------|
| Raspberry Pi 4 (2GB+) | 1 | $45 |
| 32x64 RGB LED Matrix | 1 | $40 |
| RGB Matrix Bonnet | 1 | $15 |
| Push Button | 1 | $5 |
| 5V 10A Power Supply | 1 | $15 |
| MicroSD Card (16GB) | 1 | $10 |
| Jumper Wires | Pack | $5 |
| Powered Speakers | 1 | $15 |
| **Total** | | **~$150** |

## Optional Components

- **Enclosure/Case**: 3D printed case for a polished look
- **Big Red Button**: More dramatic reset experience
- **USB Audio Adapter**: Better audio quality than built-in

## Next Steps

- [Quick Start](/getting-started/quick-start/) - Assembly and initial setup
- [Native Installation](/installation/native/) - Install on bare metal
- [Docker Deployment](/installation/docker/) - Run in a container
