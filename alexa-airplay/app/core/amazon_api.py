"""
Amazon Alexa API Client
Handles OAuth, device discovery, and playback control
"""

import asyncio
import json
import logging
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import aiohttp
from aiohttp import web

logger = logging.getLogger(__name__)

# Amazon OAuth endpoints
AMAZON_AUTH_URL = "https://www.amazon.com/ap/oa"
AMAZON_TOKEN_URL = "https://api.amazon.com/auth/o2/token"
AMAZON_API_BASE = "https://api.amazonalexa.com"

# Device discovery endpoints to try (in priority order)
DEVICE_ENDPOINTS = [
    {"url": "https://api.amazonalexa.com/v2/endpoints", "type": "endpoints_v2"},
    {"url": "https://api.amazonalexa.com/v1/endpoints", "type": "endpoints_v1"},
    {"url": "https://alexa.amazon.com/api/devices-v2/device?cached=true", "type": "alexa_web_cached"},
    {"url": "https://alexa.amazon.com/api/devices-v2/device", "type": "alexa_web"},
    {"url": "https://api.amazonalexa.com/v1/devices", "type": "devices_v1"},
]

# Additional probe URLs for debugging (used by probe_all_endpoints)
PROBE_URLS = [
    # Alexa API endpoints
    "https://api.amazonalexa.com/v2/endpoints",
    "https://api.amazonalexa.com/v1/endpoints",
    "https://api.amazonalexa.com/v2/devices",
    "https://api.amazonalexa.com/v1/devices",
    "https://api.amazonalexa.com/v1/alerts",
    "https://api.amazonalexa.com/v1/skills",
    # Amazon user profile (LWA)
    "https://api.amazon.com/user/profile",
    # Alexa web app endpoints (used by alexa.amazon.com)
    "https://alexa.amazon.com/api/devices-v2/device?cached=true",
    "https://alexa.amazon.com/api/devices-v2/device",
    "https://alexa.amazon.com/api/bootstrap",
    # Alexa settings
    "https://api.amazonalexa.com/v1/devices/G0911W079081206F/settings",
    # Household
    "https://alexa.amazon.com/api/household",
]


class AmazonAPIClient:
    """Client for Amazon Alexa API"""

    def __init__(self, config):
        self.config = config
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.authenticated = False
        self.session: Optional[aiohttp.ClientSession] = None

        # Restore persisted tokens if available
        self._restore_tokens()

    def _restore_tokens(self):
        """Restore tokens saved from a previous session."""
        tokens = self.config.load_tokens()
        if tokens and tokens.get("refresh_token"):
            self.access_token = tokens.get("access_token")
            self.refresh_token = tokens.get("refresh_token")
            expiry_ts = tokens.get("expiry_ts", 0)
            self.token_expiry = datetime.fromtimestamp(expiry_ts) if expiry_ts else None
            self.authenticated = True
            logger.info("Restored OAuth tokens from disk – authenticated")

    def _persist_tokens(self):
        """Save current tokens to disk."""
        if self.access_token and self.refresh_token:
            expiry_ts = self.token_expiry.timestamp() if self.token_expiry else 0
            self.config.save_tokens(self.access_token, self.refresh_token, expiry_ts)

    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
            logger.info("Initialized HTTP session for Amazon API")

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Closed HTTP session")

    def get_oauth_url(self) -> str:
        import urllib.parse
        params = {
            "client_id": self.config.amazon_client_id,
            "scope": "alexa:all profile",
            "scope_data": json.dumps({
                "alexa:all": {"productID": "AlexaAirPlayBridge", "productInstanceAttributes": {"deviceSerialNumber": "001"}},
            }),
            "response_type": "code",
            "redirect_uri": self.config.amazon_redirect_uri,
        }
        query_string = urllib.parse.urlencode(params)
        return f"{AMAZON_AUTH_URL}?{query_string}"

    async def exchange_code_for_token(self, code: str) -> bool:
        try:
            await self.init_session()
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.config.amazon_client_id,
                "client_secret": self.config.amazon_client_secret,
                "redirect_uri": self.config.amazon_redirect_uri,
            }
            async with self.session.post(AMAZON_TOKEN_URL, data=data) as resp:
                if resp.status == 200:
                    token_data = await resp.json()
                    self.access_token = token_data.get("access_token")
                    self.refresh_token = token_data.get("refresh_token")
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                    self.authenticated = True
                    self._persist_tokens()
                    logger.info("Successfully authenticated with Amazon")
                    return True
                else:
                    error_text = await resp.text()
                    logger.error(f"Failed to exchange code: {resp.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"Error exchanging code: {e}")
            return False

    async def refresh_access_token(self) -> bool:
        if not self.refresh_token:
            return False
        try:
            await self.init_session()
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.config.amazon_client_id,
                "client_secret": self.config.amazon_client_secret,
            }
            async with self.session.post(AMAZON_TOKEN_URL, data=data) as resp:
                if resp.status == 200:
                    token_data = await resp.json()
                    self.access_token = token_data.get("access_token")
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                    self._persist_tokens()
                    logger.info("Token refreshed successfully")
                    return True
                else:
                    logger.error(f"Failed to refresh token: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return False

    async def _ensure_valid_token(self):
        if not self.access_token:
            raise Exception("Not authenticated")
        if self.token_expiry and datetime.now() >= self.token_expiry:
            await self.refresh_access_token()

    async def get_devices(self) -> List[Dict]:
        """Get Echo devices, trying multiple Alexa API endpoints as fallback."""
        try:
            await self._ensure_valid_token()
            await self.init_session()
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json",
            }

            for ep in DEVICE_ENDPOINTS:
                url = ep["url"]
                ep_type = ep["type"]
                try:
                    logger.info(f"Trying device endpoint: {url}")
                    async with self.session.get(url, headers=headers) as resp:
                        body = await resp.text()
                        logger.info(f"  -> HTTP {resp.status} ({len(body)} bytes)")

                        if resp.status == 200:
                            try:
                                data = json.loads(body)
                            except json.JSONDecodeError:
                                logger.warning(f"  Non-JSON from {ep_type}")
                                continue

                            devices = self._normalize_devices(data, ep_type)
                            if devices:
                                logger.info(f"  Found {len(devices)} device(s) via {ep_type}")
                                return devices
                            logger.info(f"  200 OK but 0 usable devices from {ep_type}")
                            if isinstance(data, dict):
                                logger.debug(f"  Response keys: {list(data.keys())}")
                        elif resp.status == 401:
                            logger.warning("  401 – refreshing token")
                            if await self.refresh_access_token():
                                headers["Authorization"] = f"Bearer {self.access_token}"
                        elif resp.status == 403:
                            logger.warning(f"  403 on {ep_type} – scope may not cover this")
                        else:
                            logger.warning(f"  HTTP {resp.status} on {ep_type}: {body[:300]}")
                except Exception as exc:
                    logger.error(f"  Exception on {ep_type}: {exc}")

            logger.error("Failed to get devices from all endpoints")
            return []
        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            return []

    @staticmethod
    def _normalize_devices(data, source_type: str) -> List[Dict]:
        """Normalise various Alexa API response shapes into [{id, name, type}]."""
        items: list = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            for key in ("endpoints", "devices", "device", "items", "results"):
                val = data.get(key)
                if isinstance(val, list) and val:
                    items = val
                    break
            if not items:
                if "id" in data or "endpointId" in data or "serialNumber" in data:
                    items = [data]

        devices: List[Dict] = []
        for raw in items:
            if not isinstance(raw, dict):
                continue
            device_id = (
                raw.get("endpointId")
                or raw.get("id")
                or raw.get("deviceSerialNumber")
                or raw.get("serialNumber")
                or raw.get("accountName")
            )
            if not device_id:
                continue
            name = (
                raw.get("friendlyName")
                or raw.get("name")
                or raw.get("accountName")
                or raw.get("displayName")
                or raw.get("deviceFamily")
                or f"Echo {device_id}"
            )
            device_type = (
                raw.get("deviceType")
                or raw.get("type")
                or raw.get("deviceFamily")
                or "ECHO"
            )
            devices.append({
                "id": str(device_id),
                "name": str(name),
                "type": str(device_type),
                "source": source_type,
            })
        return devices

    async def send_command(self, device_id: str, command: str, params: Dict = None) -> bool:
        try:
            await self._ensure_valid_token()
            await self.init_session()
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "directive": {
                    "header": {
                        "namespace": "Alexa.MediaPlayer",
                        "name": command,
                        "messageId": str(datetime.now().timestamp()),
                    },
                    "endpoint": {"endpointId": device_id},
                    "payload": params or {},
                }
            }
            async with self.session.post(
                f"{AMAZON_API_BASE}/v1/directives",
                headers=headers,
                json=payload,
            ) as resp:
                if resp.status == 202:
                    logger.debug(f"Command {command} sent to {device_id}")
                    return True
                else:
                    logger.error(f"Failed to send command: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False

    async def probe_all_endpoints(self) -> List[Dict]:
        """Probe many Alexa API URLs and return status/body for each (debug tool)."""
        await self._ensure_valid_token()
        await self.init_session()
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        results = []
        for url in PROBE_URLS:
            try:
                async with self.session.get(url, headers=headers) as resp:
                    body = await resp.text()
                    results.append({
                        "url": url,
                        "status": resp.status,
                        "body_preview": body[:500],
                    })
            except Exception as e:
                results.append({"url": url, "status": -1, "error": str(e)})
        return results
