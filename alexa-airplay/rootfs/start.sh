#!/bin/sh
set -e

# Setup environment
export ADDON_DIR="/app"
export DATA_DIR="/data"
export CONFIG_DIR="/data/config"
export LOG_DIR="/data/logs"

# Create directories
mkdir -p "$CONFIG_DIR" "$LOG_DIR"

# Set defaults
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export AIRPLAY_PORT="${AIRPLAY_PORT:-5001}"
export HA_TOKEN="${SUPERVISOR_TOKEN}"
export HA_URL="http://supervisor"

# Log startup
echo "=========================================="
echo "Starting Alexa AirPlay Bridge addon..."
echo "Log level: $LOG_LEVEL"
echo "AirPlay Port: $AIRPLAY_PORT"
echo "Data directory: $DATA_DIR"
echo "=========================================="

# Start Python application
cd /app
exec python3 -u app/main.py
