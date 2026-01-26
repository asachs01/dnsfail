---
title: Audio Setup
description: Configure audio playback for the reset sound.
---

# Audio Setup

The DNS Incident Timer plays an audio clip when the reset button is pressed.

## Audio Requirements

| Requirement | Value |
|-------------|-------|
| Format | WAV (PCM) |
| Sample Rate | 44.1kHz or 48kHz |
| Channels | Mono or Stereo |
| Bit Depth | 16-bit |

:::caution[MP3 Not Supported]
The `aplay` command only supports WAV format. Convert MP3 files before use.
:::

## Default Audio File

The default audio file is located at:
- `/usr/local/share/dnsfail/media/fail.wav`

## Configuring Audio Device

### Find Available Devices

```bash
aplay -l
```

Example output:
```
**** List of PLAYBACK Hardware Devices ****
card 0: vc4hdmi0 [vc4-hdmi-0], device 0: MAI PCM i2s-hifi-0
card 1: vc4hdmi1 [vc4-hdmi-1], device 0: MAI PCM i2s-hifi-0
card 2: Headphones [bcm2835 Headphones], device 0: bcm2835 Headphones
```

### Configuration Options

```yaml
# Use system default (may not work in Docker)
audio_device: ""

# Use 3.5mm headphone jack (recommended)
audio_device: plughw:Headphones

# Use first HDMI output
audio_device: plughw:vc4hdmi0

# Direct hardware access (requires permissions)
audio_device: hw:2,0
```

:::tip[Use Card Names]
Use `plughw:Headphones` instead of `plughw:2,0`. Card numbers can change between reboots, but names are stable.
:::

## Device Naming

| Format | Description | Example |
|--------|-------------|---------|
| `hw:N,D` | Direct hardware, card N device D | `hw:2,0` |
| `plughw:N,D` | With format conversion | `plughw:2,0` |
| `plughw:Name` | Using card name | `plughw:Headphones` |
| `default` | System default | `default` |

**Prefer `plughw:`** over `hw:` - it provides automatic sample rate and format conversion.

## Testing Audio

### Quick Test

```bash
# Test with speaker-test
speaker-test -c2 -t wav -D plughw:Headphones

# Play the actual file
aplay -D plughw:Headphones /usr/local/share/dnsfail/media/fail.wav
```

### In Docker

```bash
docker compose -f docker-compose.prod.yml exec dns-counter \
    aplay -D plughw:Headphones /usr/local/share/dnsfail/media/fail.wav
```

## Volume Control

### Check Volume

```bash
amixer
# or
alsamixer
```

### Set Volume

```bash
# Set to 80%
amixer set Master 80%

# Set headphone output
amixer set Headphone 80%
```

## Custom Audio Files

### Replace the Default

```bash
# Copy your WAV file
sudo cp my-sound.wav /usr/local/share/dnsfail/media/fail.wav

# Restart service
sudo systemctl restart dns_counter
```

### Use a Different File

```yaml
# config.yaml
audio_file: /path/to/your/custom-sound.wav
```

### Convert MP3 to WAV

```bash
# Install ffmpeg
sudo apt install ffmpeg

# Convert
ffmpeg -i input.mp3 -acodec pcm_s16le -ar 44100 output.wav
```

## Docker Audio Permissions

:::danger[Required for Docker]
Docker containers cannot access the Pi's headphone audio by default.
:::

### Create udev Rule

```bash
echo 'KERNEL=="pcmC2*", MODE="0666"
KERNEL=="controlC2", MODE="0666"' | sudo tee /etc/udev/rules.d/99-alsa-permissions.rules
```

### Apply Permissions

```bash
# Reload udev rules
sudo udevadm control --reload-rules

# Apply immediately (without reboot)
sudo chmod 666 /dev/snd/pcmC2D0p /dev/snd/controlC2
```

### Why This Is Needed

The headphone jack device (`/dev/snd/pcmC2D0p`) has restrictive permissions:

| Before | After |
|--------|-------|
| `crw-rw---- root audio` | `crw-rw-rw- root audio` |

The container runs as root but isn't in the `audio` group.

## Troubleshooting

### No Sound

1. **Check device exists:**
   ```bash
   aplay -l
   ```

2. **Check volume:**
   ```bash
   amixer
   ```

3. **Check file format:**
   ```bash
   file /usr/local/share/dnsfail/media/fail.wav
   # Should show: RIFF (little-endian) data, WAVE audio
   ```

4. **Test directly:**
   ```bash
   aplay -D plughw:Headphones /usr/local/share/dnsfail/media/fail.wav
   ```

### "Cannot get card index"

In Docker, this means device permissions. See [Docker Audio Permissions](#docker-audio-permissions).

### Wrong Output Device

Audio going to HDMI instead of speakers:

```bash
# Force headphone output
sudo raspi-config
# Advanced Options → Audio → Force 3.5mm jack
```

Or in config:
```yaml
audio_device: plughw:Headphones
```

### "audio open error: Device or resource busy"

Another application is using the audio device:

```bash
# Find what's using it
fuser -v /dev/snd/*

# Kill the process or wait for it to finish
```
