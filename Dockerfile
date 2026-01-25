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

# Stage 2: Development image
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
