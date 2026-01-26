---
title: Common Issues
description: Troubleshooting common problems with the DNS Incident Timer.
---

# Common Issues

Quick solutions to frequently encountered problems.

## Display Issues

### Display Not Lighting Up

**Symptoms:** LED matrix stays dark or shows nothing.

**Solutions:**

1. **Check power:**
   - Matrix needs 5V power through the bonnet
   - Verify power supply provides enough current (5A+ recommended)

2. **Check connections:**
   - Matrix ribbon cable properly seated
   - HAT/Bonnet properly attached to GPIO header

3. **Check logs:**
   ```bash
   sudo journalctl -u dns_counter -n 50 | grep -i matrix
   ```

### Display Shows Garbage

**Symptoms:** Random colors, flickering, or wrong content.

**Solutions:**

1. **Reduce brightness:**
   ```yaml
   brightness: 50  # Lower value
   ```

2. **Check power stability:**
   - Use separate power supply for matrix
   - Don't power matrix through Pi

3. **Check ribbon cable:**
   - Ensure proper orientation
   - Replace if damaged

### Display Updates Slowly

**Symptoms:** Counter updates lag or stutter.

**Solutions:**

1. **Reduce CPU load:**
   - Check for other processes
   - Consider Pi 4 if using Pi Zero

2. **Check logs for errors:**
   ```bash
   sudo journalctl -u dns_counter -f
   ```

## Button Issues

### Button Not Responding

**Symptoms:** Pressing button does nothing.

**Solutions:**

1. **Check wiring:**
   ```bash
   # Read GPIO state (1 = released, 0 = pressed)
   gpioget gpiochip0 19
   ```

2. **Check pin configuration:**
   ```yaml
   gpio_pin: 19  # Verify correct pin
   ```

3. **Check logs:**
   ```bash
   sudo journalctl -u dns_counter | grep -i button
   ```

4. **Test GPIO directly:**
   ```bash
   gpiomon gpiochip0 19
   # Press button - should show events
   ```

### Button Triggers Multiple Times

**Symptoms:** Single press registers as multiple presses.

**Solutions:**

1. **Check for loose connections**
2. **Verify using momentary switch** (not toggle)
3. **Check for electrical noise** - add capacitor if needed

### Button Works But No Audio

**Symptoms:** Counter resets but no sound plays.

See [Audio Issues](#audio-issues) below.

## Audio Issues

### No Sound At All

**Symptoms:** Button press detected but no audio.

**Solutions:**

1. **Check audio device:**
   ```bash
   aplay -l
   ```

2. **Test audio manually:**
   ```bash
   aplay -D plughw:Headphones /usr/local/share/dnsfail/media/fail.wav
   ```

3. **Check volume:**
   ```bash
   amixer
   alsamixer
   ```

4. **Verify file exists:**
   ```bash
   ls -la /usr/local/share/dnsfail/media/
   ```

### "Cannot get card index" Error

**Symptoms:** Log shows ALSA card index error.

**Solutions:**

1. **Use card name instead of number:**
   ```yaml
   audio_device: plughw:Headphones
   ```

2. **For Docker, set permissions:**
   ```bash
   sudo chmod 666 /dev/snd/pcmC2D0p /dev/snd/controlC2
   ```

### Audio Goes to Wrong Output

**Symptoms:** Sound plays through HDMI instead of speakers.

**Solutions:**

1. **Set audio device explicitly:**
   ```yaml
   audio_device: plughw:Headphones
   ```

2. **Or use raspi-config:**
   ```bash
   sudo raspi-config
   # System Options → Audio → 3.5mm jack
   ```

## Service Issues

### Service Won't Start

**Symptoms:** `systemctl status` shows failed.

**Solutions:**

1. **Check logs:**
   ```bash
   sudo journalctl -u dns_counter -n 100
   ```

2. **Verify files exist:**
   ```bash
   ls -la /opt/dnsfail/
   ls -la /etc/dnsfail/config.yaml
   ```

3. **Check permissions:**
   ```bash
   sudo -u root /opt/dnsfail/venv/bin/python /opt/dnsfail/dns_counter.py --help
   ```

### Service Crashes After Start

**Symptoms:** Service starts then immediately stops.

**Solutions:**

1. **Check for Python errors:**
   ```bash
   sudo journalctl -u dns_counter -n 100
   ```

2. **Run manually to see errors:**
   ```bash
   sudo /opt/dnsfail/venv/bin/python /opt/dnsfail/dns_counter.py
   ```

3. **Check config syntax:**
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('/etc/dnsfail/config.yaml'))"
   ```

### Service Starts But Nothing Works

**Symptoms:** Service running but no display/button/audio.

**Solutions:**

1. **Check for hardware access:**
   ```bash
   # Check if user can access GPIO
   groups
   # Should include: gpio, audio
   ```

2. **Run as root to test:**
   ```bash
   sudo /opt/dnsfail/venv/bin/python /opt/dnsfail/dns_counter.py
   ```

## Persistence Issues

### Counter Resets on Reboot

**Symptoms:** Timer starts from 0 after every reboot.

**Solutions:**

1. **Check persistence file location:**
   ```bash
   ls -la /usr/local/share/dnsfail/
   ```

2. **Check write permissions:**
   ```bash
   touch /usr/local/share/dnsfail/test
   rm /usr/local/share/dnsfail/test
   ```

3. **Verify config:**
   ```yaml
   persistence_file: /usr/local/share/dnsfail/last_reset.json
   ```

### "Permission denied" for State File

**Symptoms:** Log shows can't write state file.

**Solutions:**

```bash
sudo mkdir -p /usr/local/share/dnsfail
sudo chmod 755 /usr/local/share/dnsfail
```

## Getting More Help

If none of these solutions work:

1. **Collect debug logs:**
   ```bash
   sudo journalctl -u dns_counter > dns_counter_debug.log
   ```

2. **Open an issue:**
   - [GitHub Issues](https://github.com/asachs01/dnsfail/issues)
   - Include logs and configuration
