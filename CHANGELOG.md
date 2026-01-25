# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Production Docker configuration (`docker-compose.prod.yml`) with hardware support
- Docker config file (`config.docker.yaml`) for container deployments
- Hardware device mapping for audio (`/dev/snd`) and GPIO (`/dev/gpiochip0`)
- Stub implementations for rgbmatrix Pillow shim to avoid header dependency
- Support for both gpiod v1 and v2 APIs (auto-detected)
- Configurable `audio_device` option for specifying ALSA device (e.g., `plughw:Headphones`)
- Device availability check at startup with retry loop

### Fixed
- GPIO button now works in Docker with gpiod v2 API
- Audio playback in Docker using explicit device selection

### Notes
- Docker deployment requires udev rule for audio device permissions:
  ```
  # /etc/udev/rules.d/99-alsa-permissions.rules
  KERNEL=="pcmC2*", MODE="0666"
  KERNEL=="controlC2", MODE="0666"
  ```
- Audio playback requires WAV format; MP3 files need conversion

## [0.1.0] - 2025-01-24
### Added
- Core timer functionality for tracking DNS queries.
- Display count on an RGB LED matrix.
- Reset functionality via a physical button.
- Audio feedback for interactions.
- `systemd` service file for running as a background service.
- Installation script (`install.sh`) for easy setup.
- MIT License.

### Fixed
- Corrected paths in the service file for production deployment.
