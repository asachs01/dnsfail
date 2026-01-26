---
title: GPIO Setup
description: Configure the physical button and GPIO pins.
---

# GPIO Setup

The DNS Incident Timer uses a physical button connected to GPIO for resetting the counter.

## Default Configuration

- **GPIO Pin**: 19 (BCM numbering)
- **Physical Pin**: 35
- **Mode**: Input with internal pull-up
- **Active**: Low (button press = 0)

## Wiring

### Simple Button Wiring

```
GPIO 19 (Pin 35) ────┬──── Button ──── GND (Pin 39)
                     │
              (internal pull-up)
```

The software enables an internal pull-up resistor, so you only need:
1. One wire from GPIO 19 to one side of the button
2. One wire from the other side of the button to any GND pin

### Physical Pin Layout

```
                    ┌─────────────┐
               3V3  │ (1)    (2)  │ 5V
               SDA  │ (3)    (4)  │ 5V
               SCL  │ (5)    (6)  │ GND
               GP4  │ (7)    (8)  │ TXD
               GND  │ (9)   (10)  │ RXD
              GP17  │(11)   (12)  │ GP18
              GP27  │(13)   (14)  │ GND
              GP22  │(15)   (16)  │ GP23
               3V3  │(17)   (18)  │ GP24
              MOSI  │(19)   (20)  │ GND
              MISO  │(21)   (22)  │ GP25
              SCLK  │(23)   (24)  │ CE0
               GND  │(25)   (26)  │ CE1
             ID_SD  │(27)   (28)  │ ID_SC
               GP5  │(29)   (30)  │ GND
               GP6  │(31)   (32)  │ GP12
              GP13  │(33)   (34)  │ GND
         ──▶ GP19  │(35)   (36)  │ GP16  ◀── Default
              GP26  │(37)   (38)  │ GP20
               GND  │(39)   (40)  │ GP21
                    └─────────────┘
```

## Using a Different GPIO Pin

Edit the configuration file:

```yaml
# config.yaml
gpio_pin: 17  # Change to your preferred GPIO
```

**Valid GPIO pins for buttons** (with internal pull-up):
- GPIO 4, 5, 6, 12, 13, 16, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27

:::caution
Avoid these pins if using the RGB Matrix HAT/Bonnet, as they're used for the display.
:::

## gpiod Library Versions

The software supports both gpiod v1 and v2 APIs:

| Library Version | API | Installation |
|-----------------|-----|--------------|
| gpiod < 2.0 | v1 (`get_line()`) | System package |
| gpiod >= 2.0 | v2 (`request_lines()`) | pip install gpiod |

The software auto-detects which version is installed:

```python
# Automatic detection
if hasattr(gpiod, "request_lines"):
    # Use v2 API
else:
    # Use v1 API
```

## Testing GPIO

### Check Pin State

```bash
# Read current value (0 = pressed, 1 = released)
gpioget gpiochip0 19
```

### Monitor Pin Changes

```bash
# Watch for changes
gpiomon gpiochip0 19
```

### Verify gpiod Version

```bash
# Python
python3 -c "import gpiod; print(gpiod.__version__)"
```

## Button Types

### Momentary Push Button (Recommended)

- Press = contact closes
- Release = contact opens
- No latching

### Arcade Button

- Satisfying tactile feedback
- Usually has built-in LED (optional)
- Standard size: 30mm or 24mm

### Toggle Switch (Not Recommended)

Toggle switches will trigger repeatedly. Use momentary buttons.

## Debouncing

The software includes a 300ms debounce:

```python
if current_time - last_press > 0.3:  # 300ms debounce
    # Process button press
```

This prevents multiple triggers from a single press.

## Troubleshooting

### Button Not Detected

1. **Check wiring:**
   ```bash
   gpioget gpiochip0 19
   # Should return 1 when not pressed, 0 when pressed
   ```

2. **Check permissions:**
   ```bash
   ls -la /dev/gpiochip0
   # Should be accessible by your user
   ```

3. **Check logs:**
   ```bash
   # Look for GPIO errors
   sudo journalctl -u dns_counter | grep -i gpio
   ```

### Multiple Triggers

If the button triggers multiple times:
- Check for loose connections
- Verify you're using a momentary (not toggle) switch
- The debounce may need adjustment (modify source code)

### Docker GPIO Issues

In Docker, ensure:

1. **Device mapping:**
   ```yaml
   devices:
     - /dev/gpiochip0:/dev/gpiochip0
   ```

2. **Privileged mode:**
   ```yaml
   privileged: true
   ```

3. **gpiod v2 compatibility** (check logs for "Using gpiod v2 API")

## LED Indicator (Optional)

If your button has a built-in LED:

```
GPIO 26 ───── 330Ω ───── LED+ ───── LED- ───── GND
```

You'll need to modify the source code to control the LED.
