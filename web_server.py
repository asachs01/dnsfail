#!/usr/bin/env python3
"""Web server for DNS Incident Timer remote control and monitoring.

Provides a minimal web interface to view the current timer state and
trigger resets remotely. Designed to run alongside the main dns_counter
application, sharing the same state file.

No authentication - intended for local network use only.
"""

import json
import logging
import os
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from flask import Flask, Response, jsonify, render_template, request, send_file
import yaml

# Prometheus metrics - import from shared module
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from metrics import (
    RESET_COUNTER, SECONDS_SINCE_RESET, UPTIME_SECONDS,
    AUDIO_PLAYBACK_ERRORS, APP_START_TIME, PROMETHEUS_AVAILABLE
)

# Configure logging
logger = logging.getLogger("dns_counter.web")


def load_config(config_path: str = "/usr/local/share/dnsfail/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file with fallback to defaults."""
    DEFAULT_CONFIG = {
        "gpio_pin": 19,
        "brightness": 80,
        "audio_file": "/usr/local/share/dnsfail/media/fail.wav",
        "audio_device": "",
        "web_port": 5000,
        "persistence_file": "/usr/local/share/dnsfail/last_reset.json",
        "log_level": "INFO",
    }

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            loaded_config = yaml.safe_load(f)

        if loaded_config:
            config = DEFAULT_CONFIG.copy()
            config.update(loaded_config)
            return config
        return DEFAULT_CONFIG

    except Exception as e:
        logger.warning(f"Could not load config from {config_path}: {e}")
        return DEFAULT_CONFIG


class WebServer:
    """Flask-based web server for timer control.

    Provides:
        - GET / : Web interface
        - GET /api/state : Current timer state (JSON)
        - POST /api/reset : Reset the timer
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
        reset_callback: Optional[callable] = None,
        get_state_callback: Optional[callable] = None,
    ):
        """Initialize the web server.

        Args:
            config: Configuration dictionary (optional, loads from file if not provided)
            config_path: Path to config file (default: /usr/local/share/dnsfail/config.yaml)
            reset_callback: Optional callback to invoke on reset (for state sync with main app)
            get_state_callback: Optional callback to get current state from main app
        """
        if config is None:
            config_path = config_path or "/usr/local/share/dnsfail/config.yaml"
            config = load_config(config_path)

        self.config = config
        self.persistence_file = config["persistence_file"]
        self.audio_file = config["audio_file"]
        self.audio_device = config.get("audio_device", "")
        self.port = config["web_port"]
        self._reset_callback = reset_callback
        self._get_state_callback = get_state_callback

        # Lock for state file operations
        self._lock = threading.Lock()

        # Create Flask app with static folder for audio files
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        self.app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register Flask routes."""

        @self.app.route("/")
        def index():
            """Serve the main web interface."""
            return render_template("index.html")

        @self.app.route("/api/state")
        def get_state():
            """Get current timer state."""
            # Use callback if available (syncs with main app), otherwise read file
            if self._get_state_callback:
                last_reset = self._get_state_callback()
                return jsonify({
                    "last_reset": last_reset.isoformat() if hasattr(last_reset, 'isoformat') else str(last_reset),
                    "success": True
                })
            state = self._load_state()
            return jsonify({
                "last_reset": state["last_reset"],
                "success": True
            })

        @self.app.route("/api/audio")
        def get_audio():
            """Serve the reset audio file for browser playback."""
            if os.path.exists(self.audio_file):
                return send_file(self.audio_file, mimetype="audio/wav")
            return jsonify({"error": "Audio file not found"}), 404

        @self.app.route("/metrics")
        def metrics():
            """Prometheus metrics endpoint."""
            # Update gauge metrics
            UPTIME_SECONDS.set(time.time() - APP_START_TIME)

            # Calculate seconds since last reset
            if self._get_state_callback:
                last_reset = self._get_state_callback()
            else:
                state = self._load_state()
                last_reset_str = state.get("last_reset")
                if last_reset_str:
                    last_reset = datetime.fromisoformat(last_reset_str.replace("Z", "+00:00"))
                else:
                    last_reset = None

            if last_reset:
                now = datetime.now(timezone.utc)
                if hasattr(last_reset, 'tzinfo') and last_reset.tzinfo is None:
                    last_reset = last_reset.replace(tzinfo=timezone.utc)
                seconds_since = (now - last_reset).total_seconds()
                SECONDS_SINCE_RESET.set(seconds_since)

            return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

        @self.app.route("/api/reset", methods=["POST"])
        def reset_timer():
            """Reset the timer and play audio."""
            try:
                # Increment reset counter for web source
                RESET_COUNTER.labels(source='web').inc()

                # Use callback if available (syncs with main app and plays audio)
                if self._reset_callback:
                    new_reset = self._reset_callback()
                    return jsonify({
                        "success": True,
                        "last_reset": new_reset.isoformat() if hasattr(new_reset, 'isoformat') else str(new_reset),
                        "message": "Timer reset successfully"
                    })

                # Fallback: standalone mode (no main app)
                new_reset = datetime.now(timezone.utc)
                self._save_state(new_reset)
                self._play_audio()

                return jsonify({
                    "success": True,
                    "last_reset": new_reset.isoformat(),
                    "message": "Timer reset successfully"
                })
            except Exception as e:
                logger.error(f"Reset failed: {e}")
                return jsonify({
                    "success": False,
                    "message": str(e)
                }), 500

    def _load_state(self) -> Dict[str, Any]:
        """Load the current state from persistence file."""
        with self._lock:
            try:
                with open(self.persistence_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data
            except FileNotFoundError:
                # If no state file, return current time in UTC
                return {"last_reset": datetime.now(timezone.utc).isoformat()}
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
                return {"last_reset": datetime.now(timezone.utc).isoformat()}

    def _save_state(self, last_reset: datetime) -> None:
        """Save state to persistence file using atomic write."""
        with self._lock:
            try:
                data = {"last_reset": last_reset.isoformat(), "version": 1}
                dir_path = os.path.dirname(self.persistence_file)

                # Ensure directory exists
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)

                # Atomic write
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    delete=False,
                    dir=dir_path or ".",
                    encoding="utf-8",
                ) as tf:
                    json.dump(data, tf)
                os.rename(tf.name, self.persistence_file)
                logger.info(f"Saved state: {data}")
            except Exception as e:
                logger.error(f"Failed to save state: {e}")
                raise

    def _play_audio(self) -> None:
        """Play the reset audio file."""
        if not os.path.exists(self.audio_file):
            logger.warning(f"Audio file not found: {self.audio_file}")
            return

        try:
            cmd = ["aplay"]
            if self.audio_device:
                cmd.extend(["-D", self.audio_device])
            cmd.append(self.audio_file)

            logger.debug(f"Playing audio: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                logger.error(f"Audio playback failed: {result.stderr}")
            else:
                logger.debug("Audio playback completed")
        except subprocess.TimeoutExpired:
            logger.error("Audio playback timed out")
        except Exception as e:
            logger.error(f"Audio playback error: {e}")

    def run(self, host: str = "0.0.0.0", debug: bool = False) -> None:
        """Start the web server.

        Args:
            host: Host to bind to (default: 0.0.0.0 for all interfaces)
            debug: Enable Flask debug mode
        """
        logger.info(f"Starting web server on http://{host}:{self.port}")
        self.app.run(host=host, port=self.port, debug=debug, threaded=True)


def create_app(config_path: Optional[str] = None) -> Flask:
    """Create Flask app for use with WSGI servers.

    Args:
        config_path: Path to configuration file

    Returns:
        Configured Flask application
    """
    server = WebServer(config_path=config_path)
    return server.app


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DNS Incident Timer Web Server")
    parser.add_argument(
        "--config",
        default="/usr/local/share/dnsfail/config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port to listen on (overrides config)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(name)s: %(levelname)s %(message)s"
    )

    # Load config and create server
    config = load_config(args.config)
    if args.port:
        config["web_port"] = args.port

    server = WebServer(config=config)
    server.run(host=args.host, debug=args.debug)
