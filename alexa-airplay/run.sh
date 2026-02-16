#!/bin/bash
set -e

# Use wrapper script if it exists, otherwise run directly
if [ -f /data/start_app.sh ]; then
    export LOG_LEVEL="DEBUG"
    exec /data/start_app.sh
fi

# Source bashio for logging
source /usr/lib/bashio/init.sh || true

# Set up environment
export ADDON_DIR="/app"
export DATA_DIR="/data"
export CONFIG_DIR="/data/config"
export LOG_DIR="/data/logs"

# Create directories if they don't exist
mkdir -p "$CONFIG_DIR" "$LOG_DIR"

# Set logging level (can be set via addon options)
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Get configuration
AMAZON_CLIENT_ID=$(bashio::config 'amazon_client_id' 2>/dev/null || echo "")
AMAZON_CLIENT_SECRET=$(bashio::config 'amazon_client_secret' 2>/dev/null || echo "")
AMAZON_REDIRECT_URI=$(bashio::config 'amazon_redirect_uri' 2>/dev/null || echo "http://localhost:8000/oauth/callback")
AIRPLAY_PORT=$(bashio::config 'airplay_port' 2>/dev/null || echo "5000")

# Export for Python application
export AMAZON_CLIENT_ID
export AMAZON_CLIENT_SECRET
export AMAZON_REDIRECT_URI
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
