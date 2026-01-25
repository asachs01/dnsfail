#!/usr/bin/env python3
"""Mock implementation of gpiod library for Docker development."""
import logging
import os

logger = logging.getLogger("dns_counter")

# Module-level constants
LINE_REQ_DIR_IN = 1
LINE_REQ_FLAG_BIAS_PULL_UP = 2


class Line:
    """Mock GPIO Line class."""

    def __init__(self, pin):
        self.pin = pin
        self.consumer = None
        logger.debug(f"Mock Line created for pin {pin}")

    def request(self, consumer=None, type=None, flags=None):
        """Mock request - stores configuration."""
        self.consumer = consumer
        logger.debug(
            f"Line {self.pin} requested: consumer={consumer}, "
            f"type={type}, flags={flags}"
        )

    def get_value(self):
        """Mock get_value - returns 0 if MOCK_BUTTON_PRESS=1, else 1."""
        if os.environ.get("MOCK_BUTTON_PRESS") == "1":
            logger.debug(f"Line {self.pin} get_value: 0 (simulated button press)")
            return 0
        logger.debug(f"Line {self.pin} get_value: 1 (not pressed)")
        return 1

    def release(self):
        """Mock release - no-op."""
        logger.debug(f"Line {self.pin} released")


class Chip:
    """Mock GPIO Chip class."""

    def __init__(self, device_path="/dev/gpiochip0"):
        self.device_path = device_path
        self.lines = {}
        logger.info(f"Mock Chip opened: {device_path}")

    def get_line(self, pin):
        """Return mock Line for given pin."""
        if pin not in self.lines:
            self.lines[pin] = Line(pin)
        logger.debug(f"get_line({pin})")
        return self.lines[pin]

    def close(self):
        """Mock close - no-op."""
        logger.debug(f"Chip {self.device_path} closed")
