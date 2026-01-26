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
from datetime import datetime
from typing import Any, Dict, Optional

from flask import Flask, jsonify, render_template, request
import yaml

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

    def __init__(self, config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None):
        """Initialize the web server.

        Args:
            config: Configuration dictionary (optional, loads from file if not provided)
            config_path: Path to config file (default: /usr/local/share/dnsfail/config.yaml)
        """
        if config is None:
            config_path = config_path or "/usr/local/share/dnsfail/config.yaml"
            config = load_config(config_path)

        self.config = config
        self.persistence_file = config["persistence_file"]
        self.audio_file = config["audio_file"]
        self.audio_device = config.get("audio_device", "")
        self.port = config["web_port"]

        # Lock for state file operations
        self._lock = threading.Lock()

        # Create Flask app
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.app = Flask(__name__, template_folder=template_dir)

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
            state = self._load_state()
            return jsonify({
                "last_reset": state["last_reset"],
                "success": True
            })

        @self.app.route("/api/reset", methods=["POST"])
        def reset_timer():
            """Reset the timer and play audio."""
            try:
                new_reset = datetime.now()
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
                # If no state file, return current time
                return {"last_reset": datetime.now().isoformat()}
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
                return {"last_reset": datetime.now().isoformat()}

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
