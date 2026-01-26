---
title: Quick Start
description: Get the DNS Incident Timer running in 5 minutes.
---

# Quick Start

Get your DNS Incident Timer up and running quickly.

## Prerequisites

- Raspberry Pi with Raspberry Pi OS installed
- Hardware assembled (see [Hardware Requirements](/getting-started/hardware/))
- SSH access to the Pi

## Installation

### Option 1: Native Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/asachs01/dnsfail.git
cd dnsfail

# Run the installer
sudo ./install.sh
```

The installer will:
1. Install system dependencies
2. Build the RGB matrix library
3. Install Python packages
4. Set up the systemd service
5. Enable the service to start on boot

### Option 2: Docker Installation

```bash
# Clone the repository
git clone https://github.com/asachs01/dnsfail.git
cd dnsfail

# Set up audio device permissions (required once)
echo 'KERNEL=="pcmC2*", MODE="0666"
KERNEL=="controlC2", MODE="0666"' | sudo tee /etc/udev/rules.d/99-alsa-permissions.rules
sudo udevadm control --reload-rules
sudo chmod 666 /dev/snd/pcmC2D0p /dev/snd/controlC2

# Start with Docker
docker compose -f docker-compose.prod.yml up -d
```

## Verify Installation

### Check Service Status

```bash
# For native installation
sudo systemctl status dns_counter

# For Docker
docker compose -f docker-compose.prod.yml logs -f
```

### Test the Button

1. Press the physical button connected to GPIO 19
2. You should hear the audio clip play
3. The display counter should reset to 0

### Test Audio

```bash
# Native
aplay /usr/local/share/dnsfail/media/fail.wav

# Docker
docker exec dnsfail-dns-counter-1 aplay -D plughw:Headphones /usr/local/share/dnsfail/media/fail.wav
```

## Configuration

The default configuration works for most setups. To customize:

```bash
# Edit the configuration file
sudo nano /etc/dnsfail/config.yaml
```

Key settings:
```yaml
gpio_pin: 19          # Button GPIO pin
brightness: 80        # LED brightness (1-100)
audio_file: /usr/local/share/dnsfail/media/fail.wav
```

Restart after changes:
```bash
# Native
sudo systemctl restart dns_counter

# Docker
docker compose -f docker-compose.prod.yml restart
```

## Troubleshooting

### Display Not Working

1. Check power to the LED matrix
2. Verify the matrix bonnet is properly seated
3. Check logs: `sudo journalctl -u dns_counter -f`

### Button Not Responding

1. Verify wiring to GPIO 19
2. Check logs for GPIO errors
3. Test with: `gpioget gpiochip0 19`

### No Audio

1. Check speaker connection
2. Verify audio device: `aplay -l`
3. Test audio: `speaker-test -c2 -t wav`

See [Troubleshooting](/troubleshooting/common-issues/) for more help.

## Next Steps

- [Configuration Options](/configuration/options/) - Customize behavior
- [Docker Deployment](/installation/docker/) - Production container setup
- [Architecture](/reference/architecture/) - How it all works
