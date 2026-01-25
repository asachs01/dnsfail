#!/usr/bin/env python3
import os
import gpiod  # Replace lgpio with gpiod
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from PIL import Image, ImageDraw, ImageFont
import time
import datetime
import threading
from datetime import datetime, timedelta
import logging
from logging.handlers import SysLogHandler
import subprocess
import json
import tempfile

# Persistence file for last_reset timestamp
PERSISTENCE_FILE = '/usr/local/share/dnsfail/last_reset.json'

# Set up logging with more detail
logger = logging.getLogger('dns_counter')
logger.setLevel(logging.DEBUG)  # Change to DEBUG level

# Add console handler with detailed formatting
console = logging.StreamHandler()
console.setFormatter(logging.Formatter(
    '%(asctime)s dns_counter: %(levelname)s [%(filename)s:%(lineno)d] %(message)s'
))
logger.addHandler(console)

# Add syslog handler with detailed formatting
try:
    syslog = SysLogHandler(address='/dev/log', facility=SysLogHandler.LOG_DAEMON)
    syslog.setFormatter(logging.Formatter(
        'dns_counter[%(process)d]: %(levelname)s [%(filename)s:%(lineno)d] %(message)s'
    ))
    logger.addHandler(syslog)
except (OSError, IOError) as e:
    logger.warning(f"Could not initialize syslog handler: {e}")

class DNSCounter(object):
    def __init__(self):
        self.parser = self.create_parser()
        self.args = self.parser.parse_args()

        logger.info("Initializing RGB Matrix...")
        options = RGBMatrixOptions()
        options.rows = 32
        options.cols = 64
        options.chain_length = self.args.led_chain
        options.parallel = self.args.led_parallel
        options.row_address_type = self.args.led_row_addr
        options.multiplexing = self.args.led_multiplexing
        options.pwm_bits = 11  # Maximum PWM bits for smoother transitions
        options.brightness = 80  # Lower brightness can help with flicker
        options.pwm_lsb_nanoseconds = 130  # Default timing
        options.led_rgb_sequence = self.args.led_rgb_sequence
        options.pixel_mapper_config = self.args.led_pixel_mapper
        options.gpio_slowdown = 3  # Increase slowdown to reduce flicker
        options.hardware_mapping = 'adafruit-hat'
        options.scan_mode = 1  # Progressive scan mode
        options.disable_hardware_pulsing = False  # Enable hardware pulsing
        options.drop_privileges = True  # Allow privilege dropping

        try:
            self.matrix = RGBMatrix(options=options)
            logger.info("Matrix initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize matrix: {e}")
            raise

        # Initialize the last reset time from persistence or current time
        self.last_reset = self.load_state()
        logger.info(f"Counter initialized with start time: {self.last_reset}")

        # Initialize GPIO for button
        self.BUTTON_PIN = 19  # Using GPIO19 which is free
        self.chip = None
        self.line = None
        self.setup_gpio()

    def save_state(self):
        """Saves the last_reset timestamp to a JSON file atomically."""
        try:
            data = {'last_reset': self.last_reset.isoformat(), 'version': 1}
            # Use a temporary file for atomic write
            with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=os.path.dirname(PERSISTENCE_FILE), encoding='utf-8') as tf:
                json.dump(data, tf)
            os.rename(tf.name, PERSISTENCE_FILE)
            logger.debug(f"Saved state to {PERSISTENCE_FILE}: {data}")
        except Exception as e:
            logger.error(f"Failed to save state to {PERSISTENCE_FILE}: {e}")

    def load_state(self):
                """Loads the last_reset timestamp from a JSON file.
        
                Returns:
                    datetime: The loaded datetime object, or datetime.now() if loading fails.
                """
                if not os.path.exists(PERSISTENCE_FILE):
                    logger.warning(f"Persistence file not found at {PERSISTENCE_FILE}. Initializing with current time.")
                    return datetime.now()
        
                try:
                    with open(PERSISTENCE_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    last_reset_str = data.get('last_reset')
                    if last_reset_str:
                        loaded_time = datetime.fromisoformat(last_reset_str)
                        logger.info(f"Loaded last_reset from {PERSISTENCE_FILE}: {loaded_time}")
                        return loaded_time
                    else:
                        logger.warning(f" 'last_reset' key not found in {PERSISTENCE_FILE}. Initializing with current time.")
                        return datetime.now()
                except json.JSONDecodeError as e:
                    logger.warning(f"Persistence file {PERSISTENCE_FILE} is corrupt ({e}). Initializing with current time.")
                    return datetime.now()
                except Exception as e:
                    logger.error(f"An unexpected error occurred while loading state from {PERSISTENCE_FILE}: {e}. Initializing with current time.")
                    return datetime.now()
        
            def create_parser(self):
        import argparse
        parser = argparse.ArgumentParser()

        # Matrix arguments
        parser.add_argument("--led-rows", action="store", help="Display rows. 16 for 16x32, 32 for 32x32. Default: 32", type=int, default=32)
        parser.add_argument("--led-cols", action="store", help="Panel columns. Typically 32 or 64. Default: 64", type=int, default=64)
        parser.add_argument("--led-chain", action="store", help="Daisy-chained boards. Default: 1", type=int, default=1)
        parser.add_argument("--led-parallel", action="store", help="For Plus-models or RPi2: parallel chains. 1..3. Default: 1", type=int, default=1)
        parser.add_argument("--led-pwm-bits", action="store", help="Bits used for PWM. Range 1..11. Default: 11", type=int, default=11)
        parser.add_argument("--led-brightness", action="store", help="Sets brightness level. Range: 1..100. Default: 100", type=int, default=100)
        parser.add_argument("--led-gpio-mapping", help="Hardware Mapping: regular, adafruit-hat, adafruit-hat-pwm" , choices=['regular', 'adafruit-hat', 'adafruit-hat-pwm'], type=str, default='adafruit-hat')
        parser.add_argument("--led-scan-mode", action="store", help="Progressive or interlaced scan. 0 = Progressive, 1 = Interlaced. Default: 1", type=int, default=1)
        parser.add_argument("--led-pwm-lsb-nanoseconds", action="store", help="Base time-unit for the on-time in the lowest significant bit in nanoseconds. Default: 130", type=int, default=130)
        parser.add_argument("--led-row-addr", action="store", help="Addressing of rows. Default: 0", type=int, default=0)
        parser.add_argument("--led-multiplexing", action="store", help="Multiplexing type: 0 = direct; 1 = strip; 2 = checker; 3 = spiral; 4 = Z-strip; 5 = ZnMirrorZStripe. Default: 0", type=int, default=0)
        parser.add_argument("--led-pixel-mapper", action="store", help="Apply pixel mappers. Default: \"\"", type=str, default="")
        parser.add_argument("--led-rgb-sequence", action="store", help="Switch if your matrix has led colors swapped. Default: RGB", type=str, default="RGB")
        parser.add_argument("--led-slowdown-gpio", action="store", help="Slowdown GPIO. Higher value, slower but less flicker. Range: 0..4", type=int, default=4)

        return parser

    def format_duration(self, duration):
        """Format duration to show all time units consistently"""
        # Calculate all time components
        total_seconds = int(duration.total_seconds())
        
        # Break down into units
        years = duration.days // 365
        months = (duration.days % 365) // 30
        days = (duration.days % 365) % 30
        hours = total_seconds // 3600 % 24
        minutes = total_seconds % 3600 // 60
        seconds = total_seconds % 60
        
        # Format as two lines with units, using 'mo' for months
        line1 = f"{years:02d}y {months:02d}mo {days:02d}d"
        line2 = f"{hours:02d}h {minutes:02d}m {seconds:02d}s"
        return (line1, line2)

    def get_max_font_size(self, draw, text, max_width, max_height, start_size=20):
        """Determine the largest font size that will fit the text in the given space"""
        font_size = start_size
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        
        while font_size > 6:  # Minimum readable size
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            if text_width <= max_width and text_height <= max_height:
                return font
            
            font_size -= 1
        
        return font

    def draw_text(self, draw, text, x, y, color, size_multiplier=1):
        """Draw text using our bitmap font"""
        current_x = x
        for char in text:
            if char in self.font_5x7:
                bitmap = self.font_5x7[char]
                for row in range(7):
                    for col in range(5):
                        if bitmap[col] & (1 << (6-row)):
                            pixel_x = current_x + (col * size_multiplier)
                            pixel_y = y + (row * size_multiplier)
                            if size_multiplier == 1:
                                draw.point((pixel_x, pixel_y), color)
                            else:
                                draw.rectangle(
                                    [pixel_x, pixel_y, 
                                     pixel_x + size_multiplier - 1, 
                                     pixel_y + size_multiplier - 1], 
                                    fill=color)
            current_x += (6 * size_multiplier)  # 5 pixels + 1 space between characters

    def test_display(self):
        """Test the display with a simple pattern"""
        canvas = self.matrix.CreateFrameCanvas()
        
        # Fill with red
        for x in range(64):
            for y in range(32):
                canvas.SetPixel(x, y, 255, 0, 0)
        
        canvas = self.matrix.SwapOnVSync(canvas)
        time.sleep(2)
        
        # Fill with green
        canvas.Clear()
        for x in range(64):
            for y in range(32):
                canvas.SetPixel(x, y, 0, 255, 0)
        
        canvas = self.matrix.SwapOnVSync(canvas)
        time.sleep(2)
        
        # Fill with blue
        canvas.Clear()
        for x in range(64):
            for y in range(32):
                canvas.SetPixel(x, y, 0, 0, 255)
        
        canvas = self.matrix.SwapOnVSync(canvas)
        time.sleep(2)
        
        canvas.Clear()
        self.matrix.SwapOnVSync(canvas)

    def run(self):
        try:
            logger.info("Starting display loop...")
            canvas = self.matrix.CreateFrameCanvas()
            
            # Use system font directory
            font_dir = "/usr/local/share/dnsfail/fonts"
            
            header_font = graphics.Font()
            header_font.LoadFont(os.path.join(font_dir, "6x10.bdf"))
            
            time_font = graphics.Font()
            time_font.LoadFont(os.path.join(font_dir, "5x8.bdf"))  # More readable size
            
            # Create colors
            white = graphics.Color(255, 255, 255)
            red = graphics.Color(255, 0, 0)
            
            while True:
                canvas.Clear()
                
                # Draw header text in two lines
                header_text1 = "DAYS SINCE"
                header_text2 = "DNS"
                
                # Draw headers
                graphics.DrawText(canvas, header_font, 
                               (64 - len(header_text1) * 6) // 2,
                               8,
                               white, header_text1)
                
                graphics.DrawText(canvas, header_font,
                               (64 - len(header_text2) * 6) // 2,
                               16,
                               white, header_text2)
                
                # Calculate and draw time in two lines
                duration = datetime.now() - self.last_reset
                time_line1, time_line2 = self.format_duration(duration)
                
                # Draw first line of time (MM:WW:DD)
                graphics.DrawText(canvas, time_font,
                               (64 - len(time_line1) * 5) // 2,
                               24,
                               red, time_line1)
                
                # Draw second line of time (HH:MM:SS)
                graphics.DrawText(canvas, time_font,
                               (64 - len(time_line2) * 5) // 2,
                               31,
                               red, time_line2)
                
                # Update the display
                canvas = self.matrix.SwapOnVSync(canvas)
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            if self.line:
                self.line.release()
            if self.chip:
                self.chip.close()
            self.matrix.Clear()
        except Exception as e:
            logger.error(f"Display error: {e}")
            if self.line:
                self.line.release()
            if self.chip:
                self.chip.close()
            self.matrix.Clear()
            raise

    def setup_gpio(self):
        try:
            # Open GPIO chip using gpiod
            self.chip = gpiod.Chip('/dev/gpiochip0')
            
            # Get the GPIO line and configure it as input with pull-up
            self.line = self.chip.get_line(self.BUTTON_PIN)
            self.line.request(consumer='dns_counter', 
                             type=gpiod.LINE_REQ_DIR_IN,
                             flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP)
            
            logger.info("GPIO setup successful with pull-up enabled")
            
            # Start a thread to check the button state
            self.button_thread = threading.Thread(target=self._check_button, daemon=True)
            self.button_thread.start()
            
        except Exception as e:
            logger.error(f"Unexpected GPIO error: {e}")
            logger.error("Try running: sudo chmod 660 /dev/gpiochip0")
            self.chip = None
            self.line = None

    def _check_button(self):
        """Thread function to check button state"""
        last_press = 0
        last_value = None
        logger.info("Button monitoring started")
        logger.info(f"Initial button state: {self.line.get_value()}")
        
        # Get absolute path to sound file
        sound_file = '/usr/local/share/dnsfail/media/fail.wav'
        logger.debug(f"Sound file path: {sound_file}")
        logger.debug(f"Sound file exists: {os.path.exists(sound_file)}")
        
        # Set up environment with /tmp as home
        env = os.environ.copy()
        env['HOME'] = '/tmp'  # Use /tmp which is world-writable
        env['XDG_RUNTIME_DIR'] = '/tmp'  # Also set XDG runtime dir
        
        while True:
            try:
                if self.line:
                    value = self.line.get_value()
                    if value != last_value:
                        logger.debug(f"Button state changed to: {value}")
                        last_value = value
                        
                        if value == 0:  # Button pressed (active low)
                            current_time = time.time()
                            if current_time - last_press > 0.3:  # Simple debounce
                                logger.info("Button press detected - Resetting counter")
                                self.last_reset = datetime.now()
                                self.save_state()  # Save the new reset time
                                try:
                                    logger.debug("Attempting to play sound...")
                                    result = subprocess.run([
                                        'aplay',
                                        sound_file
                                    ], stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       text=True,
                                       env=env)
                                    if result.returncode != 0:
                                        logger.error(f"Audio error: {result.stderr}")
                                    else:
                                        logger.debug("Sound playback completed successfully")
                                except Exception as e:
                                    logger.error(f"Error playing sound: {e}", exc_info=True)
                                last_press = current_time
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in button loop: {e}", exc_info=True)
                time.sleep(0.1)

if __name__ == "__main__":
    try:
        dns_counter = DNSCounter()
        dns_counter.run()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        raise 