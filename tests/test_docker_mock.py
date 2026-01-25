#!/usr/bin/env python3
"""Tests for Docker mock environment."""
import os
import sys
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set mock mode before imports
os.environ['MOCK_MODE'] = '1'
sys.argv.append('--mock')


def test_mock_rgbmatrix_import():
    """Test that mock_rgbmatrix can be imported."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mocks'))
    import mock_rgbmatrix
    assert hasattr(mock_rgbmatrix, 'RGBMatrix')
    assert hasattr(mock_rgbmatrix, 'RGBMatrixOptions')
    assert hasattr(mock_rgbmatrix, 'graphics')


def test_mock_gpiod_import():
    """Test that mock_gpiod can be imported."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mocks'))
    import mock_gpiod
    assert hasattr(mock_gpiod, 'Chip')
    assert hasattr(mock_gpiod, 'LINE_REQ_DIR_IN')
    assert hasattr(mock_gpiod, 'LINE_REQ_FLAG_BIAS_PULL_UP')


def test_dns_counter_initializes():
    """Test that DNSCounter initializes in mock mode."""
    import sys
    # Import after setting mock mode
    from dns_counter import DNSCounter

    # Mock sys.argv to provide --mock flag
    old_argv = sys.argv
    try:
        sys.argv = ['test', '--mock']
        # This should not raise an exception
        counter = DNSCounter()
        assert counter is not None
        assert counter.matrix is not None
    finally:
        sys.argv = old_argv


def test_font_directory_resolution():
    """Test that font directory resolves correctly in mock mode."""
    from dns_counter import FONT_DIR
    assert FONT_DIR == './fonts'


def test_persistence_file_path():
    """Test that persistence file path is correct in mock mode."""
    from dns_counter import PERSISTENCE_FILE
    assert PERSISTENCE_FILE == '/tmp/last_reset.json'


def test_sound_file_path():
    """Test that sound file path is correct in mock mode."""
    from dns_counter import SOUND_FILE
    assert SOUND_FILE == './fail.mp3'


def test_mock_button_press_simulation():
    """Test that mock button press can be simulated via environment variable."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mocks'))
    import mock_gpiod

    # Test default state (not pressed)
    chip = mock_gpiod.Chip('/dev/gpiochip0')
    line = chip.get_line(19)
    line.request(consumer='test')
    assert line.get_value() == 1

    # Test simulated button press
    os.environ['MOCK_BUTTON_PRESS'] = '1'
    assert line.get_value() == 0

    # Clean up
    os.environ.pop('MOCK_BUTTON_PRESS', None)


def test_mock_canvas_operations():
    """Test that mock canvas operations don't raise exceptions."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mocks'))
    import mock_rgbmatrix

    options = mock_rgbmatrix.RGBMatrixOptions()
    matrix = mock_rgbmatrix.RGBMatrix(options=options)
    canvas = matrix.CreateFrameCanvas()

    # These should not raise exceptions
    canvas.SetPixel(0, 0, 255, 0, 0)
    canvas.Clear()
    matrix.SwapOnVSync(canvas)
    matrix.Clear()


def test_mock_graphics_functions():
    """Test that mock graphics functions work correctly."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mocks'))
    import mock_rgbmatrix

    color = mock_rgbmatrix.Color(255, 255, 255)
    assert color.r == 255
    assert color.g == 255
    assert color.b == 255

    font = mock_rgbmatrix.Font()
    result = font.LoadFont('./fonts/6x10.bdf')
    assert result is True

    # DrawText should not raise
    canvas = mock_rgbmatrix.MockCanvas()
    mock_rgbmatrix.DrawText(canvas, font, 10, 10, color, "Test")
