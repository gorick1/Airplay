# API Reference - Alexa AirPlay Bridge

Complete API documentation for the addon's REST endpoints and integrations.

## Base URL

```
http://your-home-assistant-ip:8000/api
```

All requests return JSON responses.

## Authentication

Internal requests (from Home Assistant):
- Include header: `Authorization: Bearer $SUPERVISOR_TOKEN`
- Automatically handled by addon

External requests:
- OAuth required for certain endpoints
- See specific endpoint documentation

## Endpoints

### Health Check

**GET** `/health`

Check addon health status.

**Response**:
```json
{
  "status": "healthy",
  "authenticated": true,
  "devices": 3,
  "uptime": 3600
}
```

**Status codes**:
- `200` - Addon running normally
- `503` - Addon initializing or unhealthy

---

### Devices

#### List Devices

**GET** `/devices`

Get all virtual AirPlay devices and their current status.

**Response**:
```json
[
  {
    "id": "airplay_device_abc123",
    "name": "Living Room Echo",
    "type": "device",
    "alexa_device_id": "device_abc123",
    "state": "playing",
    "volume": 75,
    "current_track": "Blinding Lights",
    "artist": "The Weeknd"
  },
  {
    "id": "airplay_device_xyz789",
    "name": "Kitchen Echo Dot",
    "type": "device",
    "alexa_device_id": "device_xyz789",
    "state": "stopped",
    "volume": 50,
    "current_track": null,
    "artist": null
  }
]
```

**Fields**:
- `id` - Unique virtual device ID
- `name` - Display name
- `type` - "device" or "group"
- `alexa_device_id` - Amazon device ID
- `state` - "playing", "paused", or "stopped"
- `volume` - 0-100
- `current_track` - Track name if playing
- `artist` - Artist name if playing

**Query parameters**:
- `type=device` - Only devices (not groups)
- `state=playing` - Only devices currently playing

**Examples**:
```bash
# Get all devices
curl http://localhost:8000/api/devices

# Get only playing devices
curl http://localhost:8000/api/devices?state=playing

# Get only group devices
curl http://localhost:8000/api/devices?type=group
```

---

#### Get Device Details

**GET** `/devices/{device_id}`

Get detailed information about a specific device.

**Response**:
```json
{
  "id": "airplay_device_abc123",
  "name": "Living Room Echo",
  "type": "device",
  "alexa_device_id": "device_abc123",
  "device_model": "Echo Dot (4th Gen)",
  "state": "playing",
  "volume": 75,
  "current_track": "Blinding Lights",
  "artist": "The Weeknd",
  "album": "After Hours",
  "duration_ms": 200040,
  "position_ms": 85000,
  "muted": false,
  "shuffle": false,
  "repeat": "off",
  "last_active": "2024-01-15T10:30:00Z",
  "capabilities": [
    "play",
    "pause",
    "next",
    "previous",
    "volume",
    "shuffle",
    "repeat"
  ]
}
```

**Examples**:
```bash
curl http://localhost:8000/api/devices/airplay_device_abc123
```

---

#### Control Device Playback

**POST** `/devices/{device_id}/command`

Send playback control command to device.

**Request body**:
```json
{
  "action": "play|pause|next|previous|stop",
  "volume": 0-100,
  "shuffle": true|false,
  "repeat": "off|one|all"
}
```

**Response**:
```json
{
  "success": true,
  "command": "play",
  "device_id": "airplay_device_abc123"
}
```

**Actions**:

| Action | Effect |
|--------|--------|
| `play` | Start playback or resume if paused |
| `pause` | Pause current playback |
| `next` | Skip to next track |
| `previous` | Jump to previous track |
| `stop` | Stop playback and disconnect |

**Examples**:
```bash
# Play
curl -X POST http://localhost:8000/api/devices/airplay_device_abc123/command \
  -H "Content-Type: application/json" \
  -d '{"action": "play"}'

# Set volume to 60%
curl -X POST http://localhost:8000/api/devices/airplay_device_abc123/command \
  -H "Content-Type: application/json" \
  -d '{"volume": 60}'

# Enable shuffle
curl -X POST http://localhost:8000/api/devices/airplay_device_abc123/command \
  -H "Content-Type: application/json" \
  -d '{"shuffle": true}'

# Next track + set volume
curl -X POST http://localhost:8000/api/devices/airplay_device_abc123/command \
  -H "Content-Type: application/json" \
  -d '{"action": "next", "volume": 50}'
```

**Status codes**:
- `200` - Command sent successfully
- `400` - Invalid request format
- `404` - Device not found
- `503` - Device unreachable or not authenticated

---

### Configuration

#### Get Configuration

**GET** `/config`

Get current addon configuration.

**Response**:
```json
{
  "amazon_client_id": "amzn1.application-...",
  "amazon_client_secret": "***",
  "airplay_port": 5000,
  "web_port": 8000,
  "debug": false,
  "authenticated": true,
  "config_dir": "/data/config",
  "data_dir": "/data"
}
```

**Note**: `amazon_client_secret` is masked for security.

---

#### Save Configuration

**POST** `/config`

Update addon configuration.

**Request body**:
```json
{
  "amazon_client_id": "your-client-id",
  "amazon_client_secret": "your-client-secret",
  "airplay_port": 5000,
  "debug": false
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Configuration saved and applied"
}
```

**Examples**:
```bash
curl -X POST http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "amazon_client_id": "amzn1.application-...",
    "amazon_client_secret": "your-secret"
  }'
```

**Status codes**:
- `200` - Configuration saved
- `400` - Invalid configuration
- `403` - Not authorized
- `500` - Write error

---

### OAuth

#### Get Authorization URL

**GET** `/oauth/authorize`

Get OAuth authorization URL for Amazon login.

**Response**:
```json
{
  "url": "https://www.amazon.com/ap/oa?client_id=...&redirect_uri=..."
}
```

**Returns the full Amazon OAuth URL to redirect user to.**

---

#### OAuth Callback

**GET** `/oauth/callback`

Handles OAuth callback from Amazon after user authorization.

**Query parameters**:
- `code` - Authorization code from Amazon

**Response** (HTML):
```html
<html>
  <body>
    <h2>✓ Authorization Successful!</h2>
    <p>You can close this window and return to the configuration page.</p>
  </body>
</html>
```

**This endpoint is called automatically by the browser after user logs in.**

---

### Streaming

#### Stream Metadata

**WebSocket** `/ws/metadata`

Real-time device status updates via WebSocket.

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/metadata');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Device update:', update);
};
```

**Message format**:
```json
{
  "type": "device_update",
  "device_id": "airplay_device_abc123",
  "state": "playing",
  "volume": 75,
  "track": "Blinding Lights",
  "artist": "The Weeknd",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Message types**:
- `device_update` - Device state changed
- `device_discovered` - New device found
- `device_lost` - Device disconnected
- `connection_status` - Amazon API status

---

### Admin

#### Get Addon Status

**GET** `/admin/status`

Get detailed addon operational status.

**Response**:
```json
{
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "authenticated": true,
  "devices_count": 3,
  "services": {
    "web_ui": "running",
    "device_manager": "running",
    "airplay_server": "running",
    "amazon_api": "ready"
  },
  "memory_usage_mb": 85,
  "cpu_usage_percent": 2.3,
  "last_api_call": "2024-01-15T10:30:00Z",
  "errors": []
}
```

---

#### Get Logs

**GET** `/admin/logs`

Get recent addon logs.

**Query parameters**:
- `level=ERROR|WARNING|INFO|DEBUG` - Filter by log level
- `lines=50` - Number of lines to return (default: 50)
- `device_id=...` - Filter by device

**Response**:
```json
{
  "logs": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "level": "INFO",
      "message": "Device discovered: Living Room Echo",
      "device_id": "airplay_device_abc123"
    }
  ],
  "total_lines": 2500,
  "returned_lines": 50
}
```

**Examples**:
```bash
# Get last 100 error logs
curl "http://localhost:8000/api/admin/logs?level=ERROR&lines=100"

# Get logs for specific device
curl "http://localhost:8000/api/admin/logs?device_id=airplay_device_abc123"
```

---

## Error Responses

All errors return JSON format:

```json
{
  "error": "Error name",
  "message": "Human readable error message",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common Errors

| Code | Message | Cause |
|------|---------|-------|
| `AUTH_REQUIRED` | Authentication required | Not authorized for this endpoint |
| `NOT_FOUND` | Device not found | Device doesn't exist or was removed |
| `INVALID_REQUEST` | Invalid request format | Bad JSON or missing required fields |
| `NOT_AUTHENTICATED` | Not authenticated with Amazon | Need to authorize first |
| `DEVICE_UNREACHABLE` | Device unreachable | Echo device offline or network issue |
| `API_ERROR` | Amazon API error | Rate limited or service issue |
| `INTERNAL_ERROR` | Internal server error | Addon error - check logs |

---

## Rate Limiting

Current rate limits (per minute):
- Device control: 100 requests
- Configuration: 10 requests
- Streaming: Unlimited (WebSocket)

Rate limit headers in response:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705315200
```

If rate limited, returns `429 Too Many Requests`.

---

## Examples

### JavaScript/Fetch

```javascript
// Get all devices
async function getDevices() {
  const response = await fetch('http://localhost:8000/api/devices');
  const devices = await response.json();
  console.log(devices);
}

// Send command
async function playDevice(deviceId) {
  await fetch(`http://localhost:8000/api/devices/${deviceId}/command`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'play' })
  });
}

// Subscribe to updates
function subscribeToUpdates() {
  const ws = new WebSocket('ws://localhost:8000/ws/metadata');
  ws.onmessage = (e) => console.log(JSON.parse(e.data));
}
```

### Python

```python
import requests
import asyncio
import json

BASE_URL = 'http://localhost:8000/api'

# Get devices
def get_devices():
    response = requests.get(f'{BASE_URL}/devices')
    return response.json()

# Send command
def send_command(device_id, action):
    response = requests.post(
        f'{BASE_URL}/devices/{device_id}/command',
        json={'action': action}
    )
    return response.json()

# List all devices
devices = get_devices()
for device in devices:
    print(f"{device['name']}: {device['state']}")

# Play first device
if devices:
    send_command(devices[0]['id'], 'play')
```

### cURL

```bash
# Get devices
curl http://localhost:8000/api/devices | jq

# Get device status
curl http://localhost:8000/api/devices/airplay_device_abc123

# Send play command
curl -X POST http://localhost:8000/api/devices/airplay_device_abc123/command \
  -H "Content-Type: application/json" \
  -d '{"action": "play"}'

# Set volume to 70%
curl -X POST http://localhost:8000/api/devices/airplay_device_abc123/command \
  -H "Content-Type: application/json" \
  -d '{"volume": 70}'
```

---

## Webhooks

Coming in v1.1:
- Device state change webhook
- Error notification webhook
- Custom callback support

---

## Changelog

### v1.0.0
- Initial API release
- Core device and playback endpoints
- OAuth and configuration management
- WebSocket metadata streaming

---

For questions or issues, see the [main documentation](README.md).
