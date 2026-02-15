#!/bin/bash
set -e

# Source bashio for logging
source /usr/lib/bashio/init.sh || true

# Set up environment
export ADDON_DIR="/app"
export DATA_DIR="/data"
export CONFIG_DIR="/data/config"
export LOG_DIR="/data/logs"

# Create directories if they don't exist
mkdir -p "$CONFIG_DIR" "$LOG_DIR"

# Set logging level
if bashio::config.true 'debug_logging' 2>/dev/null; then
    export LOG_LEVEL="DEBUG"
else
    export LOG_LEVEL="INFO"
fi

# Get configuration
AMAZON_CLIENT_ID=$(bashio::config 'amazon_client_id' 2>/dev/null || echo "")
AMAZON_CLIENT_SECRET=$(bashio::config 'amazon_client_secret' 2>/dev/null || echo "")
AIRPLAY_PORT=$(bashio::config 'airplay_port' 2>/dev/null || echo "5000")

# Export for Python application
export AMAZON_CLIENT_ID
export AMAZON_CLIENT_SECRET
export AIRPLAY_PORT
export HA_TOKEN=$SUPERVISOR_TOKEN
export HA_URL="http://supervisor"

# Log startup
echo "Starting Alexa AirPlay Bridge addon..."
echo "Log level: $LOG_LEVEL"
echo "AirPlay Port: $AIRPLAY_PORT"

# Start the main application
cd /app
exec python3 -u app/main.py
