---
title: Docker Deployment
description: Run the DNS Incident Timer in a Docker container with hardware access.
---

# Docker Deployment

Run the DNS Incident Timer in a Docker container while maintaining access to the LED matrix, GPIO, and audio hardware.

## Prerequisites

- Docker and Docker Compose installed on the Pi
- Hardware connected (LED matrix, button, speakers)

### Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in for group changes
```

## Quick Start

```bash
# Clone the repository
git clone https://github.com/asachs01/dnsfail.git
cd dnsfail

# Set up audio permissions (required once)
echo 'KERNEL=="pcmC2*", MODE="0666"
KERNEL=="controlC2", MODE="0666"' | sudo tee /etc/udev/rules.d/99-alsa-permissions.rules
sudo udevadm control --reload-rules

# Start the container
docker compose -f docker-compose.prod.yml up -d
```

## Configuration Files

### docker-compose.prod.yml

The production compose file configures hardware access:

```yaml
services:
  dns-counter:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    entrypoint: ["python", "dns_counter.py", "--config", "/app/config.yaml"]
    volumes:
      - ./config.docker.yaml:/app/config.yaml
      - /usr/local/share/dnsfail:/usr/local/share/dnsfail
      - ./logs:/app/logs
    devices:
      - /dev/snd:/dev/snd        # Audio devices
      - /dev/gpiochip0:/dev/gpiochip0  # GPIO
    environment:
      - MOCK_MODE=0
      - PYTHONUNBUFFERED=1
    privileged: true
    restart: unless-stopped
    network_mode: host
```

### config.docker.yaml

Container-specific configuration:

```yaml
gpio_pin: 19
brightness: 80
audio_file: /usr/local/share/dnsfail/media/fail.wav
audio_device: plughw:Headphones  # Use card name, not number
web_port: 5000
persistence_file: /usr/local/share/dnsfail/last_reset.json
log_level: INFO
```

## Audio Device Permissions

:::caution[Required Step]
Docker containers cannot access the Pi's headphone audio device without special permissions.
:::

The bcm2835 Headphones device (`/dev/snd/pcmC2D0p`) has restrictive permissions by default. You must create a udev rule:

```bash
# Create udev rule for persistent permissions
echo 'KERNEL=="pcmC2*", MODE="0666"
KERNEL=="controlC2", MODE="0666"' | sudo tee /etc/udev/rules.d/99-alsa-permissions.rules

# Reload rules
sudo udevadm control --reload-rules

# Apply immediately (without reboot)
sudo chmod 666 /dev/snd/pcmC2D0p /dev/snd/controlC2
```

### Why This Is Needed

| Device | Default Permissions | After Fix |
|--------|-------------------|-----------|
| pcmC0D0p (HDMI) | `rw-rw-rw-` (world) | unchanged |
| pcmC2D0p (Headphones) | `rw-rw----` (audio group) | `rw-rw-rw-` |

The container runs as root but isn't in the `audio` group, so it can't access group-only devices.

## Building the Image

The Dockerfile uses multi-stage builds:

```bash
# Build production image
docker compose -f docker-compose.prod.yml build

# Force rebuild (no cache)
docker compose -f docker-compose.prod.yml build --no-cache
```

### Build Stages

1. **base**: Python with common dependencies
2. **development**: Mock mode for testing
3. **production**: Full hardware support with rgbmatrix and gpiod

## Managing the Container

```bash
# Start
docker compose -f docker-compose.prod.yml up -d

# Stop
docker compose -f docker-compose.prod.yml down

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart
docker compose -f docker-compose.prod.yml restart

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build
```

## Testing

### Verify Audio

```bash
# List audio devices
docker compose -f docker-compose.prod.yml exec dns-counter aplay -l

# Test playback
docker compose -f docker-compose.prod.yml exec dns-counter \
    aplay -D plughw:Headphones /usr/local/share/dnsfail/media/fail.wav
```

### Verify GPIO

```bash
# Check logs for GPIO status
docker compose -f docker-compose.prod.yml logs | grep -i gpio

# Should see: "Using gpiod v2 API"
# Should see: "GPIO setup successful"
```

## Development Mode

For testing without hardware:

```bash
# Use development compose file
docker compose up -d

# This runs in mock mode with simulated hardware
```

## Troubleshooting

### "Cannot get card index for Headphones"

Audio device permissions issue. See [Audio Device Permissions](#audio-device-permissions) above.

### "Chip object has no attribute 'get_line'"

The container's gpiod library is v2, but code was written for v1. Update to the latest code which supports both APIs:

```bash
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
```

### Button Detected But No Audio

Check if the audio file exists and is WAV format:

```bash
docker compose -f docker-compose.prod.yml exec dns-counter \
    ls -la /usr/local/share/dnsfail/media/
```

### Container Exits Immediately

Check logs for startup errors:

```bash
docker compose -f docker-compose.prod.yml logs
```

Common causes:
- Missing `/usr/local/share/dnsfail` directory on host
- Config file syntax errors

## Next Steps

- [Configuration Options](/dnsfail/configuration/options/) - Customize settings
- [Docker Issues](/dnsfail/troubleshooting/docker/) - More troubleshooting
