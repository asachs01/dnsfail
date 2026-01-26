---
title: Docker Issues
description: Troubleshooting Docker-specific problems with the DNS Incident Timer.
---

# Docker Issues

Solutions for problems specific to running the DNS Incident Timer in Docker.

## Audio Issues

### "Cannot get card index for Headphones"

**Symptoms:**
```
ALSA lib confmisc.c:165:(snd_config_get_card) Cannot get card index for Headphones
aplay: main:850: audio open error: No such file or directory
```

**Cause:** The container can't access the audio device due to restrictive permissions on the host.

**Solution:**

1. **Create udev rule (persistent):**
   ```bash
   echo 'KERNEL=="pcmC2*", MODE="0666"
   KERNEL=="controlC2", MODE="0666"' | sudo tee /etc/udev/rules.d/99-alsa-permissions.rules

   sudo udevadm control --reload-rules
   ```

2. **Apply immediately:**
   ```bash
   sudo chmod 666 /dev/snd/pcmC2D0p /dev/snd/controlC2
   ```

3. **Restart container:**
   ```bash
   docker compose -f docker-compose.prod.yml down
   docker compose -f docker-compose.prod.yml up -d
   ```

### Audio Works in Exec But Not From Button

**Symptoms:**
- `docker exec ... aplay` works
- Button press doesn't produce sound

**Cause:** The main Python process and `docker exec` have different device visibility.

**Solutions:**

1. **Ensure udev rule is applied** (see above)

2. **Verify card is visible at startup:**
   Check logs for:
   ```
   Audio devices ready after 1 attempts
   ```

3. **Check audio device config:**
   ```yaml
   audio_device: plughw:Headphones
   ```

### "Cannot get card index for 2"

**Symptoms:** Error references card number instead of name.

**Solution:** Use card name instead:

```yaml
# Wrong
audio_device: plughw:2,0

# Correct
audio_device: plughw:Headphones
```

Card numbers can change; names are stable.

## GPIO Issues

### "'Chip' object has no attribute 'get_line'"

**Symptoms:**
```
AttributeError: 'Chip' object has no attribute 'get_line'
```

**Cause:** The Docker image has gpiod v2, but the code was written for v1 API.

**Solution:**

Update to the latest code which supports both APIs:

```bash
git pull origin main
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
```

Check logs for:
```
Using gpiod v2 API
GPIO setup successful with pull-up enabled
```

### Button Not Detected

**Symptoms:** No button events in logs.

**Solutions:**

1. **Verify device mapping:**
   ```yaml
   devices:
     - /dev/gpiochip0:/dev/gpiochip0
   ```

2. **Check privileged mode:**
   ```yaml
   privileged: true
   ```

3. **Test GPIO from container:**
   ```bash
   docker compose -f docker-compose.prod.yml exec dns-counter \
       python3 -c "import gpiod; print(gpiod.Chip('/dev/gpiochip0'))"
   ```

## Build Issues

### Build Fails at rgbmatrix

**Symptoms:** Build fails during `rpi-rgb-led-matrix` compilation.

**Cause:** Missing Pillow shim headers.

**Solution:** The Dockerfile should create stub files. Verify the Dockerfile has:

```dockerfile
printf '%s\n' '#ifndef SHIMS_PIL_H' ... > rgbmatrix/shims/pillow.h
printf '%s\n' '#include "pillow.h"' ... > rgbmatrix/shims/pillow.c
```

### Image Very Large

**Symptoms:** Docker image is several GB.

**Solution:** Use multi-stage builds and clean up:

```bash
# Remove build cache
docker builder prune

# Rebuild
docker compose -f docker-compose.prod.yml build --no-cache
```

### Cached Layers Not Updating

**Symptoms:** Code changes not reflected after rebuild.

**Solution:**

```bash
# Force rebuild without cache
docker compose -f docker-compose.prod.yml build --no-cache

# Or remove old images
docker compose -f docker-compose.prod.yml down --rmi local
docker compose -f docker-compose.prod.yml up -d --build
```

## Container Issues

### Container Exits Immediately

**Symptoms:** Container starts then exits.

**Solutions:**

1. **Check logs:**
   ```bash
   docker compose -f docker-compose.prod.yml logs
   ```

2. **Common causes:**
   - Missing config file
   - Invalid YAML syntax
   - Missing persistence directory

3. **Verify mounts exist:**
   ```bash
   ls -la /usr/local/share/dnsfail/
   ```

### Container Can't Access Network

**Symptoms:** Web interface not accessible.

**Solution:** Verify `network_mode: host` in compose file:

```yaml
services:
  dns-counter:
    network_mode: host
```

### Logs Full of Syslog Errors

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory
# References to /dev/log
```

**Cause:** Container doesn't have syslog daemon.

**Impact:** Cosmetic only - functionality not affected.

**Solution:** These can be ignored. The important logs still appear.

## Permission Issues

### "Permission denied" Errors

**Symptoms:** Various permission errors in logs.

**Solutions:**

1. **Use privileged mode:**
   ```yaml
   privileged: true
   ```

2. **Check device permissions on host:**
   ```bash
   ls -la /dev/snd/
   ls -la /dev/gpiochip0
   ```

3. **Check volume permissions:**
   ```bash
   ls -la /usr/local/share/dnsfail/
   ```

### Can't Write State File

**Symptoms:** Timer resets on container restart.

**Solution:**

1. **Create directory on host:**
   ```bash
   sudo mkdir -p /usr/local/share/dnsfail
   sudo chmod 777 /usr/local/share/dnsfail
   ```

2. **Verify volume mount:**
   ```yaml
   volumes:
     - /usr/local/share/dnsfail:/usr/local/share/dnsfail
   ```

## Debugging Tips

### View Real-time Logs

```bash
docker compose -f docker-compose.prod.yml logs -f
```

### Execute Commands in Container

```bash
# Get a shell
docker compose -f docker-compose.prod.yml exec dns-counter bash

# Run specific command
docker compose -f docker-compose.prod.yml exec dns-counter aplay -l
```

### Check Container Status

```bash
docker compose -f docker-compose.prod.yml ps
```

### View Container Details

```bash
docker inspect dnsfail-dns-counter-1
```

### Compare Exec vs Main Process

Test from inside container vs exec:

```bash
# From exec (new process)
docker exec dnsfail-dns-counter-1 aplay -l

# What main process sees (in logs)
docker logs dnsfail-dns-counter-1 | grep -i audio
```

## Complete Reset

If all else fails, start fresh:

```bash
# Stop and remove everything
docker compose -f docker-compose.prod.yml down -v --rmi local

# Remove any cached data
sudo rm -rf /usr/local/share/dnsfail/

# Recreate directory
sudo mkdir -p /usr/local/share/dnsfail
sudo chmod 777 /usr/local/share/dnsfail

# Set audio permissions
sudo chmod 666 /dev/snd/pcmC2D0p /dev/snd/controlC2

# Rebuild from scratch
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
```
