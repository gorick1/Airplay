ARG BUILD_FROM=ghcr.io/home-assistant/base:latest
FROM ${BUILD_FROM}

# Install only essential Python packages using apk (Alpine)
RUN apk add --no-cache python3 py3-pip

# Set working directory
WORKDIR /app

# Copy requirements first
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

# Run the application
CMD [ "/app/run.sh" ]
