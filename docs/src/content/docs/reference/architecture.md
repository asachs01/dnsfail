---
title: Architecture
description: System architecture and component design of the DNS Incident Timer.
---

# Architecture

The DNS Incident Timer is a single-application Python system with multiple concurrent components.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DNS Incident Timer                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  Main Thread │    │Button Thread │    │  Web Interface   │  │
│  │  (Display)   │    │   (GPIO)     │    │   (Optional)     │  │
│  └──────┬───────┘    └──────┬───────┘    └────────┬─────────┘  │
│         │                    │                     │            │
│         └────────────────────┼─────────────────────┘            │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │   Shared State    │                        │
│                    │   (last_reset)    │                        │
│                    └─────────┬─────────┘                        │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │   Persistence     │                        │
│                    │   (JSON file)     │                        │
│                    └───────────────────┘                        │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                       Hardware Layer                             │
├────────────────┬─────────────────┬──────────────────────────────┤
│  RGB Matrix    │  GPIO Button    │  Audio Output                │
│  (64x32 LED)   │  (Pin 19)       │  (ALSA/aplay)                │
└────────────────┴─────────────────┴──────────────────────────────┘
```

## Component Details

### Main Thread (Display Loop)

The primary thread handles display rendering:

```python
def run(self) -> None:
    while True:
        canvas.Clear()

        # Draw header
        graphics.DrawText(canvas, header_font, x, y, white, "DAYS SINCE")
        graphics.DrawText(canvas, header_font, x, y, white, "DNS")

        # Calculate elapsed time
        duration = datetime.now() - self.last_reset

        # Draw time
        graphics.DrawText(canvas, time_font, x, y, red, time_line1)
        graphics.DrawText(canvas, time_font, x, y, red, time_line2)

        canvas = self.matrix.SwapOnVSync(canvas)
        time.sleep(1)
```

**Key characteristics:**
- Updates at 1Hz (once per second)
- Uses VSync for flicker-free updates
- Reads `last_reset` atomically (thread-safe via GIL)

### Button Thread (GPIO Monitor)

A daemon thread monitors the physical button:

```python
def _check_button(self) -> None:
    while True:
        value = self._get_button_value()
        if value == 0 and debounce_ok:  # Button pressed
            self.last_reset = datetime.now()
            self.save_state()
            subprocess.run(["aplay", "-D", device, sound_file])
        time.sleep(0.1)
```

**Key characteristics:**
- 100ms polling interval
- 300ms debounce to prevent double-triggers
- Daemon thread (won't block program exit)
- Supports gpiod v1 and v2 APIs

### State Management

State is managed through a single `last_reset` datetime:

| Operation | Thread Safety |
|-----------|---------------|
| Read `last_reset` | Safe (atomic via GIL) |
| Write `last_reset` | Safe (atomic via GIL) |
| File persistence | Atomic via temp file + rename |

### Persistence Layer

State survives reboots via JSON file:

```json
{
  "last_reset": "2024-01-25T12:00:00.000000",
  "version": 1
}
```

**Atomic write pattern:**
1. Write to temporary file in same directory
2. Atomic rename to target path
3. Prevents corruption on power loss

## Hardware Interfaces

### RGB Matrix (rpi-rgb-led-matrix)

| Setting | Value | Purpose |
|---------|-------|---------|
| `rows` | 32 | Panel height |
| `cols` | 64 | Panel width |
| `hardware_mapping` | adafruit-hat | HAT type |
| `gpio_slowdown` | 3 | Reduce flicker |
| `pwm_bits` | 11 | Color depth |
| `scan_mode` | 1 | Progressive scan |

### GPIO (gpiod)

The button uses active-low logic with internal pull-up:

```
Button released:  GPIO 19 = HIGH (1)  ← Pull-up holds high
Button pressed:   GPIO 19 = LOW (0)   ← Connected to GND
```

**API version detection:**
```python
if hasattr(gpiod, "request_lines"):
    # v2 API: gpiod.request_lines() with LineSettings
else:
    # v1 API: chip.get_line() with LINE_REQ flags
```

### Audio (ALSA)

Audio playback uses the `aplay` command:

```bash
aplay -D plughw:Headphones /path/to/sound.wav
```

| Format | Requirement |
|--------|-------------|
| Type | WAV (PCM) |
| Sample Rate | 44.1kHz or 48kHz |
| Channels | Mono or Stereo |
| Bit Depth | 16-bit |

## Configuration Flow

```
┌─────────────────┐
│ Command Line    │──┐
│ Arguments       │  │
└─────────────────┘  │    ┌──────────────────┐
                     ├───▶│ Configuration    │
┌─────────────────┐  │    │ Dictionary       │
│ YAML Config     │──┤    └────────┬─────────┘
│ File            │  │             │
└─────────────────┘  │             ▼
                     │    ┌──────────────────┐
┌─────────────────┐  │    │ DNSCounter       │
│ Default Values  │──┘    │ Initialization   │
└─────────────────┘       └──────────────────┘
```

**Precedence (highest to lowest):**
1. Command-line arguments (matrix settings only)
2. YAML configuration file
3. Built-in defaults

## Error Handling

### Graceful Degradation

| Component | Failure Mode | Fallback |
|-----------|--------------|----------|
| Config file | Missing/corrupt | Use defaults |
| State file | Missing/corrupt | Start from now |
| GPIO | Permission denied | Display-only mode |
| Syslog | Unavailable | Console logging only |

### Cleanup on Exit

```python
try:
    dns_counter.run()
except KeyboardInterrupt:
    pass
finally:
    line.release()      # Release GPIO
    chip.close()        # Close chip
    matrix.Clear()      # Clear display
```

## Threading Model

```
┌─────────────────────────────────────────────────┐
│                  Main Process                    │
├─────────────────────────────────────────────────┤
│                                                  │
│  Main Thread                Button Thread        │
│  ┌─────────────┐           ┌─────────────┐      │
│  │ Display     │           │ GPIO Poll   │      │
│  │ Loop        │◀─────────▶│ Loop        │      │
│  │ (1 Hz)      │  shared   │ (10 Hz)     │      │
│  │             │  state    │ (daemon)    │      │
│  └─────────────┘           └─────────────┘      │
│                                                  │
└─────────────────────────────────────────────────┘
```

**Thread safety notes:**
- Python GIL ensures atomic datetime operations
- No explicit locks needed for `last_reset` access
- Button thread is daemon to ensure clean exit

## File Layout

### Native Installation

```
/opt/dnsfail/
├── dns_counter.py          # Main application
├── venv/                   # Python virtual environment
└── requirements.txt        # Dependencies

/etc/dnsfail/
└── config.yaml             # Configuration

/usr/local/share/dnsfail/
├── fonts/                  # BDF fonts
│   ├── 5x8.bdf
│   └── 6x10.bdf
├── media/                  # Audio files
│   └── fail.wav
└── last_reset.json         # State persistence

/etc/systemd/system/
└── dns_counter.service     # systemd unit
```

### Docker Installation

```
Container:
/app/
├── dns_counter.py          # Main application
├── config.yaml             # Mounted config
└── requirements.txt

/usr/local/share/dnsfail/   # Mounted volume
├── fonts/
├── media/
└── last_reset.json         # Persisted state

Host:
./config.docker.yaml        # Configuration
/usr/local/share/dnsfail/   # Persistence volume
```

## Startup Sequence

1. **Parse arguments** - Matrix configuration from CLI
2. **Load config** - YAML file with fallback to defaults
3. **Initialize matrix** - Set up RGB LED panel
4. **Load state** - Restore last reset time from JSON
5. **Setup GPIO** - Configure button with API version detection
6. **Start button thread** - Spawn daemon monitor thread
7. **Wait for audio** - Retry loop for device availability
8. **Run display loop** - Main rendering loop

## Dependencies

| Package | Purpose |
|---------|---------|
| `gpiod` | GPIO access (v1 or v2) |
| `rpi-rgb-led-matrix` | LED matrix control |
| `Pillow` | Image/text rendering |
| `PyYAML` | Configuration parsing |
| `Flask` | Web interface (optional) |
