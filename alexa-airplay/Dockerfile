ARG BUILD_FROM=ghcr.io/home-assistant/base:latest
FROM ${BUILD_FROM}

# Install only essential Python packages using apk (Alpine)
RUN apk add --no-cache python3 py3-pip

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application code
COPY app ./app

# Create data directories
RUN mkdir -p /data/config /data/logs

# Copy s6-overlay service files
COPY rootfs /

# Expose ports
EXPOSE 8000 5001
