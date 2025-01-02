#!/usr/bin/env python3
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from PIL import Image, ImageDraw, ImageFont
import time
import datetime
import os
import threading
from datetime import datetime, timedelta

class DNSCounter(object):
    def __init__(self):
        self.parser = self.create_parser()
        self.args = self.parser.parse_args()

        options = RGBMatrixOptions()
        options.rows = 32
        options.cols = 64
        options.chain_length = self.args.led_chain
        options.parallel = self.args.led_parallel
        options.row_address_type = self.args.led_row_addr
        options.multiplexing = self.args.led_multiplexing
        options.pwm_bits = self.args.led_pwm_bits
        options.brightness = self.args.led_brightness
        options.pwm_lsb_nanoseconds = self.args.led_pwm_lsb_nanoseconds
        options.led_rgb_sequence = self.args.led_rgb_sequence
        options.pixel_mapper_config = self.args.led_pixel_mapper
        options.gpio_slowdown = self.args.led_slowdown_gpio
        options.hardware_mapping = self.args.led_gpio_mapping

        self.matrix = RGBMatrix(options=options)
        self.last_reset = datetime.now()

        # We'll initialize GPIO only when needed
        self.BUTTON_PIN = 17
        self.setup_gpio()

        # Load bitmap font data
        self.font_5x7 = {
            'A': [0x7E, 0x09, 0x09, 0x09, 0x7E],  # Example bitmap for 'A'
            # ... we'll need to define all characters
        }
        
        # Alternative: Load font from file
        self.font_path = "/usr/share/fonts/misc/tom-thumb.bdf"  # We'll need to install this

    def setup_gpio(self):
        # Temporarily disable GPIO setup
        self.gpio = None
        print("GPIO functionality temporarily disabled")
        return

        # Original code commented out for now
        """
        try:
            import RPi.GPIO as GPIO
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self.BUTTON_PIN, GPIO.FALLING, 
                                callback=self.button_callback, bouncetime=300)
            self.gpio = GPIO
        except Exception as e:
            print(f"GPIO setup failed: {e}")
            print("Button functionality will be disabled")
            self.gpio = None
        """

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

    def button_callback(self, channel):
        self.last_reset = datetime.now()
        threading.Thread(target=self.play_video).start()

    def play_video(self):
        os.system('cvlc --play-and-exit fail.mp4')

    def format_duration(self, duration):
        # Calculate all time components
        total_days = duration.days
        seconds = duration.seconds
        
        # Break down the components
        years = total_days // 365
        remaining_days = total_days % 365
        months = remaining_days // 30
        remaining_days = remaining_days % 30
        weeks = remaining_days // 7
        days = remaining_days % 7
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        # Build the time string with consistent 2-digit numbers and 1-char units
        components = []
        if years > 0:
            components.append(f"{years:02d}y")
        if months > 0 or years > 0:
            components.append(f"{months:02d}m")
        if weeks > 0 or months > 0 or years > 0:
            components.append(f"{weeks:02d}w")
        if days > 0 or weeks > 0 or months > 0 or years > 0:
            components.append(f"{days:02d}d")
        
        # Always show hours, minutes, seconds
        components.extend([
            f"{hours:02d}h",
            f"{minutes:02d}m",
            f"{seconds:02d}s"
        ])
        
        return " ".join(components)

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

    def run(self):
        try:
            # Use Teeny Tiny Pixls font
            font_path = "fonts/TeenyTinyPixls-o2zo.ttf"  # Adjust path as needed
            header_font = ImageFont.truetype(font_path, 8)  # Small size for header
            time_font = ImageFont.truetype(font_path, 16)   # Larger size for time
            
            while True:
                image = Image.new('RGB', (self.matrix.width, self.matrix.height), (0, 0, 0))
                draw = ImageDraw.Draw(image)

                # Draw header text
                header_text = "Days Since DNS:"
                text_bbox = draw.textbbox((0, 0), header_text, font=header_font)
                text_width = text_bbox[2] - text_bbox[0]
                x_position = (self.matrix.width - text_width) // 2
                draw.text((x_position, 2), header_text, font=header_font, fill=(255, 255, 255))

                # Calculate time
                duration = datetime.now() - self.last_reset
                time_text = self.format_duration(duration)
                
                # Draw time text with larger font
                text_bbox = draw.textbbox((0, 0), time_text, font=time_font)
                text_width = text_bbox[2] - text_bbox[0]
                x_position = (self.matrix.width - text_width) // 2
                draw.text((x_position, 16), time_text, font=time_font, fill=(255, 0, 0))

                self.matrix.SetImage(image)
                time.sleep(1)
                
        except KeyboardInterrupt:
            if self.gpio:
                self.gpio.cleanup()
            self.matrix.Clear()

if __name__ == "__main__":
    dns_counter = DNSCounter()
    try:
        dns_counter.run()
    except KeyboardInterrupt:
        print("Exiting...") 