#!/usr/bin/env python3
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw, ImageFont
import time
import datetime
import RPi.GPIO as GPIO
import os
import threading
from datetime import datetime, timedelta

# GPIO Setup
BUTTON_PIN = 17  # Adjust this to your actual GPIO pin
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Matrix configuration
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.hardware_mapping = 'adafruit-hat'  # or 'regular' depending on your setup
options.gpio_slowdown = 4  # Adjust if needed

matrix = RGBMatrix(options=options)

# Initialize variables
last_reset = datetime.now()
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
font = ImageFont.truetype(font_path, 12)  # Increased from 8 to 12

def play_video():
    os.system('cvlc --play-and-exit fail.mp4')  # Using VLC to play video

def format_duration(duration):
    # Simplify to just show days
    days = duration.days
    return f"{days}"

def button_callback(channel):
    global last_reset
    last_reset = datetime.now()
    threading.Thread(target=play_video).start()

def update_display():
    while True:
        # Create a new image with a black background
        image = Image.new('RGB', (64, 32), (0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw "Days Since DNS" text
        draw.text((2, 2), "Days Since", font=font, fill=(255, 255, 255))
        draw.text((2, 15), "DNS:", font=font, fill=(255, 255, 255))

        # Calculate and draw the number of days
        duration = datetime.now() - last_reset
        days_text = format_duration(duration)
        
        # Center the number
        text_bbox = draw.textbbox((0, 0), days_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        x_position = (64 - text_width) // 2
        
        draw.text((x_position, 15), days_text, font=font, fill=(255, 0, 0))

        # Update the matrix
        matrix.SetImage(image)
        time.sleep(60)  # Update every minute

def main():
    # Set up button interrupt
    GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, 
                         callback=button_callback, bouncetime=300)

    try:
        update_display()
    except KeyboardInterrupt:
        GPIO.cleanup()
        matrix.Clear()

if __name__ == "__main__":
    main() 