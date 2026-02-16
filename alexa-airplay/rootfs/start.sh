#!/usr/bin/with-contenv bashio
# ──────────────────────────────────────────────────────────────
# Alexa AirPlay Bridge – Container Startup
# ──────────────────────────────────────────────────────────────
set -e

echo "───────────────────────────────────────"
echo "  Alexa AirPlay Bridge – Starting…"
echo "───────────────────────────────────────"

# ── directories ──
mkdir -p /data/config /data/logs

# ── environment ──
export ADDON_DIR="/app"
export DATA_DIR="/data"
export CONFIG_DIR="/data/config"
export LOG_DIR="/data/logs"
export HA_TOKEN="${SUPERVISOR_TOKEN:-}"
export HA_URL="http://supervisor"

# ── read addon options via bashio ──
AMAZON_CLIENT_ID="$(bashio::config 'amazon_client_id' 2>/dev/null || echo '')"
AMAZON_CLIENT_SECRET="$(bashio::config 'amazon_client_secret' 2>/dev/null || echo '')"
AIRPLAY_PORT="$(bashio::config 'airplay_port' 2>/dev/null || echo '5001')"
DEBUG_LOGGING="$(bashio::config 'debug_logging' 2>/dev/null || echo 'false')"

export AMAZON_CLIENT_ID
export AMAZON_CLIENT_SECRET
export AIRPLAY_PORT

if [ "$DEBUG_LOGGING" = "true" ]; then
  export LOG_LEVEL="DEBUG"
else
  export LOG_LEVEL="${LOG_LEVEL:-INFO}"
fi

# Web port MUST match ingress_port in config.json (8099)
export WEB_PORT=8099

echo "Log level     : $LOG_LEVEL"
echo "Web UI port   : $WEB_PORT"
echo "AirPlay port  : $AIRPLAY_PORT"

# ── launch ──
cd /app
exec python3 -u app/main.py
