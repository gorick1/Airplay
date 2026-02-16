"""
Web UI Server for Alexa AirPlay Bridge
Provides configuration UI and API endpoints.
Fully compatible with Home Assistant Ingress proxy.
"""

import json
import logging
from aiohttp import web

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# HTML Template
# Uses ONLY relative URLs so that it works identically whether
# the page is opened directly (http://container:8099/) or
# through the HA ingress proxy (/api/hassio_ingress/<token>/).
# ──────────────────────────────────────────────────────────────
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Alexa AirPlay Bridge</title>
<style>
:root{--bg:#1a1a2e;--card:#16213e;--accent:#0f3460;--blue:#53a8e2;--green:#4ecca3;
       --red:#e74c3c;--text:#eee;--muted:#999;--border:#2a3a5a}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,
     "Segoe UI",Roboto,sans-serif;padding:20px;max-width:900px;margin:0 auto}
h1{text-align:center;margin:20px 0;color:var(--blue)}
h2{color:var(--blue);margin-bottom:15px;font-size:1.2em}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;
      padding:24px;margin-bottom:20px}
.status-badge{display:inline-block;padding:4px 12px;border-radius:12px;font-size:0.85em;
              font-weight:600}
.status-ok{background:rgba(78,204,163,.15);color:var(--green)}
.status-warn{background:rgba(231,76,60,.15);color:var(--red)}
label{display:block;margin:10px 0 4px;font-weight:600;color:var(--muted);font-size:.9em}
input[type=text],input[type=password]{width:100%;padding:10px 12px;border:1px solid var(--border);
      border-radius:8px;background:var(--bg);color:var(--text);font-size:.95em}
input:focus{outline:none;border-color:var(--blue)}
button{padding:10px 20px;border:none;border-radius:8px;cursor:pointer;font-size:.95em;
       font-weight:600;transition:.2s}
.btn-primary{background:var(--blue);color:#fff}
.btn-primary:hover{background:#4298d2}
.btn-success{background:var(--green);color:#111}
.btn-success:hover{background:#3dbb92}
.btn-danger{background:var(--red);color:#fff}
.btn-danger:hover{background:#d63031}
.btn-row{display:flex;gap:10px;margin-top:15px}
.msg{padding:10px 14px;border-radius:8px;margin:10px 0;font-size:.9em}
.msg-ok{background:rgba(78,204,163,.12);color:var(--green);border:1px solid rgba(78,204,163,.25)}
.msg-err{background:rgba(231,76,60,.12);color:var(--red);border:1px solid rgba(231,76,60,.25)}
.device-list{list-style:none}
.device-list li{padding:10px 14px;border-bottom:1px solid var(--border);display:flex;
                justify-content:space-between;align-items:center}
.device-list li:last-child{border-bottom:none}
.device-name{font-weight:600}.device-state{font-size:.85em;color:var(--muted)}
#msg{display:none}
.footer{text-align:center;padding:20px;color:var(--muted);font-size:.8em}
</style>
</head>
<body>

<h1>&#127911; Alexa AirPlay Bridge</h1>

<!-- Status Card -->
<div class="card">
  <h2>Status</h2>
  <p>Bridge: <span class="status-badge status-ok">Running</span>
     &nbsp; Amazon Auth: <span id="authBadge" class="status-badge status-warn">Not Connected</span></p>
</div>

<!-- Credentials Card -->
<div class="card">
  <h2>Amazon Developer Credentials</h2>
  <div id="msg" class="msg"></div>
  <label for="client_id">Client ID</label>
  <input type="text" id="client_id" placeholder="amzn1.application-oa2-client.…"/>
  <label for="client_secret">Client Secret</label>
  <input type="password" id="client_secret" placeholder="Enter your client secret"/>
  <div class="btn-row">
    <button class="btn-primary" onclick="saveConfig()">Save Credentials</button>
    <button class="btn-success" id="authBtn" onclick="startOAuth()" disabled>Authorize with Amazon</button>
  </div>
</div>

<!-- Devices Card -->
<div class="card">
  <h2>Devices</h2>
  <ul id="deviceList" class="device-list">
    <li><span class="device-state">Authorize with Amazon to discover devices.</span></li>
  </ul>
  <div class="btn-row">
    <button class="btn-primary" onclick="loadDevices()">Refresh Devices</button>
  </div>
</div>

<div class="footer">Alexa AirPlay Bridge &bull; Home Assistant Add-on</div>

<script>
/* ────────── helpers ────────── */
// Resolve relative to current page URL so ingress prefix is kept automatically.
function apiUrl(path) {
  // Ensure we have a proper base with trailing slash
  let base = window.location.href;
  if (!base.endsWith('/')) base += '/';
  // path should NOT start with /
  if (path.startsWith('/')) path = path.substring(1);
  return new URL(path, base).href;
}

function showMsg(text, ok) {
  const el = document.getElementById('msg');
  el.textContent = text;
  el.className = ok ? 'msg msg-ok' : 'msg msg-err';
  el.style.display = 'block';
  if (ok) setTimeout(() => el.style.display = 'none', 5000);
}

/* ────────── Load config ────────── */
async function loadConfig() {
  try {
    const r = await fetch(apiUrl('api/config'), {credentials:'same-origin'});
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const d = await r.json();
    document.getElementById('client_id').value     = d.amazon_client_id || '';
    document.getElementById('client_secret').value = d.amazon_client_secret || '';

    const hasAuth = d.authenticated === true;
    const badge = document.getElementById('authBadge');
    badge.textContent = hasAuth ? 'Connected' : 'Not Connected';
    badge.className   = 'status-badge ' + (hasAuth ? 'status-ok' : 'status-warn');

    const hasCreds = !!(d.amazon_client_id && d.amazon_client_secret);
    document.getElementById('authBtn').disabled = !hasCreds;
  } catch(e) {
    console.error('loadConfig:', e);
  }
}

/* ────────── Save config ────────── */
async function saveConfig() {
  try {
    const body = JSON.stringify({
      amazon_client_id:     document.getElementById('client_id').value.trim(),
      amazon_client_secret: document.getElementById('client_secret').value.trim()
    });
    const r = await fetch(apiUrl('api/config'), {
      method:  'POST',
      headers: {'Content-Type':'application/json'},
      body:    body,
      credentials: 'same-origin'
    });
    if (!r.ok) {
      const txt = await r.text();
      throw new Error('HTTP ' + r.status + ': ' + txt);
    }
    const d = await r.json();
    showMsg(d.message || 'Saved', true);
    loadConfig();
  } catch(e) {
    showMsg('Failed to save: ' + e.message, false);
  }
}

/* ────────── OAuth ────────── */
function startOAuth() {
  // Navigate in the same window; the server builds the full Amazon URL
  window.location.href = apiUrl('api/oauth/authorize');
}

/* ────────── Devices ────────── */
async function loadDevices() {
  try {
    const r = await fetch(apiUrl('api/devices'), {credentials:'same-origin'});
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const d = await r.json();
    const ul = document.getElementById('deviceList');
    if (!d.devices || d.devices.length === 0) {
      ul.innerHTML = '<li><span class="device-state">No devices found.</span></li>';
      return;
    }
    ul.innerHTML = d.devices.map(dev =>
      '<li><span class="device-name">' + (dev.name||dev.id) + '</span>' +
      '<span class="device-state">' + (dev.state||'unknown') + '</span></li>'
    ).join('');
  } catch(e) {
    console.error('loadDevices:', e);
  }
}

/* ────────── Init ────────── */
document.addEventListener('DOMContentLoaded', loadConfig);
</script>
</body>
</html>"""


class WebUIServer:
    """aiohttp-based web server with full HA Ingress support."""

    def __init__(self, config, amazon_client, device_manager):
        self.config = config
        self.amazon_client = amazon_client
        self.device_manager = device_manager
        self.app = web.Application()
        self.runner = None
        self._setup_routes()

    # ── routes ────────────────────────────────────────────────
    def _setup_routes(self):
        self.app.router.add_get('/', self._handle_index)
        self.app.router.add_get('/health', self._handle_health)
        self.app.router.add_get('/api/config', self._handle_get_config)
        self.app.router.add_post('/api/config', self._handle_save_config)
        self.app.router.add_get('/api/devices', self._handle_get_devices)
        self.app.router.add_get('/api/oauth/authorize', self._handle_oauth_start)
        self.app.router.add_get('/oauth/callback', self._handle_oauth_callback)
        # In some HA ingress paths, upstream sends 4 leading slashes.
        # Register explicit aliases so these routes still resolve.
        self.app.router.add_get('////', self._handle_index)
        self.app.router.add_get('////health', self._handle_health)
        self.app.router.add_get('////api/config', self._handle_get_config)
        self.app.router.add_post('////api/config', self._handle_save_config)
        self.app.router.add_get('////api/devices', self._handle_get_devices)
        self.app.router.add_get('////api/oauth/authorize', self._handle_oauth_start)
        self.app.router.add_get('////oauth/callback', self._handle_oauth_callback)
        # Home Assistant ingress can occasionally forward paths like "////".
        # Catch anything unmatched and normalize repeated leading slashes.
        self.app.router.add_route('*', '/{tail:.*}', self._handle_catch_all)

    async def _handle_catch_all(self, request: web.Request) -> web.StreamResponse:
        """Normalize malformed ingress paths and dispatch to the intended handler.

        Example malformed paths observed in production:
        - ////
        - ////api/config
        """
        raw_path = request.path or '/'
        normalized = '/' + '/'.join(part for part in raw_path.split('/') if part)
        if normalized == '//':
            normalized = '/'

        logger.warning(f"Unmatched route path={raw_path!r}, normalized={normalized!r}, method={request.method}")

        if normalized == '/' and request.method == 'GET':
            return await self._handle_index(request)
        if normalized == '/health' and request.method == 'GET':
            return await self._handle_health(request)
        if normalized == '/api/config' and request.method == 'GET':
            return await self._handle_get_config(request)
        if normalized == '/api/config' and request.method == 'POST':
            return await self._handle_save_config(request)
        if normalized == '/api/devices' and request.method == 'GET':
            return await self._handle_get_devices(request)
        if normalized == '/api/oauth/authorize' and request.method == 'GET':
            return await self._handle_oauth_start(request)
        if normalized == '/oauth/callback' and request.method == 'GET':
            return await self._handle_oauth_callback(request)

        return web.json_response(
            {
                "error": "Not Found",
                "path": raw_path,
                "normalized_path": normalized,
                "method": request.method,
            },
            status=404,
        )

    # ── index ─────────────────────────────────────────────────
    async def _handle_index(self, request: web.Request) -> web.Response:
        logger.info("Serving index page")
        return web.Response(text=HTML_PAGE, content_type='text/html')

    # ── health ────────────────────────────────────────────────
    async def _handle_health(self, request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    # ── GET /api/config ───────────────────────────────────────
    async def _handle_get_config(self, request: web.Request) -> web.Response:
        data = self.config.to_dict()
        data['authenticated'] = getattr(self.amazon_client, 'authenticated', False)
        return web.json_response(data)

    # ── POST /api/config ──────────────────────────────────────
    async def _handle_save_config(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        updated = False
        if 'amazon_client_id' in body and body['amazon_client_id']:
            self.config.amazon_client_id = body['amazon_client_id'].strip()
            updated = True
        if 'amazon_client_secret' in body and body['amazon_client_secret']:
            self.config.amazon_client_secret = body['amazon_client_secret'].strip()
            updated = True

        if updated:
            self.config.save()
            logger.info("Configuration saved via web UI")
            return web.json_response({"message": "Configuration saved successfully"})
        else:
            return web.json_response({"error": "No valid fields provided"}, status=400)

    # ── GET /api/devices ──────────────────────────────────────
    async def _handle_get_devices(self, request: web.Request) -> web.Response:
        try:
            devices = self.device_manager.get_all_devices()
            return web.json_response({
                "devices": [d.to_dict() for d in devices]
            })
        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            return web.json_response({"devices": [], "error": str(e)})

    # ── OAuth start ───────────────────────────────────────────
    async def _handle_oauth_start(self, request: web.Request) -> web.Response:
        """Build the Amazon OAuth URL.

        The redirect_uri is constructed dynamically from the ingress path
        so the OAuth callback lands back on the correct ingress URL.
        """
        ingress_path = request.headers.get('X-Ingress-Path', '')

        if ingress_path:
            # Build an absolute redirect URI that goes through the HA ingress
            # The HA frontend is typically on the same host the user is visiting
            host = request.headers.get('X-Forwarded-Host',
                   request.headers.get('Host', 'localhost'))
            scheme = request.headers.get('X-Forwarded-Proto', 'http')
            redirect_uri = f"{scheme}://{host}{ingress_path}/oauth/callback"
        elif self.config.amazon_redirect_uri:
            redirect_uri = self.config.amazon_redirect_uri
        else:
            redirect_uri = "http://localhost:8099/oauth/callback"

        # Temporarily update config so the token exchange uses the same URI
        self.config.amazon_redirect_uri = redirect_uri
        self.config.save()

        oauth_url = self.amazon_client.get_oauth_url()
        logger.info(f"OAuth redirect → {oauth_url}")
        raise web.HTTPFound(location=oauth_url)

    # ── OAuth callback ────────────────────────────────────────
    async def _handle_oauth_callback(self, request: web.Request) -> web.Response:
        code = request.query.get('code')
        if not code:
            return web.Response(text="Missing authorization code", status=400)

        success = await self.amazon_client.exchange_code_for_token(code)

        if success:
            html = """<!DOCTYPE html><html><head><meta charset="utf-8">
            <title>Authorization Successful</title>
            <style>body{background:#1a1a2e;color:#eee;font-family:sans-serif;
            display:flex;justify-content:center;align-items:center;height:100vh}
            .box{text-align:center;padding:40px;background:#16213e;border-radius:16px}
            h1{color:#4ecca3}a{color:#53a8e2}</style></head>
            <body><div class="box"><h1>&#10004; Authorization Successful</h1>
            <p>Your Amazon account has been connected.</p>
            <p><a href="./">Return to Dashboard</a></p></div></body></html>"""
        else:
            html = """<!DOCTYPE html><html><head><meta charset="utf-8">
            <title>Authorization Failed</title>
            <style>body{background:#1a1a2e;color:#eee;font-family:sans-serif;
            display:flex;justify-content:center;align-items:center;height:100vh}
            .box{text-align:center;padding:40px;background:#16213e;border-radius:16px}
            h1{color:#e74c3c}a{color:#53a8e2}</style></head>
            <body><div class="box"><h1>&#10008; Authorization Failed</h1>
            <p>Could not connect to Amazon.  Check your credentials and try again.</p>
            <p><a href="./">Return to Dashboard</a></p></div></body></html>"""

        return web.Response(text=html, content_type='text/html')

    # ── server lifecycle ──────────────────────────────────────
    async def start(self):
        port = int(getattr(self.config, 'web_port', 8099))
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, '0.0.0.0', port)
        await site.start()
        logger.info(f"Web UI listening on 0.0.0.0:{port}")

    async def stop(self):
        if self.runner:
            await self.runner.cleanup()
            logger.info("Web UI stopped")
