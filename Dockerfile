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

# Build and install rpi-rgb-led-matrix (without optional Pillow support)
# Note: We remove the Pillow shim files before build since we don't need image support
RUN git clone https://github.com/hzeller/rpi-rgb-led-matrix.git /tmp/matrix && \
    cd /tmp/matrix && \
    make -C lib && \
    cd /tmp/matrix/bindings/python && \
    rm -f rgbmatrix/shims/pillow.c rgbmatrix/shims/pillow.h && \
    CFLAGS="-I../../include" pip install --no-cache-dir . && \
    rm -rf /tmp/matrix

# Copy application code
COPY dns_counter.py .
COPY fonts/ ./fonts/
COPY fail.mp3 .

# Create logs directory
RUN mkdir -p /app/logs

# Set environment for production mode
ENV MOCK_MODE=0
ENV PYTHONUNBUFFERED=1

# Entrypoint for running with hardware
ENTRYPOINT ["python", "dns_counter.py"]
CMD []
