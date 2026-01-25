#!/usr/bin/env python3
"""Mock implementation of rgbmatrix library for Docker development."""
import logging

logger = logging.getLogger("dns_counter")


class RGBMatrixOptions:
    """Mock RGBMatrixOptions accepting all configuration parameters."""

    def __init__(self):
        self.rows = 32
        self.cols = 64
        self.chain_length = 1
        self.parallel = 1
        self.row_address_type = 0
        self.multiplexing = 0
        self.pwm_bits = 11
        self.brightness = 100
        self.pwm_lsb_nanoseconds = 130
        self.led_rgb_sequence = "RGB"
        self.pixel_mapper_config = ""
        self.gpio_slowdown = 4
        self.hardware_mapping = "adafruit-hat"
        self.scan_mode = 1
        self.disable_hardware_pulsing = False
        self.drop_privileges = True
        logger.debug("Mock RGBMatrixOptions initialized")


class MockCanvas:
    """Mock canvas object for RGBMatrix."""

    def __init__(self, width=64, height=32):
        self.width = width
        self.height = height
        logger.debug(f"Mock canvas created: {width}x{height}")

    def SetPixel(self, x, y, r, g, b):
        """Mock SetPixel - no-op with debug logging."""
        logger.debug(f"SetPixel({x}, {y}, {r}, {g}, {b})")

    def Clear(self):
        """Mock Clear - no-op with debug logging."""
        logger.debug("Canvas cleared")

    def Fill(self, r, g, b):
        """Mock Fill - no-op with debug logging."""
        logger.debug(f"Canvas filled with RGB({r}, {g}, {b})")


class RGBMatrix:
    """Mock RGBMatrix class."""

    def __init__(self, options=None):
        self.options = options or RGBMatrixOptions()
        self.canvas = MockCanvas(self.options.cols, self.options.rows)
        logger.info(
            f"Mock RGBMatrix initialized: {self.options.cols}x{self.options.rows}"
        )

    def CreateFrameCanvas(self):
        """Return mock canvas."""
        logger.debug("CreateFrameCanvas called")
        return self.canvas

    def SwapOnVSync(self, canvas):
        """Mock SwapOnVSync - no-op returning canvas."""
        logger.debug("SwapOnVSync called")
        return canvas

    def Clear(self):
        """Mock Clear - no-op."""
        logger.debug("Matrix cleared")
        self.canvas.Clear()


class Color:
    """Mock Color class."""

    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b
        logger.debug(f"Color created: RGB({r}, {g}, {b})")


class Font:
    """Mock Font class."""

    def __init__(self):
        self.path = None
        logger.debug("Font object created")

    def LoadFont(self, path):
        """Mock LoadFont - stores path."""
        self.path = path
        logger.debug(f"Font loaded from: {path}")
        return True


def DrawText(canvas, font, x, y, color, text):
    """Mock DrawText function - no-op with debug logging."""
    logger.debug(f"DrawText: '{text}' at ({x}, {y})")


# Mock graphics module
class _GraphicsModule:
    """Mock graphics module."""

    Color = Color
    Font = Font
    DrawText = staticmethod(DrawText)


graphics = _GraphicsModule()
