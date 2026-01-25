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

## Development

### Running Tests

The project includes comprehensive unit tests for timer logic (duration formatting, persistence, and reset handling).

1. **Install Development Dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements-dev.txt
   ```

2. **Run All Tests:**
   ```bash
   pytest tests/ -v
   ```

3. **Run Tests with Coverage:**
   ```bash
   pytest tests/ --cov=dns_counter --cov-report=term-missing
   ```

4. **Coverage Target:**
   - Overall timer logic: >80% coverage
   - Tests are isolated and do not require hardware dependencies

### Test Structure
- `tests/test_timer.py`: Unit tests for timer functions
- `tests/conftest.py`: Pytest fixtures and hardware mocks
- Coverage reports available in `htmlcov/` directory

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