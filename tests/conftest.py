"""Pytest fixtures for dns_counter tests."""
import os
import sys
import pytest
from unittest.mock import MagicMock

# Mock hardware dependencies before any imports
sys.modules['gpiod'] = MagicMock()
sys.modules['rgbmatrix'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageDraw'] = MagicMock()
sys.modules['PIL.ImageFont'] = MagicMock()


@pytest.fixture
def temp_persistence_file(tmp_path, monkeypatch):
    """Provide a temporary persistence file path and patch the module constant.

    Args:
        tmp_path: pytest's built-in temporary directory fixture
        monkeypatch: pytest's built-in monkeypatch fixture

    Yields:
        Path: Temporary file path for persistence testing
    """
    # Create temp file path
    temp_file = tmp_path / "last_reset.json"

    # Ensure directory exists (tmp_path should exist, but be explicit)
    temp_file.parent.mkdir(parents=True, exist_ok=True)

    # Patch the PERSISTENCE_FILE constant in dns_counter module
    import dns_counter
    monkeypatch.setattr(dns_counter, 'PERSISTENCE_FILE', str(temp_file))

    yield temp_file

    # Cleanup is automatic via tmp_path


@pytest.fixture
def mock_datetime(monkeypatch):
    """Provide a frozen datetime for reproducible tests.

    Uses freezegun to freeze datetime.now() at a known value.

    Args:
        monkeypatch: pytest's built-in monkeypatch fixture

    Yields:
        datetime: Frozen datetime object
    """
    from freezegun import freeze_time
    from datetime import datetime

    # Freeze at a specific moment: 2026-01-25 12:00:00
    frozen_time = "2026-01-25 12:00:00"

    with freeze_time(frozen_time):
        yield datetime.now()


@pytest.fixture
def dns_counter_mock(temp_persistence_file, monkeypatch):
    """Provide a DNSCounter instance with mocked hardware dependencies.

    This fixture creates a DNSCounter instance suitable for testing timer logic
    without requiring actual GPIO or LED matrix hardware.

    Args:
        temp_persistence_file: Fixture providing temporary persistence file
        monkeypatch: pytest's built-in monkeypatch fixture

    Yields:
        DNSCounter: Mock DNSCounter instance
    """
    import dns_counter
    from datetime import datetime

    # Mock the argparse to avoid command-line argument issues
    class MockArgs:
        led_chain = 1
        led_parallel = 1
        led_row_addr = 0
        led_multiplexing = 0
        led_rgb_sequence = "RGB"
        led_pixel_mapper = ""

    # Create a minimal mock DNSCounter that bypasses hardware initialization
    class TestDNSCounter:
        def __init__(self):
            self.last_reset = datetime.now()

        def save_state(self):
            """Use the real save_state implementation."""
            return dns_counter.DNSCounter.save_state(self)

        def load_state(self):
            """Use the real load_state implementation."""
            return dns_counter.DNSCounter.load_state(self)

        def format_duration(self, duration):
            """Use the real format_duration implementation."""
            return dns_counter.DNSCounter.format_duration(self, duration)

    yield TestDNSCounter()
