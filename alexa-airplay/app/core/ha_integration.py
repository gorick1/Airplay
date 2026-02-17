"""
Home Assistant Integration
Handles communication with Home Assistant Supervisor API
to discover media_player entities and send playback commands.
"""

import logging
import os
from typing import Dict, List, Optional
import aiohttp

logger = logging.getLogger(__name__)

HA_URL = os.getenv("HA_URL", "http://supervisor")


class HAClient:
    """Client for the Home Assistant Supervisor REST API."""

    def __init__(self):
        self.token: str = os.getenv("SUPERVISOR_TOKEN", "")
        self.base_url: str = f"{HA_URL}/core/api"
        self._session: Optional[aiohttp.ClientSession] = None

    # ── session management ────────────────────────────────────
    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    # ── generic helpers ───────────────────────────────────────
    async def _get(self, path: str):
        session = await self._ensure_session()
        url = f"{self.base_url}{path}"
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error("GET %s -> %s", path, resp.status)
                return None
        except Exception as e:
            logger.error("GET %s error: %s", path, e)
            return None

    async def _post(self, path: str, data: dict = None) -> bool:
        session = await self._ensure_session()
        url = f"{self.base_url}{path}"
        try:
            async with session.post(url, json=data or {}) as resp:
                if resp.status == 200:
                    return True
                body = await resp.text()
                logger.error("POST %s -> %s: %s", path, resp.status, body[:200])
                return False
        except Exception as e:
            logger.error("POST %s error: %s", path, e)
            return False

    # ── discovery ─────────────────────────────────────────────
    async def get_all_media_players(self) -> List[Dict]:
        """Return every media_player entity in HA with state + attributes."""
        states = await self._get("/states")
        if not states or not isinstance(states, list):
            return []
        return [
            s for s in states
            if s.get("entity_id", "").startswith("media_player.")
        ]

    async def get_entity_state(self, entity_id: str) -> Optional[Dict]:
        """Get the current state of a single entity."""
        return await self._get(f"/states/{entity_id}")

    # ── media player service calls ────────────────────────────
    async def call_service(self, domain: str, service: str,
                           entity_id: str, data: dict = None) -> bool:
        """Call a HA service targeting a specific entity."""
        payload = {"entity_id": entity_id}
        if data:
            payload.update(data)
        return await self._post(f"/services/{domain}/{service}", payload)

    async def play_media(self, entity_id: str,
                         content_id: str,
                         content_type: str = "custom") -> bool:
        """Call media_player.play_media on a device.

        content_type can be:
          "custom"       - send content_id as a voice command
          "APPLE_MUSIC"  - search Apple Music
          "AMAZON_MUSIC" - search Amazon Music
          "SPOTIFY"      - search Spotify
          "TUNEIN"       - search TuneIn
          "music"        - generic
        """
        return await self.call_service(
            "media_player", "play_media", entity_id,
            {"media_content_id": content_id, "media_content_type": content_type},
        )

    async def media_play(self, entity_id: str) -> bool:
        return await self.call_service("media_player", "media_play", entity_id)

    async def media_pause(self, entity_id: str) -> bool:
        return await self.call_service("media_player", "media_pause", entity_id)

    async def media_stop(self, entity_id: str) -> bool:
        return await self.call_service("media_player", "media_stop", entity_id)

    async def media_next(self, entity_id: str) -> bool:
        return await self.call_service("media_player", "media_next_track", entity_id)

    async def media_previous(self, entity_id: str) -> bool:
        return await self.call_service("media_player", "media_previous_track", entity_id)

    async def volume_set(self, entity_id: str, level: float) -> bool:
        """Set volume (0.0 - 1.0)."""
        return await self.call_service(
            "media_player", "volume_set", entity_id,
            {"volume_level": max(0.0, min(1.0, level))},
        )
