#!/usr/bin/env python3
"""DNS Failure Counter Display for Raspberry Pi with RGB LED Matrix.

This module implements a visual counter that displays the time elapsed since the last
DNS failure on a 64x32 RGB LED matrix connected to a Raspberry Pi via an Adafruit HAT.

Hardware Requirements:
    - Raspberry Pi (any model with GPIO support)
    - Adafruit RGB Matrix HAT or compatible interface
    - 64x32 RGB LED matrix panel
    - Physical button connected to configurable GPIO pin (default: 19)

Key Features:
    - Real-time display of elapsed time in years, months, days, hours, minutes, seconds
    - Physical button reset functionality with audio feedback
    - Persistent state storage across reboots using JSON file
    - Thread-based button monitoring for non-blocking operation
    - Atomic file writes to prevent state corruption
    - Comprehensive logging to both console and syslog
    - YAML-based configuration file support

The counter can be reset by pressing the physical button, which also plays an audio
notification using the system's aplay utility.
"""
import argparse
import json
import logging
import os
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from logging.handlers import SysLogHandler
from typing import Any, Dict, Optional, Tuple

import gpiod
import yaml
from PIL import ImageDraw, ImageFont
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# Prometheus metrics - import from shared module
from metrics import (
    RESET_COUNTER, SECONDS_SINCE_RESET, UPTIME_SECONDS,
    AUDIO_PLAYBACK_ERRORS, APP_START_TIME, PROMETHEUS_AVAILABLE
)

# Set up logging with more detail
logger = logging.getLogger("dns_counter")
logger.setLevel(logging.DEBUG)  # Change to DEBUG level

# Add console handler with detailed formatting
console = logging.StreamHandler()
console.setFormatter(
    logging.Formatter(
        "%(asctime)s dns_counter: %(levelname)s [%(filename)s:%(lineno)d] %(message)s"
    )
)
logger.addHandler(console)

# Add syslog handler with detailed formatting
try:
    syslog = SysLogHandler(address="/dev/log", facility=SysLogHandler.LOG_DAEMON)
    syslog.setFormatter(
        logging.Formatter(
            "dns_counter[%(process)d]: %(levelname)s "
            "[%(filename)s:%(lineno)d] %(message)s"
        )
    )
    logger.addHandler(syslog)
except (OSError, IOError) as e:
    logger.warning(f"Could not initialize syslog handler: {e}")


def load_config(
    config_path: str = "/usr/local/share/dnsfail/config.yaml",
) -> Dict[str, Any]:
    """Load configuration from YAML file with fallback to defaults.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        dict: Configuration dictionary with all required keys
    """
    DEFAULT_CONFIG = {
        "gpio_pin": 19,
        "brightness": 80,
        "audio_file": "/usr/local/share/dnsfail/media/fail.wav",
        "web_port": 5000,
        "persistence_file": "/usr/local/share/dnsfail/last_reset.json",
        "log_level": "INFO",
    }

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            loaded_config = yaml.safe_load(f)

        # Merge loaded config into defaults (loaded values override)
        if loaded_config:
            config = DEFAULT_CONFIG.copy()
            config.update(loaded_config)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        else:
            logger.warning(f"Config file {config_path} is empty, using defaults")
            return DEFAULT_CONFIG

    except FileNotFoundError:
        logger.warning(f"Config file not found at {config_path}, using defaults")
        return DEFAULT_CONFIG
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML config at {config_path}: {e}, using defaults")
        return DEFAULT_CONFIG
    except Exception as e:
        logger.error(
            f"Unexpected error loading config from {config_path}: {e}, using defaults"
        )
        return DEFAULT_CONFIG


class DNSCounter(object):
    """DNS failure counter with RGB matrix display and GPIO button reset.

    This class manages a visual counter displayed on an RGB LED matrix that shows
    the elapsed time since the last DNS failure. It handles hardware initialization,
    state persistence, button input monitoring, and display rendering.

    Hardware Dependencies:
        - Adafruit RGB Matrix HAT connected to Raspberry Pi GPIO
        - 64x32 RGB LED matrix panel
        - Physical button on configurable GPIO pin (active low with pull-up)

    State Management:
        - Counter state persists across reboots via JSON file (configurable path)
        - Atomic writes using temporary files prevent corruption
        - Graceful fallback to current time if state cannot be loaded

    Threading:
        - Button monitoring runs in a daemon thread for non-blocking operation
        - Main thread handles display updates at 1Hz refresh rate

    Attributes:
        parser: Command-line argument parser for matrix configuration
        args: Parsed command-line arguments
        config: Configuration dictionary loaded from YAML file
        persistence_file: Path to JSON file for state persistence
        matrix: RGB matrix display object
        last_reset: Timestamp of the last counter reset
        BUTTON_PIN: GPIO pin number for reset button (from config)
        chip: GPIO chip handle for hardware access
        line: GPIO line handle for button input
        button_thread: Background thread monitoring button state
    """

    def __init__(self) -> None:
        """Initialize the DNS counter with hardware and restore state.

        Sets up the RGB matrix with optimized settings for the Adafruit HAT,
        loads configuration from YAML file, loads the last reset timestamp from
        persistent storage, and initializes GPIO for button input monitoring.

        Raises:
            Exception: If RGB matrix initialization fails (propagated from RGBMatrix)
        """
        self.parser: argparse.ArgumentParser = self.create_parser()
        self.args: argparse.Namespace = self.parser.parse_args()

        # Load configuration before initializing hardware
        self.config: Dict[str, Any] = load_config(self.args.config)

        # Set log level from config
        try:
            logger.setLevel(getattr(logging, self.config["log_level"]))
        except (AttributeError, TypeError):
            logger.warning(
                f"Invalid log_level '{self.config['log_level']}' in config, "
                "falling back to INFO"
            )
            logger.setLevel(logging.INFO)

        # Set instance variables from config
        self.persistence_file: str = self.config["persistence_file"]

        logger.info("Initializing RGB Matrix...")
        options = RGBMatrixOptions()
        options.rows = 32
        options.cols = 64
        options.chain_length = self.args.led_chain
        options.parallel = self.args.led_parallel
        options.row_address_type = self.args.led_row_addr
        options.multiplexing = self.args.led_multiplexing
        options.pwm_bits = 11  # Maximum PWM bits for smoother transitions
        options.brightness = self.config["brightness"]  # Use config value
        options.pwm_lsb_nanoseconds = 130  # Default timing
        options.led_rgb_sequence = self.args.led_rgb_sequence
        options.pixel_mapper_config = self.args.led_pixel_mapper
        options.gpio_slowdown = 3  # Increase slowdown to reduce flicker
        options.hardware_mapping = "adafruit-hat"
        options.scan_mode = 1  # Progressive scan mode
        options.disable_hardware_pulsing = False  # Enable hardware pulsing
        options.drop_privileges = True  # Allow privilege dropping

        try:
            self.matrix: RGBMatrix = RGBMatrix(options=options)
            logger.info("Matrix initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize matrix: {e}")
            raise

        # Initialize the last reset time from persistence or current time
        self.last_reset: datetime = self.load_state()
        logger.info(f"Counter initialized with start time: {self.last_reset}")

        # Initialize GPIO for button
        self.BUTTON_PIN: int = self.config["gpio_pin"]  # Use config value
        self.chip: Optional[gpiod.Chip] = None
        self.line: Any = None  # gpiod.Line (v1) or LineRequest (v2)
        self.button_thread: Optional[threading.Thread] = None
        self._gpiod_version: int = 1  # Will be set by setup_gpio
        self.setup_gpio()

    def save_state(self) -> None:
        """Save the last_reset timestamp to JSON file using atomic write.

        Uses a temporary file and atomic rename to ensure the persistence file
        is never left in a corrupt state, even if the program crashes during write.

        Note:
            Logs errors but does not raise exceptions to prevent crashes during
            normal operation.
        """
        try:
            data = {"last_reset": self.last_reset.isoformat(), "version": 1}
            # Use a temporary file for atomic write
            with tempfile.NamedTemporaryFile(
                mode="w",
                delete=False,
                dir=os.path.dirname(self.persistence_file),
                encoding="utf-8",
            ) as tf:
                json.dump(data, tf)
            os.rename(tf.name, self.persistence_file)
            logger.debug(f"Saved state to {self.persistence_file}: {data}")
        except Exception as e:
            logger.error(f"Failed to save state to {self.persistence_file}: {e}")

    def load_state(self) -> datetime:
        """Load the last_reset timestamp from JSON persistence file.

        Implements graceful degradation: if the file doesn't exist, is corrupt,
        or has any other issues, returns the current time instead of failing.

        Returns:
            datetime: The loaded datetime object, or datetime.now(timezone.utc) if loading fails

        Note:
            All errors during loading are logged but not raised, ensuring the
            application can always start even with a missing or corrupt state file.
        """
        if not os.path.exists(self.persistence_file):
            logger.warning(
                f"Persistence file not found at {self.persistence_file}. "
                "Initializing with current time."
            )
            return datetime.now(timezone.utc)

        try:
            with open(self.persistence_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            last_reset_str = data.get("last_reset")
            if last_reset_str:
                loaded_time = datetime.fromisoformat(last_reset_str)
                logger.info(
                    f"Loaded last_reset from {self.persistence_file}: {loaded_time}"
                )
                return loaded_time
            else:
                logger.warning(
                    f"'last_reset' key not found in {self.persistence_file}. "
                    "Initializing with current time."
                )
                return datetime.now(timezone.utc)
        except json.JSONDecodeError as e:
            logger.warning(
                f"Persistence file {self.persistence_file} is corrupt ({e}). "
                "Initializing with current time."
            )
            return datetime.now(timezone.utc)
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while loading state from "
                f"{self.persistence_file}: {e}. Initializing with current time."
            )
            return datetime.now(timezone.utc)

    def reset(self) -> datetime:
        """Reset the counter, save state, and play audio.

        This method is called by both the physical button and web interface
        to ensure synchronized state.

        Returns:
            datetime: The new last_reset timestamp
        """
        self.last_reset = datetime.now(timezone.utc)
        self.save_state()

        # Play audio
        sound_file = self.config["audio_file"]
        audio_device = self.config.get("audio_device", "")

        try:
            logger.debug("Playing reset sound...")
            # Use shell wrapper to ensure fresh ALSA context (fixes Docker startup race)
            play_script = "/app/play_audio.sh"
            if os.path.exists(play_script):
                aplay_cmd = ["bash", play_script, audio_device or "default", sound_file]
            else:
                # Fallback to direct aplay for non-Docker environments
                aplay_cmd = ["aplay"]
                if audio_device:
                    aplay_cmd.extend(["-D", audio_device])
                aplay_cmd.append(sound_file)
            logger.debug(f"Running: {' '.join(aplay_cmd)}")
            result = subprocess.run(
                aplay_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if result.returncode != 0:
                logger.error(f"Audio error: {result.stderr}")
            else:
                logger.debug("Sound playback completed successfully")
        except Exception as e:
            logger.error(f"Error playing sound: {e}", exc_info=True)

        return self.last_reset

    def get_last_reset(self) -> datetime:
        """Get the current last_reset timestamp.

        Returns:
            datetime: The current last_reset value
        """
        return self.last_reset

    def create_parser(self) -> argparse.ArgumentParser:
        """Create and configure argument parser for LED matrix options.

        Returns:
            argparse.ArgumentParser: Configured parser with all matrix-related arguments

        Note:
            Most arguments map directly to RGBMatrixOptions parameters and should
            match the hardware configuration of your specific LED matrix panel.
        """
        parser = argparse.ArgumentParser()

        # Matrix arguments
        parser.add_argument(
            "--led-rows",
            action="store",
            help="Display rows. 16 for 16x32, 32 for 32x32. Default: 32",
            type=int,
            default=32,
        )
        parser.add_argument(
            "--led-cols",
            action="store",
            help="Panel columns. Typically 32 or 64. Default: 64",
            type=int,
            default=64,
        )
        parser.add_argument(
            "--led-chain",
            action="store",
            help="Daisy-chained boards. Default: 1",
            type=int,
            default=1,
        )
        parser.add_argument(
            "--led-parallel",
            action="store",
            help="For Plus-models or RPi2: parallel chains. 1..3. Default: 1",
            type=int,
            default=1,
        )
        parser.add_argument(
            "--led-pwm-bits",
            action="store",
            help="Bits used for PWM. Range 1..11. Default: 11",
            type=int,
            default=11,
        )
        parser.add_argument(
            "--led-brightness",
            action="store",
            help="Sets brightness level. Range: 1..100. Default: 100",
            type=int,
            default=100,
        )
        parser.add_argument(
            "--led-gpio-mapping",
            help="Hardware Mapping: regular, adafruit-hat, adafruit-hat-pwm",
            choices=["regular", "adafruit-hat", "adafruit-hat-pwm"],
            type=str,
            default="adafruit-hat",
        )
        parser.add_argument(
            "--led-scan-mode",
            action="store",
            help="Progressive or interlaced scan. 0 = Progressive, 1 = Interlaced. "
            "Default: 1",
            type=int,
            default=1,
        )
        parser.add_argument(
            "--led-pwm-lsb-nanoseconds",
            action="store",
            help="Base time-unit for the on-time in the lowest significant bit in "
            "nanoseconds. Default: 130",
            type=int,
            default=130,
        )
        parser.add_argument(
            "--led-row-addr",
            action="store",
            help="Addressing of rows. Default: 0",
            type=int,
            default=0,
        )
        parser.add_argument(
            "--led-multiplexing",
            action="store",
            help="Multiplexing type: 0 = direct; 1 = strip; 2 = checker; 3 = spiral; "
            "4 = Z-strip; 5 = ZnMirrorZStripe. Default: 0",
            type=int,
            default=0,
        )
        parser.add_argument(
            "--led-pixel-mapper",
            action="store",
            help='Apply pixel mappers. Default: ""',
            type=str,
            default="",
        )
        parser.add_argument(
            "--led-rgb-sequence",
            action="store",
            help="Switch if your matrix has led colors swapped. Default: RGB",
            type=str,
            default="RGB",
        )
        parser.add_argument(
            "--led-slowdown-gpio",
            action="store",
            help="Slowdown GPIO. Higher value, slower but less flicker. Range: 0..4",
            type=int,
            default=4,
        )
        parser.add_argument(
            "--config",
            action="store",
            help="Path to configuration file",
            type=str,
            default="/usr/local/share/dnsfail/config.yaml",
        )

        return parser

    def format_duration(self, duration: timedelta) -> Tuple[str, str]:
        """Format duration into two display lines showing all time units.

        Args:
            duration: Time duration to format

        Returns:
            Tuple[str, str]: Two formatted strings:
                - Line 1: "YYy MMmo DDd" format (years, months, days)
                - Line 2: "HHh MMm SSs" format (hours, minutes, seconds)

        Note:
            Months are approximated as 30-day periods. For precise date arithmetic,
            consider using dateutil or similar library.
        """
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

    def get_max_font_size(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        max_width: int,
        max_height: int,
        start_size: int = 20,
    ) -> ImageFont.FreeTypeFont:
        """Determine the largest font size that fits text in given space.

        Args:
            draw: PIL ImageDraw object for measuring text
            text: Text string to size
            max_width: Maximum width in pixels
            max_height: Maximum height in pixels
            start_size: Initial font size to try (default: 20)

        Returns:
            ImageFont.FreeTypeFont: Font object at largest size that fits

        Note:
            Uses binary search approach, decreasing from start_size until text fits.
            Minimum font size is 6 pixels for readability.
        """
        font_size = start_size
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size
        )

        while font_size > 6:  # Minimum readable size
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size
            )
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            if text_width <= max_width and text_height <= max_height:
                return font

            font_size -= 1

        return font

    def draw_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        x: int,
        y: int,
        color: Tuple[int, int, int],
        size_multiplier: int = 1,
    ) -> None:
        """Draw text using custom bitmap font.

        Args:
            draw: PIL ImageDraw object to draw on
            text: Text string to render
            x: Starting x coordinate
            y: Starting y coordinate
            color: RGB color tuple (R, G, B)
            size_multiplier: Scale factor for font size (default: 1)

        Note:
            Uses self.font_5x7 bitmap font definition. Each character is 5x7 pixels
            with 1 pixel spacing. Characters not in font are skipped.
        """
        current_x = x
        for char in text:
            if char in self.font_5x7:
                bitmap = self.font_5x7[char]
                for row in range(7):
                    for col in range(5):
                        if bitmap[col] & (1 << (6 - row)):
                            pixel_x = current_x + (col * size_multiplier)
                            pixel_y = y + (row * size_multiplier)
                            if size_multiplier == 1:
                                draw.point((pixel_x, pixel_y), color)
                            else:
                                draw.rectangle(
                                    [
                                        pixel_x,
                                        pixel_y,
                                        pixel_x + size_multiplier - 1,
                                        pixel_y + size_multiplier - 1,
                                    ],
                                    fill=color,
                                )
            current_x += 6 * size_multiplier  # 5 pixels + 1 space between characters

    def test_display(self) -> None:
        """Test RGB matrix with red, green, blue color sequence.

        Displays full-screen red, green, and blue for 2 seconds each to verify
        matrix functionality and color channels. Useful for hardware diagnostics.

        Note:
            Blocks for 6 seconds total. Not called during normal operation.
        """
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

    def run(self) -> None:
        """Main display loop that renders the counter continuously.

        Displays a two-section layout:
            - Top: "DAYS SINCE" / "DNS" header in white
            - Bottom: Elapsed time in two lines (YYy MMmo DDd / HHh MMm SSs) in red

        Updates display every second. Runs until interrupted with Ctrl+C.

        Raises:
            KeyboardInterrupt: Caught and handled gracefully with cleanup
            Exception: Logged with full traceback, then re-raised after cleanup

        Note:
            Performs proper cleanup on exit: releases GPIO resources and clears display.
        """
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
                graphics.DrawText(
                    canvas,
                    header_font,
                    (64 - len(header_text1) * 6) // 2,
                    8,
                    white,
                    header_text1,
                )

                graphics.DrawText(
                    canvas,
                    header_font,
                    (64 - len(header_text2) * 6) // 2,
                    16,
                    white,
                    header_text2,
                )

                # Calculate and draw time in two lines
                duration = datetime.now(timezone.utc) - self.last_reset
                time_line1, time_line2 = self.format_duration(duration)

                # Draw first line of time (MM:WW:DD)
                graphics.DrawText(
                    canvas,
                    time_font,
                    (64 - len(time_line1) * 5) // 2,
                    24,
                    red,
                    time_line1,
                )

                # Draw second line of time (HH:MM:SS)
                graphics.DrawText(
                    canvas,
                    time_font,
                    (64 - len(time_line2) * 5) // 2,
                    31,
                    red,
                    time_line2,
                )

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

    def setup_gpio(self) -> None:
        """Initialize GPIO for button input using gpiod library.

        Configures GPIO line from config as input with pull-up resistor, then
        spawns a daemon thread to monitor button state.

        Note:
            Logs errors but does not raise exceptions. Sets chip and line to None
            on failure, allowing the display to continue working without button input.
            Thread is daemon so it won't prevent program exit.
            Supports both gpiod v1 and v2 APIs.
        """
        try:
            # Detect gpiod API version and use appropriate method
            if hasattr(gpiod, "request_lines"):
                # gpiod v2 API
                self._gpiod_version = 2
                logger.info("Using gpiod v2 API")
                self.line = gpiod.request_lines(
                    "/dev/gpiochip0",
                    consumer="dns_counter",
                    config={
                        self.BUTTON_PIN: gpiod.LineSettings(
                            direction=gpiod.line.Direction.INPUT,
                            bias=gpiod.line.Bias.PULL_UP,
                        )
                    },
                )
                self.chip = None  # Not needed in v2
            else:
                # gpiod v1 API
                self._gpiod_version = 1
                logger.info("Using gpiod v1 API")
                self.chip = gpiod.Chip("/dev/gpiochip0")
                self.line = self.chip.get_line(self.BUTTON_PIN)
                self.line.request(
                    consumer="dns_counter",
                    type=gpiod.LINE_REQ_DIR_IN,
                    flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP,
                )

            logger.info("GPIO setup successful with pull-up enabled")

            # Start a thread to check the button state
            self.button_thread = threading.Thread(
                target=self._check_button, daemon=True
            )
            self.button_thread.start()

        except Exception as e:
            logger.error(f"Unexpected GPIO error: {e}")
            logger.error("Try running: sudo chmod 660 /dev/gpiochip0")
            self.chip = None
            self.line = None

    def _get_button_value(self) -> int:
        """Read button value, handling both gpiod v1 and v2 APIs.

        Returns:
            0 if button is pressed (active low), 1 if released.
        """
        if self._gpiod_version == 2:
            # v2 API: get_value takes pin number, returns Value enum
            val = self.line.get_value(self.BUTTON_PIN)
            # Value.INACTIVE = 0 (button pressed with pull-up)
            # Value.ACTIVE = 1 (button released)
            return 0 if val == gpiod.line.Value.INACTIVE else 1
        else:
            # v1 API: get_value returns int directly
            return self.line.get_value()

    def _check_button(self) -> None:
        """Thread function to continuously monitor button state.

        Polls button every 100ms and detects press events (transition to 0).
        When pressed, resets counter, saves state, and plays audio notification.

        Note:
            Runs in daemon thread - will not prevent program exit. Uses 300ms
            debounce to prevent multiple triggers. Accesses shared self.last_reset
            state - thread-safe due to Python GIL and atomic datetime assignment.
            Sets HOME and XDG_RUNTIME_DIR environment variables to /tmp to avoid
            PulseAudio permission errors when running as different user.
        """
        last_press = 0
        last_value = None
        logger.info("Button monitoring started")
        logger.info(f"Initial button state: {self._get_button_value()}")

        # Get absolute path to sound file from config
        sound_file = self.config["audio_file"]
        audio_device = self.config.get("audio_device", "")  # Optional device
        logger.debug(f"Sound file path: {sound_file}")
        logger.debug(f"Sound file exists: {os.path.exists(sound_file)}")
        logger.debug(f"Audio device: {audio_device or 'default'}")

        # Wait for audio devices to be fully available (container startup issue)
        for attempt in range(10):
            test_result = subprocess.run(
                ["aplay", "-l"], capture_output=True, text=True
            )
            if "Headphones" in test_result.stdout:
                logger.info(f"Audio devices ready after {attempt + 1} attempts")
                break
            logger.warning(f"Waiting for audio devices (attempt {attempt + 1}/10)...")
            time.sleep(1)
        else:
            logger.error(f"Audio devices not fully available: {test_result.stdout[:200]}")

        while True:
            try:
                if self.line:
                    value = self._get_button_value()
                    if value != last_value:
                        logger.debug(f"Button state changed to: {value}")
                        last_value = value

                        if value == 0:  # Button pressed (active low)
                            current_time = time.time()
                            if current_time - last_press > 0.3:  # Simple debounce
                                logger.info("Button press detected - Resetting counter")
                                # Increment Prometheus counter for button resets
                                if PROMETHEUS_AVAILABLE:
                                    RESET_COUNTER.labels(source='button').inc()
                                self.last_reset = datetime.now(timezone.utc)
                                self.save_state()  # Save the new reset time
                                try:
                                    logger.debug("Attempting to play sound...")
                                    # Use shell wrapper for fresh ALSA context
                                    play_script = "/app/play_audio.sh"
                                    if os.path.exists(play_script):
                                        aplay_cmd = [
                                            "bash",
                                            play_script,
                                            audio_device or "default",
                                            sound_file,
                                        ]
                                    else:
                                        aplay_cmd = ["aplay"]
                                        if audio_device:
                                            aplay_cmd.extend(["-D", audio_device])
                                        aplay_cmd.append(sound_file)
                                    logger.debug(f"Running: {' '.join(aplay_cmd)}")
                                    result = subprocess.run(
                                        aplay_cmd,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                    )
                                    if result.returncode != 0:
                                        logger.error(f"Audio error: {result.stderr}")
                                        if PROMETHEUS_AVAILABLE:
                                            AUDIO_PLAYBACK_ERRORS.inc()
                                    else:
                                        logger.debug(
                                            "Sound playback completed successfully"
                                        )
                                except Exception as e:
                                    logger.error(
                                        f"Error playing sound: {e}", exc_info=True
                                    )
                                    if PROMETHEUS_AVAILABLE:
                                        AUDIO_PLAYBACK_ERRORS.inc()
                                last_press = current_time
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in button loop: {e}", exc_info=True)
                time.sleep(0.1)


def start_web_server(dns_counter_instance: "DNSCounter") -> None:
    """Start web server in a background thread.

    Args:
        dns_counter_instance: DNSCounter instance for shared state access
    """
    try:
        from web_server import WebServer

        # Create web server with same config and callbacks for state sync
        server = WebServer(
            config=dns_counter_instance.config,
            reset_callback=dns_counter_instance.reset,
            get_state_callback=dns_counter_instance.get_last_reset,
        )

        # Run in background thread
        web_thread = threading.Thread(
            target=lambda: server.app.run(
                host="0.0.0.0",
                port=dns_counter_instance.config["web_port"],
                debug=False,
                threaded=True,
                use_reloader=False,
            ),
            daemon=True,
        )
        web_thread.start()
        logger.info(f"Web server started on port {dns_counter_instance.config['web_port']}")
    except ImportError:
        logger.warning("Flask not available, web server disabled")
    except Exception as e:
        logger.error(f"Failed to start web server: {e}")


if __name__ == "__main__":
    try:
        dns_counter = DNSCounter()

        # Start web server if enabled
        if dns_counter.config.get("web_port"):
            start_web_server(dns_counter)

        dns_counter.run()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        raise
