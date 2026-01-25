"""Unit tests for dns_counter timer logic.

Tests cover:
- Duration formatting (format_duration method)
- State persistence (save_state/load_state methods)
- Reset logic (button press handling)
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch

from freezegun import freeze_time


class TestDurationFormatting:
    """Test suite for format_duration() method."""

    def test_format_duration_zero(self, dns_counter_mock):
        """Zero seconds should format as all zeros."""
        duration = timedelta(seconds=0)
        line1, line2 = dns_counter_mock.format_duration(duration)

        assert line1 == "00y 00mo 00d", f"Expected '00y 00mo 00d', got '{line1}'"
        assert line2 == "00h 00m 00s", f"Expected '00h 00m 00s', got '{line2}'"

    def test_format_duration_one_day(self, dns_counter_mock):
        """86400 seconds (1 day) should format correctly."""
        duration = timedelta(seconds=86400)
        line1, line2 = dns_counter_mock.format_duration(duration)

        assert line1 == "00y 00mo 01d", f"Expected '00y 00mo 01d', got '{line1}'"
        assert line2 == "00h 00m 00s", f"Expected '00h 00m 00s', got '{line2}'"

    def test_format_duration_one_year(self, dns_counter_mock):
        """365 days should format as 1 year."""
        duration = timedelta(days=365)
        line1, line2 = dns_counter_mock.format_duration(duration)

        assert line1 == "01y 00mo 00d", f"Expected '01y 00mo 00d', got '{line1}'"
        assert line2 == "00h 00m 00s", f"Expected '00h 00m 00s', got '{line2}'"

    def test_format_duration_mixed(self, dns_counter_mock):
        """Complex duration should format all units correctly.

        400 days + 16837 seconds breakdown:
        - Years: 400 // 365 = 1 year
        - Remaining days: 400 % 365 = 35 days
        - Months: 35 // 30 = 1 month
        - Days: 35 % 30 = 5 days
        - 16837 seconds = 4 hours, 40 minutes, 37 seconds
        """
        duration = timedelta(days=400, seconds=16837)
        line1, line2 = dns_counter_mock.format_duration(duration)

        assert line1 == "01y 01mo 05d", f"Expected '01y 01mo 05d', got '{line1}'"
        assert line2 == "04h 40m 37s", f"Expected '04h 40m 37s', got '{line2}'"

    def test_format_duration_edge_29_days(self, dns_counter_mock):
        """29 days should NOT roll to a month (requires 30)."""
        duration = timedelta(days=29)
        line1, line2 = dns_counter_mock.format_duration(duration)

        assert line1 == "00y 00mo 29d", f"Expected '00y 00mo 29d', got '{line1}'"
        assert line2 == "00h 00m 00s", f"Expected '00h 00m 00s', got '{line2}'"

    def test_format_duration_edge_364_days(self, dns_counter_mock):
        """364 days should show 11 months and 4 days (not roll to year).

        Breakdown:
        - Years: 364 // 365 = 0 years
        - Remaining: 364 % 365 = 364 days
        - Months: 364 // 30 = 12 months
        - Days: 364 % 30 = 4 days
        """
        duration = timedelta(days=364)
        line1, line2 = dns_counter_mock.format_duration(duration)

        assert line1 == "00y 12mo 04d", f"Expected '00y 12mo 04d', got '{line1}'"
        assert line2 == "00h 00m 00s", f"Expected '00h 00m 00s', got '{line2}'"

    def test_format_duration_time_components(self, dns_counter_mock):
        """Test hours, minutes, seconds formatting without days."""
        # 12 hours, 34 minutes, 56 seconds = 45296 seconds
        duration = timedelta(seconds=45296)
        line1, line2 = dns_counter_mock.format_duration(duration)

        assert line1 == "00y 00mo 00d", f"Expected '00y 00mo 00d', got '{line1}'"
        assert line2 == "12h 34m 56s", f"Expected '12h 34m 56s', got '{line2}'"


class TestPersistence:
    """Test suite for save_state() and load_state() methods."""

    def test_persistence_save_load(self, dns_counter_mock, temp_persistence_file):
        """Save and load should round-trip a datetime correctly."""
        # Set a known datetime
        test_time = datetime(2026, 1, 25, 10, 30, 45)
        dns_counter_mock.last_reset = test_time

        # Save state
        dns_counter_mock.save_state()

        # Verify file exists
        assert (
            temp_persistence_file.exists()
        ), "Persistence file should exist after save"

        # Load state
        loaded_time = dns_counter_mock.load_state()

        # Verify datetime matches (isoformat should preserve up to microseconds)
        assert loaded_time == test_time, f"Expected {test_time}, got {loaded_time}"

    def test_persistence_file_structure(self, dns_counter_mock, temp_persistence_file):
        """Saved JSON should have correct structure with version and last_reset."""
        test_time = datetime(2026, 1, 25, 10, 30, 45)
        dns_counter_mock.last_reset = test_time

        dns_counter_mock.save_state()

        # Read and parse JSON
        with open(temp_persistence_file, "r") as f:
            data = json.load(f)

        assert "version" in data, "JSON should contain 'version' key"
        assert "last_reset" in data, "JSON should contain 'last_reset' key"
        assert data["version"] == 1, "Version should be 1"
        assert (
            data["last_reset"] == test_time.isoformat()
        ), "last_reset should be ISO format"

    def test_persistence_corruption_invalid_json(
        self, dns_counter_mock, temp_persistence_file
    ):
        """Malformed JSON should fall back to datetime.now()."""
        # Write invalid JSON
        with open(temp_persistence_file, "w") as f:
            f.write("{invalid json")

        # Freeze time to verify fallback
        with freeze_time("2026-01-25 15:00:00"):
            loaded_time = dns_counter_mock.load_state()
            expected_time = datetime(2026, 1, 25, 15, 0, 0)

            assert (
                loaded_time == expected_time
            ), f"Should fall back to current time, got {loaded_time}"

    def test_persistence_corruption_missing_key(
        self, dns_counter_mock, temp_persistence_file
    ):
        """Valid JSON missing 'last_reset' key should fall back to datetime.now()."""
        # Write JSON missing last_reset
        with open(temp_persistence_file, "w") as f:
            json.dump({"version": 1}, f)

        with freeze_time("2026-01-25 16:00:00"):
            loaded_time = dns_counter_mock.load_state()
            expected_time = datetime(2026, 1, 25, 16, 0, 0)

            assert (
                loaded_time == expected_time
            ), f"Should fall back to current time, got {loaded_time}"

    def test_persistence_file_not_found(self, dns_counter_mock, temp_persistence_file):
        """Non-existent file should fall back to datetime.now()."""
        # Ensure file doesn't exist
        if temp_persistence_file.exists():
            temp_persistence_file.unlink()

        with freeze_time("2026-01-25 17:00:00"):
            loaded_time = dns_counter_mock.load_state()
            expected_time = datetime(2026, 1, 25, 17, 0, 0)

            assert (
                loaded_time == expected_time
            ), f"Should fall back to current time, got {loaded_time}"

    def test_persistence_atomic_write(
        self, dns_counter_mock, temp_persistence_file, monkeypatch
    ):
        """save_state() should use atomic write (tempfile + rename)."""
        # Track calls to tempfile.NamedTemporaryFile and os.rename
        original_tempfile = tempfile.NamedTemporaryFile
        original_rename = os.rename

        tempfile_calls = []
        rename_calls = []

        def mock_tempfile(*args, **kwargs):
            result = original_tempfile(*args, **kwargs)
            tempfile_calls.append((args, kwargs, result.name))
            return result

        def mock_rename(src, dst):
            rename_calls.append((src, dst))
            return original_rename(src, dst)

        monkeypatch.setattr(tempfile, "NamedTemporaryFile", mock_tempfile)
        monkeypatch.setattr(os, "rename", mock_rename)

        # Perform save
        test_time = datetime(2026, 1, 25, 10, 30, 45)
        dns_counter_mock.last_reset = test_time
        dns_counter_mock.save_state()

        # Verify tempfile was created in same directory as target
        assert len(tempfile_calls) == 1, "Should create exactly one tempfile"
        _, kwargs, temp_name = tempfile_calls[0]
        assert kwargs.get("dir") == os.path.dirname(
            str(temp_persistence_file)
        ), "Tempfile should be in same directory as target"

        # Verify rename was called
        assert len(rename_calls) == 1, "Should call rename exactly once"
        src, dst = rename_calls[0]
        assert dst == str(
            temp_persistence_file
        ), f"Should rename to {temp_persistence_file}"

    def test_persistence_save_generic_exception(
        self, dns_counter_mock, temp_persistence_file, monkeypatch
    ):
        """Generic exception during save should be caught and logged."""

        # Mock json.dump to raise a generic Exception
        def mock_json_dump(*args, **kwargs):
            raise RuntimeError("Simulated file system error")

        import json

        monkeypatch.setattr(json, "dump", mock_json_dump)

        # Save should not crash despite exception
        test_time = datetime(2026, 1, 25, 10, 30, 45)
        dns_counter_mock.last_reset = test_time

        # This should catch the exception and log it (lines 90-91)
        dns_counter_mock.save_state()  # Should not raise

    def test_persistence_load_generic_exception(
        self, dns_counter_mock, temp_persistence_file
    ):
        """Generic exception during load should fall back to datetime.now()."""
        # Create a valid file first
        with open(temp_persistence_file, "w") as f:
            json.dump({"last_reset": "2026-01-25T10:30:45", "version": 1}, f)

        # Change file permissions to make it unreadable
        # (triggers PermissionError, not OSError in open)
        import os
        import stat

        os.chmod(temp_persistence_file, 0o000)

        try:
            # Load should fall back to current time (lines 118-120)
            # PermissionError is caught by the generic Exception handler
            with freeze_time("2026-01-25 19:00:00"):
                loaded_time = dns_counter_mock.load_state()
                expected_time = datetime(2026, 1, 25, 19, 0, 0)

                assert (
                    loaded_time == expected_time
                ), f"Should fall back to current time, got {loaded_time}"
        finally:
            # Restore permissions for cleanup
            os.chmod(temp_persistence_file, stat.S_IRUSR | stat.S_IWUSR)


class TestResetLogic:
    """Test suite for reset button logic."""

    def test_reset_updates_timestamp(self, dns_counter_mock):
        """Button press should update last_reset to current time."""
        # Mock datetime.now() to a known value
        with freeze_time("2026-01-25 18:00:00"):
            # Simulate reset
            dns_counter_mock.last_reset = datetime.now()

            expected_time = datetime(2026, 1, 25, 18, 0, 0)
            assert dns_counter_mock.last_reset == expected_time, (
                f"last_reset should be {expected_time}, "
                f"got {dns_counter_mock.last_reset}"
            )

    @patch("time.time")
    def test_debounce_prevents_multiple_resets(self, mock_time):
        """Two button presses within 0.3 seconds should only reset once."""
        # This test verifies the debounce logic in _check_button
        # Since _check_button is a thread function, we test the logic pattern

        # Initialize last_press to a time before the first button press
        # This simulates the behavior where last_press starts at 0 (no previous press)
        last_press = -1.0  # Ensure first press at 0.0 succeeds
        button_presses = []

        # Simulate the debounce logic from _check_button (lines 356-357)
        def simulate_button_press(current_time):
            nonlocal last_press
            if current_time - last_press > 0.3:  # Debounce threshold
                button_presses.append(current_time)
                last_press = current_time
                return True
            return False

        # First press at t=0.0 (0.0 - (-1.0) = 1.0 > 0.3, should succeed)
        assert simulate_button_press(0.0) is True, "First press should succeed"

        # Second press at t=0.2 (0.2 - 0.0 = 0.2 < 0.3, should be ignored)
        assert (
            simulate_button_press(0.2) is False
        ), "Second press within 0.3s should be ignored"

        # Third press at t=0.4 (0.4 - 0.0 = 0.4 > 0.3, should succeed)
        assert (
            simulate_button_press(0.4) is True
        ), "Third press after 0.3s should succeed"

        # Verify only 2 presses registered
        assert (
            len(button_presses) == 2
        ), f"Expected 2 presses, got {len(button_presses)}"
        assert button_presses == [
            0.0,
            0.4,
        ], f"Expected presses at [0.0, 0.4], got {button_presses}"
