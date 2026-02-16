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


class AmazonAPIClient:
    """Client for Amazon Alexa API"""
    
    def __init__(self, config):
        self.config = config
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.authenticated = False
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def init_session(self):
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            logger.info("Initialized HTTP session for Amazon API")
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Closed HTTP session")
    
    def get_oauth_url(self) -> str:
        """Generate OAuth authorization URL"""
        params = {
            "client_id": self.config.amazon_client_id,
            "scope": "alexa:all",
            "response_type": "code",
            "redirect_uri": self.config.amazon_redirect_uri,
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{AMAZON_AUTH_URL}?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> bool:
        """Exchange authorization code for tokens"""
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
                    logger.info("Successfully authenticated with Amazon")
                    return True
                else:
                    logger.error(f"Failed to exchange code: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"Error exchanging code: {e}")
            return False
    
    async def refresh_access_token(self) -> bool:
        """Refresh access token using refresh token"""
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
                    logger.info("Token refreshed successfully")
                    return True
                else:
                    logger.error(f"Failed to refresh token: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return False
    
    async def _ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if not self.access_token:
            raise Exception("Not authenticated")
        
        if self.token_expiry and datetime.now() >= self.token_expiry:
            await self.refresh_access_token()

    @staticmethod
    def _normalize_devices(payload: Dict) -> List[Dict]:
        """Normalize multiple Alexa payload shapes into id/name/type entries."""
        candidates = []
        if isinstance(payload, dict):
            for key in ("devices", "device", "endpoints"):
                value = payload.get(key)
                if isinstance(value, list):
                    candidates = value
                    break

        normalized: List[Dict] = []
        for raw in candidates:
            if not isinstance(raw, dict):
                continue

            device_id = (
                raw.get("id")
                or raw.get("serialNumber")
                or raw.get("deviceSerialNumber")
                or raw.get("endpointId")
                or raw.get("accountName")
            )
            if not device_id:
                continue

            name = (
                raw.get("name")
                or raw.get("accountName")
                or raw.get("deviceFamily")
                or raw.get("friendlyName")
                or f"Echo {device_id}"
            )

            device_type = (
                raw.get("type")
                or raw.get("deviceType")
                or raw.get("deviceFamily")
                or "device"
            )

            normalized.append(
                {
                    "id": str(device_id),
                    "name": str(name),
                    "type": str(device_type),
                }
            )

        return normalized
    
    async def get_devices(self) -> List[Dict]:
        """Get list of Echo devices"""
        try:
            await self._ensure_valid_token()
            await self.init_session()
            
            headers = {"Authorization": f"Bearer {self.access_token}"}

            endpoints = [
                f"{AMAZON_API_BASE}/v1/devices",
                f"{AMAZON_API_BASE}/v2/devices",
                f"{AMAZON_API_BASE}/v1/endpoints",
                f"{AMAZON_API_BASE}/api/devices-v2/device?cached=true&_={int(time.time() * 1000)}",
            ]

            for url in endpoints:
                try:
                    async with self.session.get(url, headers=headers) as resp:
                        text = await resp.text()

                        if resp.status != 200:
                            logger.warning(f"Device endpoint failed ({resp.status}): {url}")
                            continue

                        try:
                            data = json.loads(text)
                        except Exception:
                            logger.warning(f"Device endpoint returned non-JSON payload: {url}")
                            continue

                        devices = self._normalize_devices(data)
                        if devices:
                            logger.info(f"Retrieved {len(devices)} devices from Amazon ({url})")
                            return devices

                        logger.warning(f"No devices in payload from endpoint: {url}")
                except Exception as endpoint_error:
                    logger.warning(f"Device endpoint error for {url}: {endpoint_error}")

            logger.error("Failed to get devices from all known endpoints")
            return []
        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            return []
    
    async def send_command(self, device_id: str, command: str, params: Dict = None) -> bool:
        """Send command to a device"""
        try:
            await self._ensure_valid_token()
            await self.init_session()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "directive": {
                    "header": {
                        "namespace": "Alexa.MediaPlayer",
                        "name": command,
                        "messageId": str(datetime.now().timestamp())
                    },
                    "endpoint": {
                        "endpointId": device_id
                    },
                    "payload": params or {}
                }
            }
            
            async with self.session.post(
                f"{AMAZON_API_BASE}/v1/directives",
                headers=headers,
                json=payload
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
