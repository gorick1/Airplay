"""
Web UI for Alexa Music Controller
Provides device discovery dashboard and playback controls.
Fully compatible with Home Assistant Ingress proxy.
"""

import json
import logging
from aiohttp import web

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# HTML – uses only relative URLs for HA Ingress compatibility
# ──────────────────────────────────────────────────────────────
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Alexa Music Controller</title>
<style>
:root{--bg:#1a1a2e;--card:#16213e;--accent:#0f3460;--blue:#53a8e2;--green:#4ecca3;
       --red:#e74c3c;--orange:#f39c12;--text:#eee;--muted:#999;--border:#2a3a5a}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,
     "Segoe UI",Roboto,sans-serif;padding:20px;max-width:960px;margin:0 auto}
h1{text-align:center;margin:20px 0;color:var(--blue)}
h2{color:var(--blue);margin-bottom:15px;font-size:1.2em}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;
      padding:24px;margin-bottom:20px}
.status-badge{display:inline-block;padding:4px 12px;border-radius:12px;font-size:0.85em;font-weight:600}
.status-ok{background:rgba(78,204,163,.15);color:var(--green)}
.status-warn{background:rgba(231,76,60,.15);color:var(--red)}
.status-playing{background:rgba(78,204,163,.15);color:var(--green)}
.status-idle,.status-off{background:rgba(153,153,153,.15);color:var(--muted)}
.status-paused{background:rgba(243,156,18,.15);color:var(--orange)}

label{display:block;margin:10px 0 4px;font-weight:600;color:var(--muted);font-size:.9em}
select,input[type=text]{width:100%;padding:10px 12px;border:1px solid var(--border);
      border-radius:8px;background:var(--bg);color:var(--text);font-size:.95em}
select:focus,input:focus{outline:none;border-color:var(--blue)}
button{padding:10px 20px;border:none;border-radius:8px;cursor:pointer;font-size:.95em;
       font-weight:600;transition:.2s}
.btn-primary{background:var(--blue);color:#fff}
.btn-primary:hover{background:#4298d2}
.btn-success{background:var(--green);color:#111}
.btn-success:hover{background:#3dbb92}
.btn-danger{background:var(--red);color:#fff}
.btn-danger:hover{background:#d63031}
.btn-small{padding:6px 14px;font-size:.85em}
.btn-row{display:flex;gap:10px;margin-top:15px;flex-wrap:wrap}
.msg{padding:10px 14px;border-radius:8px;margin:10px 0;font-size:.9em}
.msg-ok{background:rgba(78,204,163,.12);color:var(--green);border:1px solid rgba(78,204,163,.25)}
.msg-err{background:rgba(231,76,60,.12);color:var(--red);border:1px solid rgba(231,76,60,.25)}

.device-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;margin-top:14px}
.device-card{background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:16px;
             cursor:pointer;transition:.2s}
.device-card:hover{border-color:var(--blue)}
.device-card.selected{border-color:var(--green);box-shadow:0 0 0 2px rgba(78,204,163,.3)}
.device-card .name{font-weight:700;font-size:1em;margin-bottom:6px}
.device-card .meta{font-size:.82em;color:var(--muted)}
.device-card .now-playing{font-size:.82em;color:var(--green);margin-top:6px}

.controls{display:flex;gap:8px;align-items:center;justify-content:center;flex-wrap:wrap;margin-top:12px}
.controls button{font-size:1.2em;width:44px;height:44px;padding:0;display:flex;
                 align-items:center;justify-content:center;border-radius:50%;
                 background:var(--accent);color:var(--text);border:1px solid var(--border)}
.controls button:hover{background:var(--blue);color:#fff}
.volume-row{display:flex;align-items:center;gap:10px;margin-top:10px}
.volume-row input[type=range]{flex:1;accent-color:var(--blue)}
.volume-row span{min-width:36px;text-align:right;font-size:.9em}

.filter-row{display:flex;gap:10px;margin-bottom:14px;align-items:center}
.filter-row label{margin:0;white-space:nowrap}
.footer{text-align:center;color:var(--muted);font-size:.8em;margin-top:30px}
.info-box{background:rgba(83,168,226,.08);border:1px solid rgba(83,168,226,.2);
          border-radius:8px;padding:14px;margin-bottom:16px;font-size:.88em;color:var(--muted);line-height:1.5}
.info-box b{color:var(--blue)}
</style>
</head>
<body>
<h1>&#127925; Alexa Music Controller</h1>

<div id="msgArea"></div>

<!-- Status -->
<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <h2>Connection</h2>
    <span id="haBadge" class="status-badge status-warn">Checking...</span>
  </div>
  <p style="color:var(--muted);font-size:.85em;margin-top:8px">
    This add-on discovers your Echo/Alexa devices from Home Assistant and lets
    you control music playback on them.
  </p>
</div>

<!-- Info box about requirements -->
<div class="info-box" id="infoBox">
  <b>Requirements:</b> You need the <b>Alexa Media Player</b> custom component
  (install via HACS) to control Echo playback. It creates <code>media_player</code>
  entities for each Echo device.  The built-in Nabu Casa Alexa integration only
  exposes <i>your</i> HA devices to Alexa voice control — it does not create
  entities for Echo devices.
  <br><br>
  <b>Apple Music:</b> Link Apple Music to your Alexa account in the Amazon Alexa app
  first, then you can send &ldquo;play X on Apple Music&rdquo; commands from here.
</div>

<!-- Devices -->
<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <h2>Devices</h2>
    <div class="filter-row">
      <label><input type="checkbox" id="echoOnly" checked onchange="renderDevices()"> Echo only</label>
      <button class="btn-primary btn-small" onclick="refreshDevices()">Refresh</button>
    </div>
  </div>
  <div id="deviceGrid" class="device-grid">
    <p style="color:var(--muted)">Loading devices...</p>
  </div>
</div>

<!-- Playback controls -->
<div class="card" id="controlCard" style="display:none">
  <h2>Now Playing — <span id="selectedName">-</span></h2>
  <div id="nowPlaying" style="color:var(--muted);font-size:.9em;margin-bottom:10px">Nothing playing</div>
  <div class="controls">
    <button onclick="cmd('previous')" title="Previous">&#9198;</button>
    <button onclick="cmd('play')" title="Play">&#9654;&#65039;</button>
    <button onclick="cmd('pause')" title="Pause">&#9208;&#65039;</button>
    <button onclick="cmd('stop')" title="Stop">&#9209;&#65039;</button>
    <button onclick="cmd('next')" title="Next">&#9197;</button>
  </div>
  <div class="volume-row">
    <span style="color:var(--muted)">Vol</span>
    <input type="range" id="volumeSlider" min="0" max="100" value="50"
           oninput="document.getElementById('volLabel').textContent=this.value+'%'"
           onchange="setVolume(this.value)">
    <span id="volLabel">50%</span>
  </div>
</div>

<!-- Play music command -->
<div class="card" id="playCard" style="display:none">
  <h2>Play Music</h2>
  <label for="musicService">Service</label>
  <select id="musicService">
    <option value="custom">Voice Command (say anything)</option>
    <option value="APPLE_MUSIC">Apple Music</option>
    <option value="AMAZON_MUSIC">Amazon Music</option>
    <option value="SPOTIFY">Spotify</option>
    <option value="TUNEIN">TuneIn Radio</option>
  </select>
  <label for="musicQuery">What to play</label>
  <div style="display:flex;gap:8px">
    <input type="text" id="musicQuery" placeholder='e.g. "play my liked songs on Apple Music"'
           style="flex:1" onkeydown="if(event.key==='Enter')playMusic()">
    <button class="btn-success" onclick="playMusic()">Play</button>
  </div>
  <p style="color:var(--muted);font-size:.8em;margin-top:8px">
    <b>Voice Command</b> mode sends exactly what you type as if you spoke it to Alexa.<br>
    Other modes search that specific music service for your query.
  </p>
</div>

<div class="footer">Alexa Music Controller &bull; Home Assistant Add-on</div>

<script>
/* ── helpers ──────────────────────────────────────────────── */
function apiUrl(path) {
  let base = document.baseURI || window.location.href;
  if (!base.endsWith('/')) base += '/';
  return new URL(path, base).href;
}
function showMsg(text, ok) {
  const d = document.getElementById('msgArea');
  d.innerHTML = '<div class="msg '+(ok?'msg-ok':'msg-err')+'">'+text+'</div>';
  setTimeout(() => d.innerHTML = '', 6000);
}

let allDevices = [];
let selectedEntity = null;

/* ── devices ──────────────────────────────────────────────── */
async function refreshDevices() {
  try {
    const r = await fetch(apiUrl('api/devices'), {credentials:'same-origin'});
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const d = await r.json();
    allDevices = d.devices || [];

    // Update HA badge
    const badge = document.getElementById('haBadge');
    if (d.ha_connected) {
      badge.textContent = d.device_count + ' device(s)';
      badge.className = 'status-badge status-ok';
    } else {
      badge.textContent = 'HA unavailable';
      badge.className = 'status-badge status-warn';
    }
    renderDevices();
  } catch(e) {
    console.error('refreshDevices:', e);
    document.getElementById('haBadge').textContent = 'Error';
    document.getElementById('haBadge').className = 'status-badge status-warn';
  }
}

function renderDevices() {
  const echoOnly = document.getElementById('echoOnly').checked;
  const list = echoOnly ? allDevices.filter(d => d.is_echo) : allDevices;
  const grid = document.getElementById('deviceGrid');

  if (list.length === 0) {
    grid.innerHTML = '<p style="color:var(--muted)">' +
      (allDevices.length === 0
        ? 'No media_player entities found. Make sure Alexa Media Player (HACS) is installed.'
        : 'No Echo devices found. Uncheck "Echo only" to see all media players.') +
      '</p>';
    return;
  }

  grid.innerHTML = list.map(d => {
    const sel = d.entity_id === selectedEntity ? ' selected' : '';
    const np = d.media_title
      ? '<div class="now-playing">&#9835; ' + (d.media_artist ? d.media_artist+' — ' : '') + d.media_title + '</div>'
      : '';
    const stateClass = d.state === 'playing' ? 'status-playing'
                     : d.state === 'paused'  ? 'status-paused'
                     : 'status-idle';
    return '<div class="device-card'+sel+'" onclick="selectDevice(\''+d.entity_id+'\')">' +
      '<div class="name">' + d.friendly_name + '</div>' +
      '<div class="meta"><span class="status-badge '+stateClass+'">' + d.state + '</span></div>' +
      np +
    '</div>';
  }).join('');
}

function selectDevice(entityId) {
  selectedEntity = entityId;
  const dev = allDevices.find(d => d.entity_id === entityId);
  if (!dev) return;
  document.getElementById('selectedName').textContent = dev.friendly_name;
  document.getElementById('controlCard').style.display = '';
  document.getElementById('playCard').style.display = '';
  updateNowPlaying(dev);
  if (dev.volume !== null && dev.volume !== undefined) {
    const pct = Math.round(dev.volume * 100);
    document.getElementById('volumeSlider').value = pct;
    document.getElementById('volLabel').textContent = pct + '%';
  }
  renderDevices();
}

function updateNowPlaying(dev) {
  const el = document.getElementById('nowPlaying');
  if (dev.media_title) {
    el.innerHTML = '&#9835; ' + (dev.media_artist ? dev.media_artist + ' — ' : '') + dev.media_title;
    el.style.color = 'var(--green)';
  } else {
    el.textContent = dev.state === 'playing' ? 'Playing (unknown track)' : 'Nothing playing';
    el.style.color = 'var(--muted)';
  }
}

/* ── playback commands ────────────────────────────────────── */
async function cmd(action) {
  if (!selectedEntity) { showMsg('Select a device first', false); return; }
  try {
    const r = await fetch(apiUrl('api/command'), {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({entity_id: selectedEntity, command: action}),
      credentials: 'same-origin'
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || 'HTTP ' + r.status);
    showMsg(d.message || 'OK', true);
    setTimeout(refreshDevices, 1500);
  } catch(e) {
    showMsg('Command failed: ' + e.message, false);
  }
}

async function setVolume(pct) {
  if (!selectedEntity) return;
  try {
    await fetch(apiUrl('api/command'), {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({entity_id: selectedEntity, command: 'volume', value: pct/100}),
      credentials: 'same-origin'
    });
  } catch(e) { console.error(e); }
}

async function playMusic() {
  if (!selectedEntity) { showMsg('Select a device first', false); return; }
  const query = document.getElementById('musicQuery').value.trim();
  if (!query) { showMsg('Enter something to play', false); return; }
  const service = document.getElementById('musicService').value;
  try {
    const r = await fetch(apiUrl('api/play'), {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({entity_id: selectedEntity, query: query, service: service}),
      credentials: 'same-origin'
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || 'HTTP ' + r.status);
    showMsg(d.message || 'Sent!', true);
    setTimeout(refreshDevices, 2000);
  } catch(e) {
    showMsg('Play failed: ' + e.message, false);
  }
}

/* ── init ─────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  refreshDevices();
  setInterval(refreshDevices, 15000);
});
</script>
</body>
</html>"""


# ──────────────────────────────────────────────────────────────
# Server
# ──────────────────────────────────────────────────────────────
class WebUIServer:
    """aiohttp web server with HA Ingress support."""

    def __init__(self, ha_client, device_manager):
        self.ha = ha_client
        self.dm = device_manager
        self.app = web.Application()
        self.runner = None
        self._setup_routes()

    def _setup_routes(self):
        # Normal routes
        self.app.router.add_get('/', self._index)
        self.app.router.add_get('/health', self._health)
        self.app.router.add_get('/api/devices', self._get_devices)
        self.app.router.add_post('/api/command', self._command)
        self.app.router.add_post('/api/play', self._play)
        # HA ingress sometimes sends 4 leading slashes
        self.app.router.add_get('////', self._index)
        self.app.router.add_get('////health', self._health)
        self.app.router.add_get('////api/devices', self._get_devices)
        self.app.router.add_post('////api/command', self._command)
        self.app.router.add_post('////api/play', self._play)
        # catch-all for other mangled paths
        self.app.router.add_route('*', '/{tail:.*}', self._catch_all)

    # ── lifecycle ─────────────────────────────────────────────
    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, "0.0.0.0", 8099)
        await site.start()
        logger.info("Web UI listening on 0.0.0.0:8099")

    async def stop(self):
        if self.runner:
            await self.runner.cleanup()

    # ── handlers ──────────────────────────────────────────────
    async def _index(self, request):
        return web.Response(text=HTML_PAGE, content_type='text/html')

    async def _health(self, request):
        return web.json_response({"status": "ok"})

    async def _get_devices(self, request):
        """Return all discovered media_player entities."""
        try:
            devices = self.dm.get_all()
            return web.json_response({
                "devices": devices,
                "device_count": len(devices),
                "ha_connected": len(devices) > 0 or self.ha.token != "",
            })
        except Exception as e:
            logger.error("Error getting devices: %s", e)
            return web.json_response({"devices": [], "error": str(e)}, status=500)

    async def _command(self, request):
        """Handle play/pause/stop/next/previous/volume commands."""
        try:
            data = await request.json()
            entity_id = data.get("entity_id", "")
            command = data.get("command", "")
            value = data.get("value")

            if not entity_id or not command:
                return web.json_response({"error": "entity_id and command required"}, status=400)

            ok = False
            if command == "play":
                ok = await self.ha.media_play(entity_id)
            elif command == "pause":
                ok = await self.ha.media_pause(entity_id)
            elif command == "stop":
                ok = await self.ha.media_stop(entity_id)
            elif command == "next":
                ok = await self.ha.media_next(entity_id)
            elif command == "previous":
                ok = await self.ha.media_previous(entity_id)
            elif command == "volume" and value is not None:
                ok = await self.ha.volume_set(entity_id, float(value))
            else:
                return web.json_response({"error": f"Unknown command: {command}"}, status=400)

            if ok:
                return web.json_response({"message": f"{command} sent to {entity_id}"})
            else:
                return web.json_response({"error": "HA service call failed"}, status=502)
        except Exception as e:
            logger.error("Command error: %s", e)
            return web.json_response({"error": str(e)}, status=500)

    async def _play(self, request):
        """Send a play_media command."""
        try:
            data = await request.json()
            entity_id = data.get("entity_id", "")
            query = data.get("query", "")
            service = data.get("service", "custom")

            if not entity_id or not query:
                return web.json_response({"error": "entity_id and query required"}, status=400)

            ok = await self.ha.play_media(entity_id, query, service)
            if ok:
                return web.json_response({
                    "message": f"Sent '{query}' to {entity_id} via {service}"
                })
            else:
                return web.json_response({"error": "HA service call failed"}, status=502)
        except Exception as e:
            logger.error("Play error: %s", e)
            return web.json_response({"error": str(e)}, status=500)

    async def _catch_all(self, request):
        """Normalize mangled ingress paths."""
        raw = request.path
        import re
        normalized = re.sub(r'^/{2,}', '/', raw)
        logger.debug("Catch-all: %s -> %s (%s)", raw, normalized, request.method)

        route_map = {
            ('/', 'GET'): self._index,
            ('/health', 'GET'): self._health,
            ('/api/devices', 'GET'): self._get_devices,
            ('/api/command', 'POST'): self._command,
            ('/api/play', 'POST'): self._play,
        }
        handler = route_map.get((normalized, request.method))
        if handler:
            return await handler(request)

        return web.json_response({"error": "Not found", "path": raw}, status=404)
