ARG BUILD_FROM=ghcr.io/home-assistant/base:latest
FROM ${BUILD_FROM}

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    libzlib1g-dev \
    libavahi-client-dev \
    libavahi-core-dev \
    avahi-daemon \
    libasound2-dev \
    libpulse-dev \
    libudev-dev \
    pkg-config \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install shairport-sync for AirPlay receiver capabilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    shairport-sync \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY run.sh .

# Make run script executable
RUN chmod +x run.sh

# Create data directories
RUN mkdir -p /data/config /data/logs

# Expose ports
EXPOSE 8000 5000 5353/udp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD [ "/app/run.sh" ]
