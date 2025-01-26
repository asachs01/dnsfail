#!/usr/bin/env python3
import os
import gpiod  # Replace lgpio with gpiod
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from PIL import Image, ImageDraw, ImageFont
import time
import datetime
import threading
from datetime import datetime, timedelta

class DNSCounter(object):
    def __init__(self):
        self.parser = self.create_parser()
        self.args = self.parser.parse_args()

        print("Initializing RGB Matrix...")
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
            print("Matrix initialized successfully")
        except Exception as e:
            print(f"Failed to initialize matrix: {e}")
            raise

        # Initialize the last reset time
        self.last_reset = datetime.now()

        # Initialize GPIO for button
        self.BUTTON_PIN = 19  # Using GPIO19 which is free
        self.chip = None
        self.line = None
        self.setup_gpio()

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
        # Calculate all time components
        total_days = duration.days
        seconds = duration.seconds
        
        # Break down the components
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        # Start with just minutes and seconds
        if total_days == 0 and hours == 0:
            return f"{minutes:02d}m {seconds:02d}s"
        # Add hours when we get there
        elif total_days == 0:
            return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"
        # Add days when we get there
        elif total_days < 7:
            return f"{total_days}d {hours:02d}h {minutes:02d}m"
        # Add weeks
        elif total_days < 30:
            weeks = total_days // 7
            days = total_days % 7
            return f"{weeks}w {days}d {hours:02d}h"
        # Add months
        elif total_days < 365:
            months = total_days // 30
            days = total_days % 30
            return f"{months}m {days}d {hours:02d}h"
        # Add years
        else:
            years = total_days // 365
            days = total_days % 365
            months = days // 30
            return f"{years}y {months}m {days}d"

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
            print("Starting display loop...")
            canvas = self.matrix.CreateFrameCanvas()
            
            # Use system font directory
            font_dir = "/usr/local/share/dnsfail/fonts"
            
            header_font = graphics.Font()
            header_font.LoadFont(os.path.join(font_dir, "6x10.bdf"))
            
            time_font = graphics.Font()
            time_font.LoadFont(os.path.join(font_dir, "6x13.bdf"))
            
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
                               9,
                               white, header_text1)
                
                graphics.DrawText(canvas, header_font,
                               (64 - len(header_text2) * 6) // 2,
                               18,
                               white, header_text2)
                
                # Calculate and draw time
                duration = datetime.now() - self.last_reset
                time_text = self.format_duration(duration)
                graphics.DrawText(canvas, time_font,
                               (64 - len(time_text) * 6) // 2,
                               28,
                               red, time_text)
                
                # Update the display
                canvas = self.matrix.SwapOnVSync(canvas)
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("Shutting down...")
            if self.line:
                self.line.release()
            if self.chip:
                self.chip.close()
            self.matrix.Clear()
        except Exception as e:
            print(f"Display error: {e}")
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
            
            print("GPIO setup successful with pull-up enabled")
            
            # Start a thread to check the button state
            self.button_thread = threading.Thread(target=self._check_button, daemon=True)
            self.button_thread.start()
            
        except Exception as e:
            print(f"Unexpected GPIO error: {e}")
            print(f"Try running: sudo chmod 660 /dev/gpiochip0")
            self.chip = None
            self.line = None

    def _check_button(self):
        """Thread function to check button state"""
        last_press = 0
        last_value = None
        print("Button monitoring started")
        print("Initial button state:", self.line.get_value())
        print("Waiting for button presses (0 = pressed, 1 = not pressed)")
        
        while True:
            try:
                if self.line:
                    value = self.line.get_value()
                    if value != last_value:
                        print(f"Button state changed to: {value}")
                        last_value = value
                        
                        if value == 0:  # Button pressed (active low)
                            current_time = time.time()
                            if current_time - last_press > 0.3:  # Simple debounce
                                print("Button press detected!")
                                print("Resetting counter to 0...")
                                self.last_reset = datetime.now()
                                last_press = current_time
                time.sleep(0.1)
            except Exception as e:
                print(f"Error reading button: {e}")
                time.sleep(0.1)

if __name__ == "__main__":
    dns_counter = DNSCounter()
    try:
        dns_counter.run()
    except KeyboardInterrupt:
        print("Exiting...") 