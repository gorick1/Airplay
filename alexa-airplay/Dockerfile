ARG BUILD_FROM=ghcr.io/home-assistant/base:latest
FROM ${BUILD_FROM}

# Install Python and pip
RUN apk add --no-cache python3 py3-pip

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy app code
COPY app ./app

# Copy s6-overlay service structure  
COPY rootfs /

# Create data directories
RUN mkdir -p /data/config /data/logs

# Expose ports
EXPOSE 8000 5001
