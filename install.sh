#!/bin/bash
set -e  # Exit on any error

echo "DNS Counter Installation Script"
echo "=============================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo)"
    exit 1
fi

echo "Installing system packages..."
apt-get update
apt-get install -y \
    python3-pip \
    python3-gpiod \
    git \
    python3-gi \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    alsa-utils

echo "Setting up audio..."
# Add current user to audio group
usermod -a -G audio $SUDO_USER
usermod -a -G audio root

# Set permissions for audio devices
chmod 666 /dev/snd/*

echo "Setting up GPIO permissions..."
# Add users to gpio group
usermod -a -G gpio $SUDO_USER
usermod -a -G gpio root

echo "Creating application directories..."
mkdir -p /usr/local/share/dnsfail/{media,fonts}
chmod -R 755 /usr/local/share/dnsfail

echo "Installing Python requirements..."
pip3 install -r requirements.txt

echo "Setting up service..."
cp dns_counter.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable dns_counter.service --now

echo "Installation complete!"
echo "Please reboot your system to ensure all changes take effect." 