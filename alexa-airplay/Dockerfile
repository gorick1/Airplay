ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest
FROM ${BUILD_FROM}

# Install Python and pip
RUN apk add --no-cache python3 py3-pip

# Set working directory
WORKDIR /app

# Copy requirements first (for docker layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application code
COPY app ./app

# Copy startup script
COPY rootfs/start.sh /run.sh
RUN chmod +x /run.sh

# Create data directories
RUN mkdir -p /data/config /data/logs

# Ingress port
EXPOSE 8099

CMD ["/run.sh"]
