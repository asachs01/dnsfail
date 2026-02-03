# Stage 1: Base image with dependencies
FROM python:3.11-slim AS base

# Install system dependencies including audio support
RUN apt-get update && apt-get install -y \
    build-essential \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Development image (mock mode - no hardware dependencies)
FROM base AS development

# Copy application code
COPY dns_counter.py .
COPY mocks/ ./mocks/
COPY fonts/ ./fonts/
COPY fail.mp3 .

# Create logs directory
RUN mkdir -p /app/logs

# Set environment for mock mode
ENV MOCK_MODE=1
ENV PYTHONUNBUFFERED=1

# Entrypoint for running in mock mode
ENTRYPOINT ["python", "dns_counter.py", "--mock"]
CMD []

# Stage 3: Production image (Raspberry Pi hardware - requires arm64)
FROM python:3.11-slim AS production

# Install system dependencies for hardware access
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    alsa-utils \
    libgpiod-dev \
    python3-dev \
    cython3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install gpiod Python bindings
RUN pip install --no-cache-dir gpiod

# Build and install rpi-rgb-led-matrix with Python bindings
# Create stub pillow shim files since we don't need PIL Image support
RUN git clone https://github.com/hzeller/rpi-rgb-led-matrix.git /tmp/matrix && \
    cd /tmp/matrix && \
    make -C lib && \
    cd bindings/python && \
    printf '%s\n' '#ifndef SHIMS_PIL_H' '#define SHIMS_PIL_H' '#ifdef __cplusplus' 'extern "C" {' '#endif' 'int** get_image32(void* im);' '#ifdef __cplusplus' '}' '#endif' '#endif' > rgbmatrix/shims/pillow.h && \
    printf '%s\n' '#include "pillow.h"' 'int** get_image32(void* im) { return 0; }' > rgbmatrix/shims/pillow.c && \
    make build-python PYTHON=$(which python3) && \
    make install-python PYTHON=$(which python3) && \
    rm -rf /tmp/matrix

# Copy application code
COPY dns_counter.py .
COPY web_server.py .
COPY metrics.py .
COPY templates/ ./templates/
COPY fonts/ ./fonts/
COPY fail.mp3 .
COPY entrypoint.sh .
COPY play_audio.sh .

# Create logs directory
RUN mkdir -p /app/logs

# Set environment for production mode
ENV MOCK_MODE=0
ENV PYTHONUNBUFFERED=1

# Entrypoint for running with hardware (uses bash script to wait for audio devices)
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
CMD []
