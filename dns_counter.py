#!/usr/bin/env python3
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from PIL import Image, ImageDraw, ImageFont
import time
import datetime
import RPi.GPIO as GPIO
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
        options.gpio_slowdown = 4
        options.hardware_mapping = 'adafruit-hat'

        self.matrix = RGBMatrix(options=options)
        self.last_reset = datetime.now()

        # GPIO Setup
        self.BUTTON_PIN = 17
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.BUTTON_PIN, GPIO.FALLING, 
                            callback=self.button_callback, bouncetime=300)

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

        return parser

    def button_callback(self, channel):
        self.last_reset = datetime.now()
        threading.Thread(target=self.play_video).start()

    def play_video(self):
        os.system('cvlc --play-and-exit fail.mp4')

    def format_duration(self, duration):
        days = duration.days
        return f"{days}"

    def run(self):
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
        
        while True:
            image = Image.new('RGB', (self.matrix.width, self.matrix.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)

            draw.text((2, 2), "Days Since", font=font, fill=(255, 255, 255))
            draw.text((2, 15), "DNS:", font=font, fill=(255, 255, 255))

            duration = datetime.now() - self.last_reset
            days_text = self.format_duration(duration)
            
            text_bbox = draw.textbbox((0, 0), days_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            x_position = (self.matrix.width - text_width) // 2
            
            draw.text((x_position, 15), days_text, font=font, fill=(255, 0, 0))
            self.matrix.SetImage(image)
            time.sleep(60)

if __name__ == "__main__":
    dns_counter = DNSCounter()
    try:
        dns_counter.run()
    except KeyboardInterrupt:
        GPIO.cleanup() 