"""
Web UI Server
Provides configuration interface and OAuth callback
"""

import asyncio
import logging
import json
from typing import Optional
from aiohttp import web
from pathlib import Path

logger = logging.getLogger(__name__)


class WebUIServer:
    """Web UI and API server"""
    
    def __init__(self, config, amazon_client, device_manager):
        self.config = config
        self.amazon_client = amazon_client
        self.device_manager = device_manager
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
    
    async def start(self):
        """Start web UI server"""
        try:
            logger.info(f"Starting Web UI on port {self.config.web_port}")
            
            # Create aiohttp app
            self.app = web.Application()
            
            # Setup routes
            self._setup_routes()
            
            # Start server
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, "0.0.0.0", self.config.web_port)
            await self.site.start()
            
            logger.info(f"Web UI started at http://0.0.0.0:{self.config.web_port}")
            
            # Keep running
            while True:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error starting web UI: {e}", exc_info=True)
    
    async def stop(self):
        """Stop web UI server"""
        logger.info("Stopping Web UI...")
        if self.runner:
            await self.runner.cleanup()
        logger.info("Web UI stopped")
    
    def _setup_routes(self):
        """Setup web routes"""
        # Specific routes first
        self.app.router.add_get("/health", self.handle_health)
        self.app.router.add_get("/api/config", self.handle_get_config)
        self.app.router.add_post("/api/config", self.handle_set_config)
        self.app.router.add_options("/api/config", self.handle_options)
        self.app.router.add_get("/api/devices", self.handle_get_devices)
        self.app.router.add_get("/api/oauth/authorize", self.handle_oauth_authorize)
        self.app.router.add_get("/oauth/callback", self.handle_oauth_callback)
        # Generic routes last
        self.app.router.add_get("/", self.handle_index)
        # Catch-all for malformed paths from ingress (e.g., ////)
        self.app.router.add_get("/{path_info:.*}", self.handle_wildcard)
    
    async def handle_index(self, request):
        """Serve main UI page"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Alexa AirPlay Bridge</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; padding: 20px; }
                .card { background: white; border-radius: 8px; padding: 20px; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                h1 { color: #333; margin-bottom: 20px; }
                .auth-section { text-align: center; }
                .btn { padding: 10px 20px; background: #FF9900; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
                .btn:hover { background: #EC7211; }
                .device-list { list-style: none; }
                .device-item { padding: 15px; background: #f9f9f9; border-left: 4px solid #FF9900; margin: 10px 0; border-radius: 4px; }
                .status { display: inline-block; padding: 5px 10px; border-radius: 3px; font-size: 12px; }
                .status.active { background: #4CAF50; color: white; }
                .status.inactive { background: #ccc; color: #666; }
                input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; }
                label { display: block; margin-top: 15px; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎵 Alexa AirPlay Bridge</h1>
                
                <div class="card auth-section" id="authSection">
                    <h2>Setup</h2>
                    <p>Click below to authorize with your Amazon account</p>
                    <button class="btn" onclick="authorizeWithAmazon()">Authorize Amazon</button>
                </div>
                
                <div class="card">
                    <h2>Virtual AirPlay Devices</h2>
                    <ul class="device-list" id="deviceList">
                        <li class="device-item">Loading devices...</li>
                    </ul>
                </div>
                
                <div class="card">
                    <h2>Amazon Configuration</h2>
                    <p style="color: #666; font-size: 14px; margin-bottom: 15px;">
                        Enter your Amazon Login with Alexa credentials below. Get them from your <a href="https://developer.amazon.com/en-US/docs/alexa/alexa-skills-kit/register-a-product-and-create-security-profile.html" target="_blank" style="color: #FF9900;">Amazon Developer Console</a>.
                    </p>
                    
                    <label>Client ID:</label>
                    <input type="text" id="clientId" placeholder="amzn1.application-oa2-client.xxxxxxxx">
                    
                    <label>Client Secret:</label>
                    <input type="password" id="clientSecret" placeholder="Your client secret">
                    
                    <label>OAuth Redirect URI (for Amazon):</label>
                    <input type="text" id="redirectUri" readonly style="background: #f9f9f9; color: #999;">
                    <small style="color: #999; display: block; margin-top: 5px;">Copy this URI and paste it in your Amazon Developer Console under "Allowed Return URLs"</small>
                    
                    <label>AirPlay Port:</label>
                    <input type="number" id="airplayPort" placeholder="5001" min="1000" max="65535">
                    
                    <button class="btn" onclick="saveConfig()" style="margin-top: 20px; width: 100%;">💾 Save Configuration</button>
                    <div id="configMessage" style="margin-top: 10px; padding: 10px; border-radius: 4px; text-align: center; display: none;"></div>
                </div>
            </div>
            
            <script>
                function authorizeWithAmazon() {
                    fetch('/api/oauth/authorize')
                        .then(r => r.json())
                        .then(data => window.location.href = data.url)
                        .catch(e => alert('Authorization failed: ' + e));
                }
                
                function loadDevices() {
                    fetch('/api/devices')
                        .then(r => r.json())
                        .then(devices => {
                            const list = document.getElementById('deviceList');
                            if (devices.length === 0) {
                                list.innerHTML = '<li class="device-item">No devices found</li>';
                            } else {
                                list.innerHTML = devices.map(d => 
                                    `<li class="device-item">
                                        <strong>${d.name}</strong>
                                        <span class="status ${d.state === 'playing' ? 'active' : 'inactive'}">${d.state}</span>
                                        <br><small>${d.artist || 'Not playing'}</small>
                                    </li>`
                                ).join('');
                            }
                        })
                        .catch(e => console.error('Failed to load devices:', e));
                }
                
                function saveConfig() {
                    const clientId = document.getElementById('clientId').value.trim();
                    const clientSecret = document.getElementById('clientSecret').value.trim();
                    const airplayPort = document.getElementById('airplayPort').value || 5001;
                    
                    if (!clientId || !clientSecret) {
                        showMessage('Please enter both Client ID and Client Secret', 'error');
                        return;
                    }
                    
                    const config = {
                        amazon_client_id: clientId,
                        amazon_client_secret: clientSecret,
                        airplay_port: parseInt(airplayPort),
                    };
                    
                    fetch('/api/config', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(config)
                    })
                    .then(r => {
                        if (!r.ok) {
                            return r.text().then(text => {
                                throw new Error(`HTTP ${r.status}: ${text}`);
                            });
                        }
                        return r.json();
                    })
                    .then(data => {
                        if (data.status === 'success') {
                            showMessage('✓ Configuration saved! Please restart the addon for changes to take effect.', 'success');
                        } else {
                            showMessage('Error: ' + (data.message || 'Unknown error'), 'error');
                        }
                    })
                    .catch(e => showMessage('Failed to save: ' + e, 'error'));
                }
                
                function showMessage(msg, type) {
                    const msgDiv = document.getElementById('configMessage');
                    msgDiv.textContent = msg;
                    msgDiv.style.display = 'block';
                    msgDiv.style.background = type === 'success' ? '#d4edda' : '#f8d7da';
                    msgDiv.style.color = type === 'success' ? '#155724' : '#721c24';
                    msgDiv.style.border = type === 'success' ? '1px solid #c3e6cb' : '1px solid #f5c6cb';
                }
                
                function loadConfig() {
                    fetch('/api/config')
                        .then(r => r.json())
                        .then(data => {
                            document.getElementById('clientId').value = data.amazon_client_id || '';
                            document.getElementById('clientSecret').value = data.amazon_client_secret || '';
                            document.getElementById('redirectUri').value = data.amazon_redirect_uri || '';
                            document.getElementById('airplayPort').value = data.airplay_port || 5001;
                        })
                        .catch(e => console.error('Failed to load config:', e));
                }
                
                // Load config and devices on page load
                loadConfig();
                loadDevices();
                setInterval(loadDevices, 5000);
            </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type="text/html")
    
    async def handle_health(self, request):
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "authenticated": self.amazon_client.authenticated,
            "devices": len(self.device_manager.get_all_devices())
        })
    
    async def handle_options(self, request):
        """Handle OPTIONS requests for CORS preflight"""
        return web.Response(status=204, headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        })
    
    async def handle_get_config(self, request):
        """Get current configuration"""
        return web.json_response(self.config.to_dict())
    
    async def handle_set_config(self, request):
        """Save configuration"""
        try:
            data = await request.json()
            logger.info(f"Received config data: {data}")
            
            if "amazon_client_id" in data:
                self.config.amazon_client_id = data["amazon_client_id"]
            if "amazon_client_secret" in data:
                self.config.amazon_client_secret = data["amazon_client_secret"]
            if "airplay_port" in data:
                self.config.airplay_port = data["airplay_port"]
            
            self.config.save()
            logger.info("Configuration saved successfully")
            return web.json_response({"status": "success"})
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in request: {e}")
            return web.json_response({"status": "error", "message": f"Invalid JSON: {str(e)}"}, status=400)
        except Exception as e:
            logger.error(f"Error setting config: {e}", exc_info=True)
            return web.json_response({"status": "error", "message": str(e)}, status=500)
    
    async def handle_get_devices(self, request):
        """Get list of virtual devices"""
        devices = [d.to_dict() for d in self.device_manager.get_all_devices()]
        return web.json_response(devices)
    
    async def handle_oauth_authorize(self, request):
        """Get OAuth authorization URL"""
        url = self.amazon_client.get_oauth_url()
        return web.json_response({"url": url})
    
    async def handle_oauth_callback(self, request):
        """Handle OAuth callback from Amazon"""
        try:
            code = request.query.get("code")
            
            if not code:
                return web.Response(text="No authorization code received", status=400)
            
            # Exchange code for tokens
            success = await self.amazon_client.exchange_code_for_token(code)
            
            if success:
                # Trigger device refresh
                await self.device_manager.refresh_devices()
                return web.Response(text="""
                    <html>
                    <body style="font-family: sans-serif; padding: 20px; text-align: center;">
                        <h2>✓ Authorization Successful!</h2>
                        <p>You can close this window and return to the configuration page.</p>
                        <script>window.close();</script>
                    </body>
                    </html>
                """, content_type="text/html")
            else:
                return web.Response(text="Authorization failed", status=400)
        except Exception as e:
            logger.error(f"Error in OAuth callback: {e}")
            return web.Response(text=f"Error: {e}", status=500)
    
    async def handle_wildcard(self, request):
        """Handle any unmatched routes - redirect to home if just slashes"""
        path = request.path
        # If path is all slashes, redirect to home page
        if all(c == '/' for c in path):
            return web.Response(text=self._get_index_html(), content_type="text/html")
        # Otherwise return 404
        return web.Response(text="Not found", status=404)
    
    def _get_index_html(self):
        """Get the index HTML to avoid duplication"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Alexa AirPlay Bridge</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; padding: 20px; }
                .card { background: white; border-radius: 8px; padding: 20px; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                h1 { color: #333; margin-bottom: 20px; }
                .auth-section { text-align: center; }
                .btn { padding: 10px 20px; background: #FF9900; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
                .btn:hover { background: #EC7211; }
                .device-list { list-style: none; }
                .device-item { padding: 15px; background: #f9f9f9; border-left: 4px solid #FF9900; margin: 10px 0; border-radius: 4px; }
                .status { display: inline-block; padding: 5px 10px; border-radius: 3px; font-size: 12px; }
                .status.active { background: #4CAF50; color: white; }
                .status.inactive { background: #ccc; color: #666; }
                input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; }
                label { display: block; margin-top: 15px; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎵 Alexa AirPlay Bridge</h1>
                
                <div class="card auth-section" id="authSection">
                    <h2>Setup</h2>
                    <p>Click below to authorize with your Amazon account</p>
                    <button class="btn" onclick="authorizeWithAmazon()">Authorize Amazon</button>
                </div>
                
                <div class="card">
                    <h2>Virtual AirPlay Devices</h2>
                    <ul class="device-list" id="deviceList">
                        <li class="device-item">Loading devices...</li>
                    </ul>
                </div>
                
                <div class="card">
                    <h2>Amazon Configuration</h2>
                    <p style="color: #666; font-size: 14px; margin-bottom: 15px;">
                        Enter your Amazon Login with Alexa credentials below. Get them from your <a href="https://developer.amazon.com/en-US/docs/alexa/alexa-skills-kit/register-a-product-and-create-security-profile.html" target="_blank" style="color: #FF9900;">Amazon Developer Console</a>.
                    </p>
                    
                    <label>Client ID:</label>
                    <input type="text" id="clientId" placeholder="amzn1.application-oa2-client.xxxxxxxx">
                    
                    <label>Client Secret:</label>
                    <input type="password" id="clientSecret" placeholder="Your client secret">
                    
                    <label>OAuth Redirect URI (for Amazon):</label>
                    <input type="text" id="redirectUri" readonly style="background: #f9f9f9; color: #999;">
                    <small style="color: #999; display: block; margin-top: 5px;">Copy this URI and paste it in your Amazon Developer Console under "Allowed Return URLs"</small>
                    
                    <label>AirPlay Port:</label>
                    <input type="number" id="airplayPort" placeholder="5001" min="1000" max="65535">
                    
                    <button class="btn" onclick="saveConfig()" style="margin-top: 20px; width: 100%;">💾 Save Configuration</button>
                    <div id="configMessage" style="margin-top: 10px; padding: 10px; border-radius: 4px; text-align: center; display: none;"></div>
                </div>
            </div>
            
            <script>
                function authorizeWithAmazon() {
                    fetch('/api/oauth/authorize')
                        .then(r => r.json())
                        .then(data => window.location.href = data.url)
                        .catch(e => alert('Authorization failed: ' + e));
                }
                
                function loadDevices() {
                    fetch('/api/devices')
                        .then(r => r.json())
                        .then(devices => {
                            const list = document.getElementById('deviceList');
                            if (devices.length === 0) {
                                list.innerHTML = '<li class="device-item">No devices found</li>';
                            } else {
                                list.innerHTML = devices.map(d => 
                                    `<li class="device-item">
                                        <strong>${d.name}</strong>
                                        <span class="status ${d.state === 'playing' ? 'active' : 'inactive'}">${d.state}</span>
                                        <br><small>${d.artist || 'Not playing'}</small>
                                    </li>`
                                ).join('');
                            }
                        })
                        .catch(e => console.error('Failed to load devices:', e));
                }
                
                function saveConfig() {
                    const clientId = document.getElementById('clientId').value.trim();
                    const clientSecret = document.getElementById('clientSecret').value.trim();
                    const airplayPort = document.getElementById('airplayPort').value || 5001;
                    
                    if (!clientId || !clientSecret) {
                        showMessage('Please enter both Client ID and Client Secret', 'error');
                        return;
                    }
                    
                    const config = {
                        amazon_client_id: clientId,
                        amazon_client_secret: clientSecret,
                        airplay_port: parseInt(airplayPort),
                    };
                    
                    fetch('/api/config', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(config)
                    })
                    .then(r => {
                        if (!r.ok) {
                            return r.text().then(text => {
                                throw new Error(`HTTP ${r.status}: ${text}`);
                            });
                        }
                        return r.json();
                    })
                    .then(data => {
                        if (data.status === 'success') {
                            showMessage('✓ Configuration saved! Please restart the addon for changes to take effect.', 'success');
                        } else {
                            showMessage('Error: ' + (data.message || 'Unknown error'), 'error');
                        }
                    })
                    .catch(e => showMessage('Failed to save: ' + e, 'error'));
                }
                
                function showMessage(msg, type) {
                    const msgDiv = document.getElementById('configMessage');
                    msgDiv.textContent = msg;
                    msgDiv.style.display = 'block';
                    msgDiv.style.background = type === 'success' ? '#d4edda' : '#f8d7da';
                    msgDiv.style.color = type === 'success' ? '#155724' : '#721c24';
                    msgDiv.style.border = type === 'success' ? '1px solid #c3e6cb' : '1px solid #f5c6cb';
                }
                
                function loadConfig() {
                    fetch('/api/config')
                        .then(r => r.json())
                        .then(data => {
                            document.getElementById('clientId').value = data.amazon_client_id || '';
                            document.getElementById('clientSecret').value = data.amazon_client_secret || '';
                            document.getElementById('redirectUri').value = data.amazon_redirect_uri || '';
                            document.getElementById('airplayPort').value = data.airplay_port || 5001;
                        })
                        .catch(e => console.error('Failed to load config:', e));
                }
                
                // Load config and devices on page load
                loadConfig();
                loadDevices();
                setInterval(loadDevices, 5000);
            </script>
        </body>
        </html>
        """
