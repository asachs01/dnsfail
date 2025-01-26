# DNS Failure Counter

A Raspberry Pi-powered LED matrix display that shows the time since the last DNS failure. Features a physical reset button to track new incidents.

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

### 2. Software Installation

1. **Install Required System Packages:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-gpiod git
   ```

2. **Clone the Repository:**
   ```bash
   cd /home/your_username
   git clone https://your-repo-url.git dnsfail
   cd dnsfail
   ```

3. **Install Python Dependencies:**
   ```bash
   sudo pip3 install -r requirements.txt
   ```

4. **Install RGB Matrix Library:**
   ```bash
   curl https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/rgb-matrix.sh > rgb-matrix.sh
   sudo bash rgb-matrix.sh
   ```
   - Choose "Regular" installation (not "Quality")
   - Choose "Convenience" when asked

5. **Set Up Font Directory:**
   ```bash
   sudo mkdir -p /usr/local/share/dnsfail/fonts
   sudo cp fonts/* /usr/local/share/dnsfail/fonts/
   ```

6. **Set Up Service:**
   ```bash
   sudo cp dns_counter.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable dns_counter
   ```

## Usage

### Manual Operation
1. Navigate to the project directory:
   ```bash
   cd /home/your_username/dnsfail
   ```

2. Run the counter:
   ```bash
   sudo python3 dns_counter.py
   ```

3. Press the button to reset the counter when a DNS failure occurs

### Service Operation
- Start the service:
  ```bash
  sudo systemctl start dns_counter
  ```

- Check service status:
  ```bash
  sudo systemctl status dns_counter
  ```

- View logs:
  ```bash
  sudo journalctl -u dns_counter -f
  ```

## Display Information

The display shows:
- "DAYS SINCE" on the top line
- "DNS" on the middle line
- Time duration on the bottom line

Time format changes based on duration:
- Minutes and seconds (e.g., "02m 30s")
- Hours, minutes, seconds (e.g., "01h 30m 45s")
- Days, hours, minutes (e.g., "2d 05h 30m")
- Weeks, days, hours (e.g., "1w 3d 12h")
- Months, days, hours (e.g., "2m 15d 06h")
- Years, months, days (e.g., "1y 2m 15d")

## Troubleshooting

1. **Permission Issues:**
   ```bash
   sudo chmod 660 /dev/gpiochip0
   sudo chown root:gpio /dev/gpiochip0
   ```

2. **Display Not Working:**
   - Check power supply (should be 5V 4A minimum)
   - Verify ribbon cable connection
   - Check RGB Matrix Bonnet installation

3. **Button Not Working:**
   - Verify wiring to GPIO19 and GND
   - Check button connections
   - Test button continuity with multimeter

## Maintenance

- Clean the LED matrix periodically with compressed air
- Check button connections monthly
- Update software as needed:
  ```bash
  cd /home/your_username/dnsfail
  git pull
  sudo systemctl restart dns_counter
  ``` 