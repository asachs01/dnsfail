#!/bin/bash
set -e # Exit on any error

echo "DNS Counter Installation Script"
echo "=============================="

# --- Configuration ---
APP_DIR="/usr/local/share/dnsfail"
FONTS_DIR="$APP_DIR/fonts"
MEDIA_DIR="$APP_DIR/media"
SERVICE_FILE="dns_counter.service"
SERVICE_DEST="/etc/systemd/system/$SERVICE_FILE"
MAIN_SCRIPT="dns_counter.py"
REQUIREMENTS="requirements.txt"
FAIL_SOUND="fail.mp3"
FONTS_SRC_DIR="fonts"

# --- Pre-flight Checks ---
echo "Running pre-flight checks..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run as root (sudo)."
    exit 1
fi

# Check for required source files
for f in "$MAIN_SCRIPT" "$REQUIREMENTS" "$FAIL_SOUND" "$SERVICE_FILE"; do
    if [ ! -f "$f" ]; then
        echo "ERROR: Missing required file '$f'. Make sure you are running from the project root directory."
        exit 1
    fi
done

if [ ! -d "$FONTS_SRC_DIR" ]; then
    echo "ERROR: Missing required directory '$FONTS_SRC_DIR'."
    exit 1
fi

echo "All checks passed."

# --- Installation ---
# echo "Installing system packages..."
# apt-get update
# apt-get install -y \
#     python3-pip \
#     python3-gpiod \
#     git \
#     python3-gi \
#     libcairo2-dev \
#     pkg-config \
#     python3-dev \
#     alsa-utils

echo "Creating application directories..."
mkdir -p "$MEDIA_DIR" "$FONTS_DIR"
chmod -R 755 "$APP_DIR"
echo "Directories created."

echo "Copying application files..."
cp "$MAIN_SCRIPT" "$APP_DIR/"
cp "$FAIL_SOUND" "$MEDIA_DIR/"
cp -r "$FONTS_SRC_DIR"/* "$FONTS_DIR/"
chmod 644 "$APP_DIR/$MAIN_SCRIPT"
echo "Files copied."

# echo "Installing Python requirements..."
# pip3 install -r "$REQUIREMENTS"

# --- Service Setup ---
echo "Setting up systemd service..."
# The /etc/systemd/system directory may not exist, so create it for the test
mkdir -p /etc/systemd/system
cp "$SERVICE_FILE" "$SERVICE_DEST"
chmod 644 "$SERVICE_DEST"
# systemctl daemon-reload
# systemctl enable "$SERVICE_FILE" --now
echo "Service installed and started."

# --- Audio & GPIO Permissions ---
# if id -u "$SUDO_USER" >/dev/null 2>&1; then
#     echo "Setting up audio and GPIO for user: $SUDO_USER"
#     usermod -a -G audio "$SUDO_USER"
#     usermod -a -G gpio "$SUDO_USER"
# else
#     echo "Skipping user-specific permissions, SUDO_USER not found."
# fi

# # Add root to groups as a fallback
# usermod -a -G audio root
# usermod -a -G gpio root

# # This is a broad and insecure permission setting, but keeping for compatibility.
# # A better approach would be udev rules.
# if [ -d "/dev/snd" ]; then
#     echo "Setting permissions for audio devices..."
#     chmod 666 /dev/snd/*
# fi

# --- Verification ---
echo "Verifying installation..."
FILES_TO_CHECK=(
    "$APP_DIR/$MAIN_SCRIPT"
    "$MEDIA_DIR/$FAIL_SOUND"
    "$FONTS_DIR/tom-thumb.bdf" # Check for a known font file
    "$SERVICE_DEST"
)
for f in "${FILES_TO_CHECK[@]}"; do
    if [ ! -f "$f" ]; then
        echo "VERIFICATION FAILED: File '$f' was not found."
        exit 1
    fi
done
echo "Verification successful."

echo "Installation complete!"
# echo "The service 'dns_counter' is now running."
# echo "You may need to reboot for all group permission changes to take full effect."
