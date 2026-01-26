---
title: API Reference
description: Python API and module reference for the DNS Incident Timer.
---

# API Reference

Complete reference for the DNS Incident Timer Python module.

## Module: dns_counter

The main module containing all application logic.

### Functions

#### load_config

```python
def load_config(config_path: str = "/usr/local/share/dnsfail/config.yaml") -> Dict[str, Any]
```

Load configuration from YAML file with fallback to defaults.

**Parameters:**
- `config_path` - Path to YAML configuration file

**Returns:**
- Dictionary containing all configuration keys

**Default configuration:**
```python
{
    "gpio_pin": 19,
    "brightness": 80,
    "audio_file": "/usr/local/share/dnsfail/media/fail.wav",
    "web_port": 5000,
    "persistence_file": "/usr/local/share/dnsfail/last_reset.json",
    "log_level": "INFO",
}
```

---

### Class: DNSCounter

Main application class managing display, GPIO, and state.

#### Constructor

```python
def __init__(self) -> None
```

Initialize the DNS counter with hardware and restore state.

**Actions:**
1. Parse command-line arguments
2. Load configuration from YAML
3. Initialize RGB matrix
4. Load persisted state
5. Setup GPIO button monitoring

**Raises:**
- `Exception` - If RGB matrix initialization fails

---

#### Instance Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `parser` | `ArgumentParser` | CLI argument parser |
| `args` | `Namespace` | Parsed arguments |
| `config` | `Dict[str, Any]` | Loaded configuration |
| `persistence_file` | `str` | State file path |
| `matrix` | `RGBMatrix` | LED matrix instance |
| `last_reset` | `datetime` | Last reset timestamp |
| `BUTTON_PIN` | `int` | GPIO pin number |
| `chip` | `Optional[gpiod.Chip]` | GPIO chip (v1 only) |
| `line` | `Any` | GPIO line handle |
| `button_thread` | `Optional[Thread]` | Button monitor thread |
| `_gpiod_version` | `int` | Detected gpiod version (1 or 2) |

---

#### Methods

##### save_state

```python
def save_state(self) -> None
```

Save the `last_reset` timestamp to JSON file using atomic write.

**File format:**
```json
{
    "last_reset": "2024-01-25T12:00:00.000000",
    "version": 1
}
```

**Note:** Uses temporary file and atomic rename to prevent corruption.

---

##### load_state

```python
def load_state(self) -> datetime
```

Load the `last_reset` timestamp from JSON persistence file.

**Returns:**
- Loaded datetime, or `datetime.now()` if loading fails

**Handles:**
- Missing file
- Corrupt JSON
- Missing `last_reset` key
- Any unexpected errors

---

##### create_parser

```python
def create_parser(self) -> argparse.ArgumentParser
```

Create and configure argument parser for LED matrix options.

**Returns:**
- Configured `ArgumentParser` with matrix arguments

**Supported arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `--led-rows` | 32 | Display rows |
| `--led-cols` | 64 | Panel columns |
| `--led-chain` | 1 | Daisy-chained boards |
| `--led-parallel` | 1 | Parallel chains |
| `--led-pwm-bits` | 11 | PWM bits (1-11) |
| `--led-brightness` | 100 | Brightness (1-100) |
| `--led-gpio-mapping` | adafruit-hat | Hardware mapping |
| `--led-scan-mode` | 1 | Scan mode |
| `--led-pwm-lsb-nanoseconds` | 130 | PWM timing |
| `--led-row-addr` | 0 | Row addressing |
| `--led-multiplexing` | 0 | Multiplexing type |
| `--led-pixel-mapper` | "" | Pixel mapper |
| `--led-rgb-sequence` | RGB | Color order |
| `--led-slowdown-gpio` | 4 | GPIO slowdown |
| `--config` | /usr/local/share/dnsfail/config.yaml | Config path |

---

##### format_duration

```python
def format_duration(self, duration: timedelta) -> Tuple[str, str]
```

Format duration into two display lines showing all time units.

**Parameters:**
- `duration` - Time duration to format

**Returns:**
- Tuple of two strings:
  - Line 1: `"YYy MMmo DDd"` (years, months, days)
  - Line 2: `"HHh MMm SSs"` (hours, minutes, seconds)

**Example:**
```python
>>> counter.format_duration(timedelta(days=400, hours=5, minutes=30, seconds=15))
("01y 01mo 05d", "05h 30m 15s")
```

---

##### run

```python
def run(self) -> None
```

Main display loop that renders the counter continuously.

**Display layout:**
```
┌────────────────────────────┐
│        DAYS SINCE          │  (white, centered)
│            DNS             │  (white, centered)
│       01y 02mo 15d         │  (red, centered)
│       08h 30m 45s          │  (red, centered)
└────────────────────────────┘
```

**Behavior:**
- Updates every second
- Clears display on exit
- Releases GPIO resources on exit

**Raises:**
- `KeyboardInterrupt` - Caught and handled gracefully

---

##### setup_gpio

```python
def setup_gpio(self) -> None
```

Initialize GPIO for button input using gpiod library.

**Supports:**
- gpiod v1 API (`chip.get_line()`)
- gpiod v2 API (`gpiod.request_lines()`)

**Configuration:**
- Direction: Input
- Bias: Pull-up enabled
- Consumer: "dns_counter"

**On failure:** Sets `chip` and `line` to `None` (display-only mode)

---

##### _get_button_value

```python
def _get_button_value(self) -> int
```

Read button value, handling both gpiod v1 and v2 APIs.

**Returns:**
- `0` if button is pressed (active low)
- `1` if button is released

---

##### _check_button

```python
def _check_button(self) -> None
```

Thread function to continuously monitor button state.

**Behavior:**
- Polls button every 100ms
- 300ms debounce window
- On press: resets counter, saves state, plays audio

**Runs in:** Daemon thread

---

##### test_display

```python
def test_display(self) -> None
```

Test RGB matrix with red, green, blue color sequence.

**Behavior:**
- Shows full red for 2 seconds
- Shows full green for 2 seconds
- Shows full blue for 2 seconds
- Clears display

**Note:** For hardware diagnostics only.

---

## Command Line Interface

```bash
python dns_counter.py [OPTIONS]
```

### Matrix Options

```
--led-rows N          Display rows (16 or 32)
--led-cols N          Panel columns (32 or 64)
--led-chain N         Daisy-chained boards
--led-parallel N      Parallel chains (1-3)
--led-pwm-bits N      PWM bits (1-11)
--led-brightness N    Brightness (1-100)
--led-gpio-mapping S  Hardware: regular, adafruit-hat, adafruit-hat-pwm
--led-scan-mode N     0=Progressive, 1=Interlaced
--led-slowdown-gpio N Slowdown factor (0-4)
```

### Application Options

```
--config PATH         Path to YAML configuration file
```

### Example

```bash
# Run with custom config and reduced brightness
python dns_counter.py \
    --config /etc/dnsfail/config.yaml \
    --led-brightness 50 \
    --led-slowdown-gpio 3
```

---

## Configuration File Schema

```yaml
# GPIO Configuration
gpio_pin: 19              # BCM pin number (int)

# Display Configuration
brightness: 80            # 1-100 (int)

# Audio Configuration
audio_file: /path/to/file.wav   # Absolute path (str)
audio_device: ""          # ALSA device, empty for default (str)

# Web Server Configuration
web_port: 5000            # Port number (int)

# Persistence Configuration
persistence_file: /path/to/state.json   # Absolute path (str)

# Logging Configuration
log_level: INFO           # DEBUG, INFO, WARNING, ERROR (str)
```

---

## State File Schema

```json
{
    "last_reset": "ISO-8601-datetime",
    "version": 1
}
```

**Fields:**
- `last_reset` - ISO 8601 datetime string
- `version` - Schema version (always 1)

---

## Logging

The module uses Python's `logging` module with two handlers:

### Console Handler

```
2024-01-25 12:00:00,000 dns_counter: INFO [dns_counter.py:123] Message
```

### Syslog Handler

```
dns_counter[1234]: INFO [dns_counter.py:123] Message
```

**Facility:** `LOG_DAEMON`

### Log Levels

| Level | Use |
|-------|-----|
| DEBUG | Button state changes, audio playback details |
| INFO | Startup, shutdown, button presses, state saves |
| WARNING | Missing config/state files, non-critical issues |
| ERROR | GPIO failures, audio errors, unexpected exceptions |
| CRITICAL | Fatal errors preventing startup |

---

## Error Codes

The application uses standard Unix exit codes:

| Code | Meaning |
|------|---------|
| 0 | Clean exit (Ctrl+C) |
| 1 | Fatal error (matrix init failed, etc.) |

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `MOCK_MODE=1` | Enable hardware mocking for testing |
| `PYTHONUNBUFFERED=1` | Real-time log output |
