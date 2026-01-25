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

### Known Issues
- Docker production mode has gpiod API version mismatch (v2 vs v1)
- Audio playback requires WAV format; MP3 files need conversion or alternative player

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
