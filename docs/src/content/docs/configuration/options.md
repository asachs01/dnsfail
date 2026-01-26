---
title: Configuration Options
description: All configuration options for the DNS Incident Timer.
---

# Configuration Options

The DNS Incident Timer is configured via a YAML file.

## Configuration File Location

| Installation | Path |
|--------------|------|
| Native | `/etc/dnsfail/config.yaml` |
| Docker | `./config.docker.yaml` (mounted to `/app/config.yaml`) |

## Complete Configuration Reference

```yaml
# GPIO Configuration
gpio_pin: 19  # GPIO pin for reset button (BCM numbering)

# Display Configuration
brightness: 80  # LED matrix brightness (1-100)

# Audio Configuration
audio_file: /usr/local/share/dnsfail/media/fail.wav
audio_device: ""  # Optional: ALSA device (e.g., "plughw:Headphones")

# Web Server Configuration
web_port: 5000  # Port for web interface

# Persistence Configuration
persistence_file: /usr/local/share/dnsfail/last_reset.json

# Logging Configuration
log_level: INFO  # DEBUG, INFO, WARNING, ERROR
```

## Option Details

### gpio_pin

The GPIO pin connected to the reset button, using BCM numbering.

| Value | Description |
|-------|-------------|
| `19` | Default - GPIO 19 (physical pin 35) |
| Any valid GPIO | Must have internal pull-up capability |

:::tip
Use `pinout` command on your Pi to see GPIO layout.
:::

### brightness

LED matrix brightness level.

| Value | Description |
|-------|-------------|
| `1-20` | Dim - good for dark rooms |
| `50-80` | Normal - recommended |
| `90-100` | Bright - high visibility, more power |

:::caution
Higher brightness = more power consumption and heat.
:::

### audio_file

Path to the audio file played on reset.

**Requirements:**
- Must be WAV format (PCM)
- Stereo or mono
- 44.1kHz or 48kHz sample rate

**Default locations:**
- Native: `/usr/local/share/dnsfail/media/fail.wav`
- Docker: Same path (volume mounted)

### audio_device

ALSA device for audio playback. Leave empty for system default.

| Value | Description |
|-------|-------------|
| `""` (empty) | Use system default |
| `plughw:Headphones` | Pi's 3.5mm jack (recommended for Docker) |
| `plughw:0,0` | First HDMI output |
| `hw:2,0` | Direct hardware access (may require permissions) |

:::tip
Use card names (`plughw:Headphones`) instead of numbers (`plughw:2,0`) as card numbering can change between boots.
:::

**Find available devices:**
```bash
aplay -l
```

### web_port

Port for the optional web interface.

| Value | Description |
|-------|-------------|
| `5000` | Default port |
| `80` | Standard HTTP (requires root) |
| `8080` | Alternative non-privileged port |

### persistence_file

Path to store the timer state.

The file contains:
```json
{
  "last_reset": "2024-01-25T12:00:00.000000"
}
```

**Requirements:**
- Directory must exist
- Write permissions required
- Survives reboots

### log_level

Logging verbosity.

| Level | Description |
|-------|-------------|
| `DEBUG` | Everything, including button state changes |
| `INFO` | Normal operation messages |
| `WARNING` | Potential issues |
| `ERROR` | Errors only |

## Environment Variables

Some settings can be overridden via environment variables:

```bash
MOCK_MODE=1       # Enable hardware mocking (for testing)
PYTHONUNBUFFERED=1  # Real-time log output
```

## Example Configurations

### Minimal (defaults)

```yaml
gpio_pin: 19
brightness: 80
audio_file: /usr/local/share/dnsfail/media/fail.wav
persistence_file: /usr/local/share/dnsfail/last_reset.json
```

### Docker Production

```yaml
gpio_pin: 19
brightness: 80
audio_file: /usr/local/share/dnsfail/media/fail.wav
audio_device: plughw:Headphones
web_port: 5000
persistence_file: /usr/local/share/dnsfail/last_reset.json
log_level: INFO
```

### Debug Mode

```yaml
gpio_pin: 19
brightness: 50
audio_file: /usr/local/share/dnsfail/media/fail.wav
web_port: 5000
persistence_file: /tmp/dns_counter_state.json
log_level: DEBUG
```

## Applying Changes

After modifying configuration:

```bash
# Native installation
sudo systemctl restart dns_counter

# Docker
docker compose -f docker-compose.prod.yml restart
```

## Validating Configuration

Check logs after restart to verify:

```bash
# Native
sudo journalctl -u dns_counter -n 50

# Docker
docker compose -f docker-compose.prod.yml logs --tail 50
```

Look for:
- `Configuration loaded from: /path/to/config.yaml`
- `GPIO setup successful`
- `Audio devices ready`
