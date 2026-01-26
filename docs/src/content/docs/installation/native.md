---
title: Native Installation
description: Install the DNS Incident Timer directly on Raspberry Pi OS.
---

# Native Installation

Install the DNS Incident Timer directly on your Raspberry Pi for the best performance.

## Prerequisites

- Raspberry Pi with Raspberry Pi OS (64-bit recommended)
- Internet connection
- sudo access

## Automated Installation

The easiest way to install:

```bash
# Clone the repository
git clone https://github.com/asachs01/dnsfail.git
cd dnsfail

# Run the installer
sudo ./install.sh
```

### What the Installer Does

1. **System Dependencies**
   - `git`, `build-essential`, `python3-dev`
   - `libgpiod-dev` for GPIO access
   - `alsa-utils` for audio playback

2. **RGB Matrix Library**
   - Clones and builds `rpi-rgb-led-matrix`
   - Installs Python bindings

3. **Python Environment**
   - Creates virtualenv at `/opt/dnsfail/venv`
   - Installs requirements from `requirements.txt`

4. **Application Files**
   - Copies `dns_counter.py` to `/opt/dnsfail/`
   - Copies fonts to `/opt/dnsfail/fonts/`
   - Copies audio files to `/usr/local/share/dnsfail/media/`

5. **Configuration**
   - Creates `/etc/dnsfail/config.yaml`
   - Sets up persistence directory

6. **Systemd Service**
   - Installs `dns_counter.service`
   - Enables auto-start on boot

## Manual Installation

If you prefer manual control:

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install -y \
    git \
    build-essential \
    python3-dev \
    python3-pip \
    python3-venv \
    libgpiod-dev \
    alsa-utils
```

### 2. Build RGB Matrix Library

```bash
cd /tmp
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix
make -C lib
cd bindings/python
make build-python PYTHON=$(which python3)
sudo make install-python PYTHON=$(which python3)
```

### 3. Set Up Python Environment

```bash
sudo mkdir -p /opt/dnsfail
sudo python3 -m venv /opt/dnsfail/venv
source /opt/dnsfail/venv/bin/activate
pip install pyyaml flask gpiod
```

### 4. Install Application

```bash
# From the dnsfail repository directory
sudo cp dns_counter.py /opt/dnsfail/
sudo cp -r fonts /opt/dnsfail/
sudo mkdir -p /usr/local/share/dnsfail/media
sudo cp fail.wav /usr/local/share/dnsfail/media/
```

### 5. Create Configuration

```bash
sudo mkdir -p /etc/dnsfail
sudo tee /etc/dnsfail/config.yaml << 'EOF'
gpio_pin: 19
brightness: 80
audio_file: /usr/local/share/dnsfail/media/fail.wav
web_port: 5000
persistence_file: /usr/local/share/dnsfail/last_reset.json
log_level: INFO
EOF
```

### 6. Create Systemd Service

```bash
sudo tee /etc/systemd/system/dns_counter.service << 'EOF'
[Unit]
Description=DNS Counter Display Service
After=network.target

[Service]
Type=simple
ExecStart=/opt/dnsfail/venv/bin/python /opt/dnsfail/dns_counter.py --config /etc/dnsfail/config.yaml
WorkingDirectory=/opt/dnsfail
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable dns_counter
sudo systemctl start dns_counter
```

## Verify Installation

```bash
# Check service status
sudo systemctl status dns_counter

# View logs
sudo journalctl -u dns_counter -f

# Test audio
aplay /usr/local/share/dnsfail/media/fail.wav
```

## Updating

To update to the latest version:

```bash
cd dnsfail
git pull origin main
sudo ./install.sh
```

## Uninstalling

```bash
sudo systemctl stop dns_counter
sudo systemctl disable dns_counter
sudo rm /etc/systemd/system/dns_counter.service
sudo rm -rf /opt/dnsfail
sudo rm -rf /etc/dnsfail
sudo rm -rf /usr/local/share/dnsfail
sudo systemctl daemon-reload
```

## Next Steps

- [Configuration Options](/dnsfail/configuration/options/) - Customize settings
- [GPIO Setup](/dnsfail/configuration/gpio/) - Button configuration
- [Audio Setup](/dnsfail/configuration/audio/) - Audio configuration
