# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Web interface for remote monitoring and control (`web_server.py`)
  - Live timer display matching LED matrix format
  - Reset button with audio playback
  - REST API endpoints (`/api/state`, `/api/reset`)
  - Mobile-friendly responsive design
- Astro/Starlight documentation site in `docs/` directory
- GitHub Actions CI/CD workflow for automated Docker image builds
  - Builds arm64 images for Raspberry Pi using QEMU
  - Pushes to GitHub Container Registry (`ghcr.io`)
  - Tags: `latest`, `main`, and commit SHA
- Production Docker configuration (`docker-compose.prod.yml`) with hardware support
- Docker config file (`config.docker.yaml`) for container deployments
- Hardware device mapping for audio (`/dev/snd`) and GPIO (`/dev/gpiochip0`)
- Stub implementations for rgbmatrix Pillow shim to avoid header dependency
- Support for both gpiod v1 and v2 APIs (auto-detected)
- Configurable `audio_device` option for specifying ALSA device (e.g., `plughw:Headphones`)
- Device availability check at startup with retry loop

### Fixed
- Web interface and LED display now share synchronized state via callbacks
- UTC timezone handling throughout codebase (prevents naive/aware datetime mixing)
- Web UI polls every 2 seconds for responsive updates from physical button
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
- Pre-built images available: `docker pull ghcr.io/asachs01/dnsfail:latest`

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
