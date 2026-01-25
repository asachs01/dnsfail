# DNS Failure Counter

A Raspberry Pi-powered LED matrix display that shows the time since the last DNS failure. Features a physical reset button to track new incidents and plays a sound effect when reset.

## Bill of Materials

### Required Hardware
1. Raspberry Pi 4 (any memory size)
2. [Adafruit RGB Matrix Bonnet](https://www.adafruit.com/product/3211)
3. [64x32 RGB LED Matrix - 4mm pitch](https://www.adafruit.com/product/2278)
4. Momentary Push Button (any standard normally-open button)
5. Jumper wires (at least 2)
6. 5V 4A (minimum) Power Supply for LED Matrix
7. MicroSD card (8GB minimum)
8. MicroUSB cable for Raspberry Pi power
9. Speakers or headphones for audio output

### Required Tools
1. Soldering iron and solder
2. Wire strippers
3. Small Phillips head screwdriver
4. (Optional) Heat shrink tubing

## Installation

### 1. Hardware Assembly

1. **Prepare the RGB Matrix Bonnet:**
   - Solder the RGB Matrix Bonnet to your Raspberry Pi following [Adafruit's guide](https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi/assembly)

2. **Connect the Button:**
   - Solder or connect one wire to GPIO19 on the RGB Matrix Bonnet
   - Solder or connect the other wire to any GND pin on the bonnet
   - Connect these wires to your momentary push button

3. **Connect the LED Matrix:**
   - Connect the RGB Matrix to the Bonnet using the included ribbon cable
   - Connect power to the Matrix using the terminal block on the Bonnet

4. **Connect Audio:**
   - Connect speakers or headphones to the Raspberry Pi's 3.5mm audio jack

### 2. Software Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/dnsfail.git
   cd dnsfail
   ```

2. **Run the Installation Script:**
   ```bash
   sudo chmod +x install.sh
   sudo ./install.sh
   ```

3. **Reboot the System:**
   ```bash
   sudo reboot
   ```

## Docker Development Environment

For development and testing without physical hardware:

### Quick Start

```bash
# Build and run application in mock mode
docker-compose up app

# Run tests
docker-compose --profile test up test

# Interactive development
docker-compose run --rm app /bin/bash
```

### Mock Mode Features

- **No hardware dependencies required** - Runs completely in software
- **Logs written to `./logs/` directory** - Persistent across container restarts
- **State persisted to `/tmp/last_reset.json`** - Counter state survives container restarts
- **Simulates button press** via `MOCK_BUTTON_PRESS=1` environment variable

### Development Workflow

1. **Edit `dns_counter.py` locally** - Changes reflect immediately in running container (volume mount)
2. **View logs**: `docker-compose logs -f app`
3. **Run tests**: `docker-compose --profile test up test`
4. **Simulate button press**:
   ```bash
   MOCK_BUTTON_PRESS=1 docker-compose up app
   ```
5. **Stop container**: `docker-compose down`

### Running Tests Locally

```bash
# Run all tests in Docker
docker-compose --profile test up test

# Run specific test file
docker-compose run --rm test pytest tests/test_docker_mock.py -v

# Run with coverage
docker-compose run --rm test pytest --cov=dns_counter tests/
```

### 3. Configuration

1. **Test the Display:**
   The display should start automatically after reboot. If not:
   ```bash
   sudo systemctl status dns_counter
   ```

2. **Test the Button:**
   Press the button - you should hear a sound effect and the counter should reset

3. **Adjust Audio (if needed):**
   ```bash
   alsamixer  # Use this to adjust volume
   ```

## Troubleshooting

1. **Display Issues:**
   - Check ribbon cable connection
   - Verify power supply is adequate
   - Run `sudo systemctl status dns_counter` for logs

2. **Button Not Working:**
   - Check wire connections
   - Verify GPIO permissions: `sudo chmod 660 /dev/gpiochip0`

3. **No Sound:**
   - Check audio connections
   - Verify volume: `alsamixer`
   - Test audio: `aplay /usr/local/share/dnsfail/media/fail.wav`

4. **Service Not Starting:**
   - Check logs: `journalctl -u dns_counter`
   - Verify permissions: `ls -l /usr/local/share/dnsfail`

## Maintenance

- Logs are available via:
  ```bash
  journalctl -u dns_counter
  ```
- Service can be restarted with:
  ```bash
  sudo systemctl restart dns_counter
  ```

## License

[Your chosen license]