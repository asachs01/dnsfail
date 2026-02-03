#!/bin/bash
# Wait for audio devices to be fully available before starting Python
# This prevents ALSA library caching issues where devices aren't visible
# to the running process if they weren't ready at startup

echo "=== Entrypoint starting ==="
echo "Date: $(date)"

# Wait for the ALSA devices to be fully initialized in the kernel
# The bcm2835 headphones driver can take several seconds to initialize
MAX_ATTEMPTS=60
ATTEMPT=0

echo "Waiting for audio devices to be fully initialized..."

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    # Check if Headphones appears in /proc/asound/cards (kernel level)
    if grep -q "Headphones" /proc/asound/cards 2>/dev/null; then
        # Also verify the device is accessible
        if aplay -l 2>&1 | grep -q "Headphones"; then
            echo "Audio devices ready after $((ATTEMPT + 1)) seconds"
            break
        fi
    fi
    ATTEMPT=$((ATTEMPT + 1))
    if [ $((ATTEMPT % 10)) -eq 0 ]; then
        echo "Still waiting for audio devices (attempt $ATTEMPT/$MAX_ATTEMPTS)..."
        echo "Current /proc/asound/cards:"
        cat /proc/asound/cards 2>/dev/null || echo "(not available)"
        echo "Current aplay -l:"
        aplay -l 2>&1 || echo "(failed)"
    fi
    sleep 1
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "Warning: Audio devices may not be fully available after $MAX_ATTEMPTS seconds"
    echo "Continuing anyway..."
fi

echo ""
echo "=== Starting Python application ==="
# Start the application - exec replaces this shell process
exec python dns_counter.py "$@"
