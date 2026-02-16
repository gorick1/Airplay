#!/bin/sh
set -e

# Set up environment
export ADDON_DIR="/app"
export DATA_DIR="/data"
export CONFIG_DIR="/data/config"
export LOG_DIR="/data/logs"

# Create directories if they don't exist
mkdir -p "$CONFIG_DIR" "$LOG_DIR"

# Set default values
export LOG_LEVEL="INFO"
export AMAZON_CLIENT_ID=""
export AMAZON_CLIENT_SECRET=""
export AIRPLAY_PORT="5001"
export HA_TOKEN="${SUPERVISOR_TOKEN}"
export HA_URL="http://supervisor"

# Log startup
echo "Starting Alexa AirPlay Bridge addon..."
echo "Log level: $LOG_LEVEL"
echo "AirPlay Port: $AIRPLAY_PORT"
echo "Data directory: $DATA_DIR"

# Start the main application
cd /app
exec python3 -u app/main.py
