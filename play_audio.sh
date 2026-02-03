#!/bin/bash
# Simple wrapper for audio playback
FILE="${2:-/usr/local/share/dnsfail/media/fail.wav}"
DEVICE="${1:-plughw:Headphones}"

exec aplay -D "$DEVICE" "$FILE"
